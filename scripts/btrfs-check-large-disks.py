import json
from enum import StrEnum
from os import getenv, unlink
from subprocess import PIPE, STDOUT, CalledProcessError, run
from tempfile import TemporaryDirectory
from typing import TypedDict


class CheckMountError(Exception):
    pass


class CheckCreateError(Exception):
    pass


class CheckWriteError(Exception):
    pass


class CheckReadError(Exception):
    pass


class CheckRemoveError(Exception):
    pass


class CheckUmountError(Exception):
    pass


class CheckType(StrEnum):
    BTRFS_CHECK_RO = "BTRFS_CHECK_RO"
    BTRFS_CHECK = "BTRFS_CHECK"
    WRITE = "WRITE"


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


def btrfs_check_device(device: Device, force: bool = False) -> bool:
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
        return True
    else:
        print(f"→ {name} ERROR, errors found")
        print(process.stdout)
        return False


def unmount_and_btrfs_check_device(device: Device) -> bool:
    try:
        unmount_device(device)
    except Exception as e:
        print(f"Failed to unmount {device['name']}")
        return False
    return btrfs_check_device(device)


def btrfs_check_read_only_device(device: Device) -> bool:
    return btrfs_check_device(device, force=True)


def check_write_device(device: Device) -> bool:

    # Create a temporary directory
    with TemporaryDirectory() as mountpoint:
        mount_command = ("mount", f"/dev/{device['name']}", mountpoint)
        test_file = f"{mountpoint}/geoffrey-check-file.txt"
        written_text = "test"
        umount_command = ("umount", mountpoint)
        try:
            # Mount the device
            try:
                run(args=mount_command, check=True)
            except CalledProcessError as e:
                raise CheckMountError() from e
            # Create a test file
            try:
                open(test_file, "x").close()
            except FileExistsError:
                print(f"WARNING: Test file already exists")
            except IOError as e:
                raise CheckCreateError() from e
            # Write to the test file
            try:
                with open(test_file, "w") as file:
                    file.write(written_text)
            except OSError as e:
                raise CheckWriteError() from e
            # Read the test file
            try:
                with open(test_file, "r") as file:
                    if not file.read() == written_text:
                        raise CheckReadError()
            except OSError as e:
                raise CheckReadError() from e
            # Remove the test file
            try:
                unlink(test_file)
            except OSError as e:
                raise CheckRemoveError() from e
            # Unmount the device
            try:
                run(args=umount_command, check=True)
            except CalledProcessError as e:
                raise CheckUmountError() from e
        except Exception as e:
            print(f"Failed to write to {device['name']}")
            print(e)
            return False

    print(f"→ {device['name']} OK")
    return True


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

    # Get the allowed file system types
    allowed_fstypes = getenv("FSTYPES", "btrfs").split(",")

    # Get the type of check to perform
    try:
        check_type = CheckType(getenv("CHECK", CheckType.BTRFS_CHECK_RO))
    except ValueError:
        print(f"Invalid check type: {check_type}")
        print(f"Valid check types: {', '.join(CheckType)}")
        exit(1)

    print("Force mode is enabled, not unmounting devices.")

    # Check all btrfs devices of at least min_size
    for device in get_block_devices():
        # Filter drives
        is_wrong_type = device["fstype"] not in allowed_fstypes
        is_too_small = int(device["size"]) < min_size
        is_name_skipped = device["name"] in skipped_device_names
        if is_wrong_type or is_too_small or is_name_skipped:
            print(f"Skipping {device['name']}")
            continue
        # Run the check
        check_function_map = {
            CheckType.BTRFS_CHECK_RO: btrfs_check_read_only_device,
            CheckType.BTRFS_CHECK: unmount_and_btrfs_check_device,
            CheckType.WRITE: check_write_device,
        }
        check = check_function_map[check_type]
        if not check(device):
            print(f"Check failed for {device['name']}, exiting")
            exit(1)


if __name__ == "__main__":
    main()
