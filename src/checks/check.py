from abc import ABC, abstractmethod

from lsblk import Device


class CheckResult(ABC):
    """Result of a check"""

    @abstractmethod
    def __bool__(self) -> bool:
        pass


class CheckFailure(CheckResult):
    """Result of a check that failed"""

    _exception: Exception
    _message: str

    def __init__(self, exception: Exception, message: str):
        self._exception = exception
        self._message = message

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return f"FAILURE: {self._message}"


class CheckSuccess(CheckResult):
    """Result of a check that passed"""

    def __bool__(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"SUCCESS"


class Check(ABC):
    """Abstract class for a check"""

    @classmethod
    @abstractmethod
    def get_check_type(cls) -> str:
        """Return the check type, as a string"""

    @abstractmethod
    def run(self, device: Device) -> CheckResult:
        """Run the check on the device"""
