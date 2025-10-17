"""Forthic modules package."""

from .standard import (
    ArrayModule,
    BooleanModule,
    CoreModule,
    DateTimeModule,
    JSONModule,
    MathModule,
    RecordModule,
    StringModule,
)

__all__ = [
    # Standard library modules
    "CoreModule",
    "MathModule",
    "BooleanModule",
    "StringModule",
    "ArrayModule",
    "RecordModule",
    "JSONModule",
    "DateTimeModule",
]

# Optional: PandasModule (requires pandas to be installed)
try:
    from .pandas_module import PandasModule

    __all__.append("PandasModule")
except ImportError:
    pass
