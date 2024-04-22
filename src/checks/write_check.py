from os import unlink
from pathlib import Path
from traceback import print_exception

from src.checks.check import Check
from src.errors import (
    CheckCreateError,
    CheckError,
    CheckNoMountPointError,
    CheckReadError,
    CheckRemoveError,
    CheckWriteError,
)
from src.lsblk import Device


class WritableCheck(Check):

    def __get_mount_point(self, device: Device) -> Path:
        try:
            return Path(device["mountpoints"][0])
        except IndexError:
            raise CheckNoMountPointError("No mount point") from None

    def __create_file(self, path: Path) -> None:
        try:
            open(path, "x").close()
        except FileExistsError:
            print(f"WARNING: Test file already exists")
        except IOError as e:
            raise CheckCreateError() from e

    def __write_to_file(self, path: Path, text: str) -> None:
        try:
            with open(path, "w") as file:
                file.write(text)
        except OSError as e:
            raise CheckWriteError() from e

    def __read_from_file(self, path: Path, expected_text: str) -> None:
        try:
            with open(path, "r") as file:
                if not file.read() == expected_text:
                    raise CheckReadError()
        except OSError as e:
            raise CheckReadError() from e

    def __remove_file(self, path: Path) -> None:
        try:
            unlink(path)
        except OSError as e:
            raise CheckRemoveError() from e

    def run(self, device: Device) -> bool:
        try:
            mount_point = self.__get_mount_point(device)
            test_file_path = mount_point / "geoffrey-check-file.txt"
            written_text = "test"
            self.__create_file(test_file_path)
            self.__write_to_file(test_file_path, written_text)
            self.__read_from_file(test_file_path, written_text)
            self.__remove_file(test_file_path)
        except CheckError as e:
            print(f"Failed to write to {device['name']}")
            print_exception(e)
            return False
        return True
