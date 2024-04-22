from os import getenv

from checks.btrfs import BtrfsReadOnlyForceCheck, BtrfsUnmountCheck
from checks.check import AbstractCheck, CheckResult
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


def main():
    # Get the skipped device names
    skipped_device_names = getenv("SKIP_DEVICES", "").split(",")

    # Get the filter min size
    min_size_human_default = "1T"
    min_size_human = getenv("MIN_SIZE", min_size_human_default)
    if min_size_human.endswith("B"):
        min_size_human = min_size_human[:-1]
    min_size = bytes_from_human(min_size_human)

    # Get the allowed file system types
    allowed_fstypes = getenv("FSTYPES", "btrfs").split(",")

    # Get the type of check to perform
    checks: dict[str, AbstractCheck] = {
        klass.get_check_type(): klass
        for klass in (
            BtrfsReadOnlyForceCheck,
            BtrfsUnmountCheck,
            WritableCheck,
        )
    }
    default_check_type = BtrfsReadOnlyForceCheck.get_check_type()
    env_check = getenv("CHECK", default_check_type)
    try:
        check = checks[env_check]
    except KeyError:
        print(f"Invalid check type: {env_check}")
        print(f"Valid check types: {', '.join(checks.keys())}")
        exit(1)
    print(f"Running check: {check}")

    # Get the exit_on_fail flag
    exit_on_fail = getenv("EXIT_ON_FAIL", "n").lower() in ("true", "1", "y")

    # Filter devices
    checked_devices = (
        device
        for device in get_block_devices()
        if (
            device["fstype"] in allowed_fstypes
            and int(device["size"]) >= min_size
            and device["name"] not in skipped_device_names
        )
    )

    # Run the checks
    results: dict[Device, CheckResult] = {}
    for device in checked_devices:
        print(f"Checking {device_to_human(device)}")
        result = check().run(device)
        if result:
            continue
        if exit_on_fail:
            exit(1)
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
