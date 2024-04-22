from subprocess import PIPE, STDOUT, run

from blkdiag.checks.check import Check, CheckFailure, CheckResult, CheckSuccess
from blkdiag.lsblk import Device
from blkdiag.umount import unmount_device


class BtrfsCheck(Check):

    def _btrfs_check_device(self, device: Device, force: bool = False) -> CheckResult:
        name = device["name"]
        serial = device["serial"]
        print(f"Checking {name} ({serial})")

        # Build the args
        args_base = ["btrfs", "check"]
        args_force = ["--force"] if force else []
        args_device = [f"/dev/{name}"]
        args = args_base + args_force + args_device

        # Run the command
        try:
            process = run(args=args, stderr=STDOUT, stdout=PIPE, text=True, check=True)
        except Exception as e:
            return CheckFailure(e, f"Failed to run btrfs check on {name}")

        # Output
        if "no error found" in process.stdout:
            return CheckSuccess()
        else:
            message = f"Errors found on {name}\n{process.stdout}"
            return CheckFailure(None, message)


class BtrfsUnmountCheck(BtrfsCheck):

    @classmethod
    def get_check_type(cls) -> str:
        return "BTRFS"

    def __unmount_device(self, device: Device) -> CheckResult:
        try:
            unmount_device(device)
        except Exception as e:
            return CheckFailure(e, f"Failed to unmount {device['name']}")
        return CheckSuccess()

    def run(self, device: Device) -> CheckResult:
        if not (unmount_result := self.__unmount_device(device)):
            return unmount_result
        return self._btrfs_check_device(device)


class BtrfsReadOnlyForceCheck(BtrfsCheck):

    @classmethod
    def get_check_type(cls) -> str:
        return "BTRFS_RO"

    def run(self, device: Device) -> CheckResult:
        return self._btrfs_check_device(device, force=True)
