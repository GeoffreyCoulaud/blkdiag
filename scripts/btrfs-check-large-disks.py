import json
from os import getenv
from subprocess import run
from typing import TypedDict


class Device(TypedDict):
    name: str
    size: str
    fstype: str
    mountpoints: list[str]


class LsblkOutput(TypedDict):
    blockdevices: list[Device]


def unmount_device(device: Device):
    for mountpoint in device["mountpoints"]:
        print(f"--- Unmounting {mountpoint}")
        run(args=("umount", mountpoint), check=True)


def check_device(device: Device):
    name = device["name"]
    print(f"--- Checking {name}")
    run(args=("btrfs", "check", f"/dev/{name}"), check=True)


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
                "NAME,SIZE,FSTYPE,MOUNTPOINTS",
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
    # Get the filter min size
    min_size_human_default = "1T"
    min_size_human = getenv("MIN_SIZE", min_size_human_default)
    if min_size_human.endswith("B"):
        min_size_human = min_size_human[:-1]
    min_size = bytes_from_human(min_size_human)

    # Check all btrfs devices of at least min_size
    for device in get_block_devices():
        is_wrong_type = device["fstype"] != "btrfs"
        is_too_small = int(device["size"]) < min_size
        if is_wrong_type or is_too_small:
            continue
        unmount_and_check_device(device)


if __name__ == "__main__":
    main()
