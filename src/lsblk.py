import json
from subprocess import run
from typing import TypedDict


class Device(TypedDict):
    name: str
    size: str
    fstype: str
    serial: str
    mountpoints: list[str]


class LsblkOutput(TypedDict):
    blockdevices: list[Device]


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
