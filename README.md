# blkdiag
Tools to perform diagnostics on storage devices

## Usage

Refer to the integrated help for usage.  
`blkdiag --help`

```
usage: Check block devices [-h] [--skip-devices SKIP_DEVICES] [--min-size MIN_SIZE] [--fstypes FSTYPES] [--exit-on-fail] {BTRFS_RO,BTRFS,WRITABLE}

positional arguments:
  {BTRFS_RO,BTRFS,WRITABLE}
                        Type of check to perform

options:
  -h, --help            show this help message and exit
  --skip-devices SKIP_DEVICES
                        Comma separated list of device names to skip
  --min-size MIN_SIZE   Filter devices smaller than this size
  --fstypes FSTYPES     Comma separated list of allowed file system types
  --exit-on-fail        Exit immediately on first failure
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