"""Standard library modules for Forthic."""

from .array_module import ArrayModule
from .boolean_module import BooleanModule
from .core_module import CoreModule
from .datetime_module import DateTimeModule
from .json_module import JSONModule
from .math_module import MathModule
from .record_module import RecordModule
from .string_module import StringModule

__all__ = [
    "CoreModule",
    "MathModule",
    "BooleanModule",
    "StringModule",
    "ArrayModule",
    "RecordModule",
    "JSONModule",
    "DateTimeModule",
]
