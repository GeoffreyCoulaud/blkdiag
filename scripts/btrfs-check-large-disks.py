import json
from os import getenv
from subprocess import PIPE, STDOUT, run
from typing import TypedDict


class Device(TypedDict):
    name: str
    size: str
    fstype: str
    serial: str
    mountpoints: list[str]


class LsblkOutput(TypedDict):
    blockdevices: list[Device]


def unmount_device(device: Device):
    for mountpoint in device["mountpoints"]:
        if mountpoint is None:
            continue
        print(f"Unmounting {mountpoint}")
        run(args=("umount", mountpoint), check=True)


def check_device(device: Device, force: bool = False):
    name = device["name"]
    serial = device["serial"]
    print(f"Checking {name} ({serial})")

    # Build the args
    args_base = ["btrfs", "check"]
    args_force = ["--force"] if force else []
    args_device = [f"/dev/{name}"]
    args = args_base + args_force + args_device

    # Run the command
    process = run(
        args=args,
        stderr=STDOUT,
        stdout=PIPE,
        text=True,
    )

    # Output
    if "no error found" in process.stdout:
        print(f"→ {name} OK, no errors found")
    else:
        print(f"→ {name} ERROR, errors found")
        print(process.stdout)
        exit(1)


def check_read_only_device(device: Device):
    check_device(device, force=True)


def unmount_and_check_device(device: Device):
    unmount_device(device)
    check_device(device)


def get_block_devices() -> list[Device]:
    lsblk_output: LsblkOutput = json.loads(
        run(
            args=(
                "lsblk",
                "--bytes",
                "--json",
                "--output",
                "NAME,SIZE,FSTYPE,SERIAL,MOUNTPOINTS",
            ),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    return lsblk_output["blockdevices"]


KILOBYTE = 1024
MEGABYTE = KILOBYTE**2
GIGABYTE = KILOBYTE**3
TERABYTE = KILOBYTE**4


def bytes_from_human(human: str) -> int:
    suffix = human[-1].upper()
    suffixes = {"K": KILOBYTE, "M": MEGABYTE, "G": GIGABYTE, "T": TERABYTE}
    multiplier = suffixes[suffix]
    return int(human[:-1]) * multiplier


def main():
    # Get the skipped device names
    skipped_device_names = getenv("SKIP_DEVICES", "").split(",")

    # Get the filter min size
    min_size_human_default = "1T"
    min_size_human = getenv("MIN_SIZE", min_size_human_default)
    if min_size_human.endswith("B"):
        min_size_human = min_size_human[:-1]
    min_size = bytes_from_human(min_size_human)

    # Get the force flag
    force = getenv("FORCE", "false").lower() in ("true", "1", "y")
    if force:
        print("Force mode is enabled, not unmounting devices.")

    # Check all btrfs devices of at least min_size
    for device in get_block_devices():
        is_wrong_type = device["fstype"] != "btrfs"
        is_too_small = int(device["size"]) < min_size
        is_skipped = device["name"] in skipped_device_names
        if is_wrong_type or is_too_small or is_skipped:
            print(f"Skipping {device['name']}")
            continue
        if force:
            check_read_only_device(device)
        else:
            unmount_and_check_device(device)


if __name__ == "__main__":
    main()
