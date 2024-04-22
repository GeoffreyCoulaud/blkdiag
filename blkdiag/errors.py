class CheckError(Exception):
    """Generic error raised when a check failed"""


class CheckCreateError(CheckError):
    """Error raised when a check fails to create a file"""


class CheckWriteError(CheckError):
    """Error raised when a check fails to write to a file"""


class CheckReadError(CheckError):
    """Error raised when a check fails to read from a file"""


class CheckRemoveError(CheckError):
    """Error raised when a check fails to remove a file"""


class CheckNoMountPointError(CheckError):
    """Error raised when a check fails to find a mount point"""
