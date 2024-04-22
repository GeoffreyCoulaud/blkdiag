from subprocess import run

from lsblk import Device


def unmount_device(device: Device):
    for mountpoint in device["mountpoints"]:
        if mountpoint is None:
            continue
        print(f"Unmounting {mountpoint}")
        run(args=("umount", mountpoint), check=True)
