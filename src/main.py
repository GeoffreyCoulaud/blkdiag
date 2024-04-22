from argparse import ArgumentParser, Namespace
from os import getenv

from checks.btrfs import BtrfsReadOnlyForceCheck, BtrfsUnmountCheck
from checks.check import AbstractCheck, CheckFailure, CheckResult, CheckSuccess
from checks.writable import WritableCheck
from lsblk import Device, get_block_devices

KILOBYTE = 1024
MEGABYTE = KILOBYTE**2
GIGABYTE = KILOBYTE**3
TERABYTE = KILOBYTE**4


def bytes_from_human(human: str) -> int:
    suffix = human[-1].upper()
    suffixes = {"K": KILOBYTE, "M": MEGABYTE, "G": GIGABYTE, "T": TERABYTE}
    multiplier = suffixes[suffix]
    return int(human[:-1]) * multiplier


def device_to_human(device: Device) -> str:
    return f"{device['name']} ({device['serial']})"


checks: dict[str, AbstractCheck] = {
    klass.get_check_type(): klass
    for klass in (
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
    check: AbstractCheck


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
        action="store_true",
        help="Exit immediately on first failure",
    )
    parser.add_argument(
        "check",
        default=BtrfsReadOnlyForceCheck.get_check_type(),
        choices=checks.keys(),
        type=lambda check_type: checks[check_type],
        help="Type of check to perform",
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


def main():

    args: Args = parse_arguments()
    print(f"Running check: {args.check.get_check_type()}")

    # Filter devices
    devices = get_block_devices()

    # Run the checks
    results: dict[Device, CheckResult] = {}
    for device in devices:
        device_human_name = device_to_human(device)

        # Skip devices that don't meet the criteria
        if not is_device_checkable(
            device, args.fstypes, args.min_size, args.skip_devices
        ):
            print(f"Skipping {device_human_name}")
            continue

        # Run the check
        print(f"Checking {device_human_name}")
        result = args.check().run(device)

        # Store the result
        match result:
            case CheckSuccess():
                print("Check passed")
            case CheckFailure():
                print("Check failed")
                if args.exit_on_fail:
                    break
                result[device] = result

    # Early exit if all checks passed
    if all(result):
        print("All checks passed")
        exit(0)

    # Report failed devices
    print("Some checks failed:")
    for device, result in results.items():
        device_human_name = device_to_human(device)
        print(f"{device_human_name}: {str(result)}")
    exit(1)


if __name__ == "__main__":
    main()
