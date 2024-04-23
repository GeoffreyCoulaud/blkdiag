# blkdiag
Tools to perform diagnostics on storage devices

## What does `blkdiag` do ?

This tool allows an administrator (assumed to have root privileges) to perform various sanity checks on block devices. By default, `blkdiag` will run checks on block devices formatted as `btrfs` that are bigger than 1 TiB.  
This is configurable with the CLI.

Here is a list of available checks
| Check | Description |
| ----- | ----------- |
| WRITABLE | Check that the disk is writable.<br/>Will create a file, write to it, read the content and verify it then delete the file. |
| BTRFS_RO | Runs `btrfs check --force` on the disk.<br/>Only use if you know that the disks are not being written to. |
| BTRFS | Unmounts the disk and runs `btrfs check` on it.<br/>Be careful, it doesn't remount the disk after checking. |

## Usage

Refer to the integrated help for usage.  
`blkdiag --help`

<!--HELP_START-->
```
usage: Check block devices [-h] [--skip-devices SKIP_DEVICES] [--min-size MIN_SIZE] [--fstypes FSTYPES] [--exit-on-fail] {BTRFS_RO,BTRFS,WRITABLE} [{BTRFS_RO,BTRFS,WRITABLE} ...]

positional arguments:
  {BTRFS_RO,BTRFS,WRITABLE}
                        Name of the checks to perform

options:
  -h, --help            show this help message and exit
  --skip-devices SKIP_DEVICES
                        Comma separated list of device names to skip
  --min-size MIN_SIZE   Filter devices smaller than this size
  --fstypes FSTYPES     Comma separated list of allowed file system types
  --exit-on-fail        Exit immediately on first failure
```
<!--HELP_END-->

Example usage

```
blkdiag --skip-devices 'sda,sdb' --min-size '2T' WRITABLE BTRFS
```


## Local development setup

```sh
git clone https://github.com/GeoffreyCoulaud/blkdiag.git
cd blkdiag
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
blkdiag
```