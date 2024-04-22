from argparse import ArgumentParser, Namespace
from typing import Callable

from blkdiag.checks.btrfs import BtrfsReadOnlyForceCheck, BtrfsUnmountCheck
from blkdiag.checks.check import Check, CheckFailure, CheckResult, CheckSuccess
from blkdiag.checks.writable import WritableCheck
from blkdiag.lsblk import Device, get_block_devices


def bytes_from_human(human: str) -> int:
    KILOBYTE = 1024
    MEGABYTE = KILOBYTE**2
    GIGABYTE = KILOBYTE**3
    TERABYTE = KILOBYTE**4
    suffixes = {"K": KILOBYTE, "M": MEGABYTE, "G": GIGABYTE, "T": TERABYTE}
    suffix = human[-1].upper()
    multiplier = suffixes[suffix]
    return int(human[:-1]) * multiplier


def device_to_human(device: Device) -> str:
    return f"{device['name']} ({device['serial']})"


check_name_map: dict[str, Check] = {
    check.get_check_name(): check
    for check in (
        BtrfsReadOnlyForceCheck,
        BtrfsUnmountCheck,
        WritableCheck,
    )
}


class Args(Namespace):
    skip_devices: list[str]
    min_size: int
    fstypes: list[str]
    exit_on_fail: bool
    check_names: list[str]


def parse_arguments() -> Args:
    """Parse command line arguments"""
    parser = ArgumentParser("Check block devices")
    parser.add_argument(
        "--skip-devices",
        default="",
        type=lambda devices: devices.split(","),
        help="Comma separated list of device names to skip",
    )
    parser.add_argument(
        "--min-size",
        default="1T",
        type=bytes_from_human,
        help="Filter devices smaller than this size",
    )
    parser.add_argument(
        "--fstypes",
        default="btrfs",
        type=lambda fstypes: fstypes.split(","),
        help="Comma separated list of allowed file system types",
    )
    parser.add_argument(
        "--exit-on-fail",
        default=False,
        action="store_true",
        help="Exit immediately on first failure",
    )
    parser.add_argument(
        "check_names",
        nargs="+",
        choices=check_name_map.keys(),
        help="Name of the checks to perform",
    )
    return parser.parse_args()


def is_device_checkable(
    device: Device,
    allowed_fstypes: list[str],
    min_size: int,
    skipped_device_names: list[str],
) -> bool:
    return (
        device["fstype"] in allowed_fstypes
        and int(device["size"]) >= min_size
        and device["name"] not in skipped_device_names
    )


def build_checks(check_names: list[str]) -> list[Check]:
    # Reorder so that the unmounting checks are run last
    check_names_set = set(check_names)
    last_checks = set((BtrfsUnmountCheck.get_check_name(),))
    # fmt: off
    check_names_ordered = (
        list(check_names_set - last_checks) 
        + list(check_names_set & last_checks)
    )
    # fmt: on
    # Build the checks from the types
    return [check_name_map[check_name]() for check_name in check_names_ordered]


def main():

    args: Args = parse_arguments()

    # Filter devices
    devices = get_block_devices()

    # Run the checks
    checks = build_checks(args.check_names)
    results: list[tuple[Device, str, CheckResult]] = []
    for device in devices:

        device_name = device_to_human(device)

        # Skip devices that don't meet the criteria
        if not is_device_checkable(
            device, args.fstypes, args.min_size, args.skip_devices
        ):
            print(f"Skipping {device_name}")
            continue

        # run selected checks on device
        for check in checks:

            # Run the check
            check_name = check.get_check_name()
            print(f"Checking {check_name} for {device_name}... ", end="", flush=True)
            result = check.run(device)

            # Store the result
            results.append((device, check_name, result))
            match result:
                case CheckSuccess():
                    print("Passed")
                case CheckFailure():
                    print("Failed")
                    if args.exit_on_fail:
                        break

    # Early exit if all checks passed
    if len(results) == 0:
        print("No check ran")
        exit(0)
    if all((result for (_, _, result) in results)):
        print(f"Ran {len(results)} checks, all passed")
        exit(0)

    # Report failed devices
    print("Some checks failed:")
    for device, check_name, result in results:
        device_name = device_to_human(device)
        print(f"{device_name} {check_name}: {str(result)}")
    exit(1)


if __name__ == "__main__":
    main()
