from __future__ import annotations
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from textual.validation import Failure, Number


class NumberRange(Number):
    """Extends the default number validator to incorporate exclusive minimum and maximum values as they appear in
    the jsonschema specification"""

    def __init__(
        self,
        minimum: float | int | None = None,
        maximum: float | int | None = None,
        exclusive_minimum: float | int | None = None,
        exclusive_maximum: float | int | None = None,
    ):
        super().__init__(minimum=minimum, maximum=maximum)
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum

    def _validate_range(self, value: float) -> bool:
        is_valid = super()._validate_range(value)
        if not is_valid:
            return is_valid
        if self.exclusive_minimum is not None and value <= self.exclusive_minimum:
            return False
        if self.exclusive_maximum is not None and value >= self.exclusive_maximum:
            return False
        return True

    def describe_failure(self, failure: Failure) -> str | None:
        if isinstance(failure, Number.NotInRange):
            if self.exclusive_minimum is not None:
                if self.exclusive_maximum is not None:
                    return (
                        f"Must be greater than {self.exclusive_minimum} and smaller"
                        f" than {self.exclusive_maximum}"
                    )
                elif self.maximum is not None:
                    return (
                        f"Must be greater than {self.exclusive_minimum} and smaller or"
                        f" equal to {self.maximum}"
                    )
                return f"Must be greater than {self.exclusive_minimum}"
            elif self.exclusive_maximum is not None:
                if self.minimum is None:
                    return f"Must be smaller than {self.exclusive_maximum}"
                return (
                    f"Must be greater or equal {self.minimum} and smaller than"
                    f" {self.exclusive_maximum}"
                )
        return super().describe_failure(failure)


def valid_date_by_format(value: str, date_fmt: str, valid_empty: bool = True) -> bool:
    if not value:
        return valid_empty
    try:
        datetime.strptime(value, date_fmt)
    except ValueError:
        return False
    return True


@lru_cache(maxsize=12)
def example_date(fmt: str) -> str:
    return datetime.today().strftime(fmt)


def valid_file_path(value: str, valid_empty: bool = True) -> bool:
    """Validates if a file exists. The function is not cached, since a file can appear on the system
    any time"""
    if not value:
        return valid_empty
    return Path(value).is_file()


def valid_folder(value: str, valid_empty: bool = True) -> bool:
    """Validates if a folder exists. The function is not cached, since a folder can appear on the system
    any time"""
    if not value:
        return valid_empty
    return Path(value).is_dir()


def is_absolute_path(value: str, valid_empty: bool = True) -> bool:
    if not value:
        return valid_empty
    p = Path(value)
    if p.expanduser().parts != p.parts:
        return True
    if p.resolve().parts != p.parts:
        return False
    return True


@lru_cache(maxsize=64)
def empty_value(value: str) -> bool:
    """A validator to add when Input.valid_empty is not True"""
    return bool(value)
