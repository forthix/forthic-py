"""Math module - Mathematical operations.

Provides arithmetic, comparison, and mathematical utility functions.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...utils import is_truthy
from .array_module import MAX_MATERIALIZED_ELEMENTS


class MathModule(DecoratedModule):
    """Mathematical operations and utilities including arithmetic, aggregation, and conversions."""

    def __init__(self) -> None:
        super().__init__("math")
        register_module_doc(
            MathModule,
            """
Mathematical operations and utilities including arithmetic, aggregation, and conversions.

## Categories
- Arithmetic: +, -, *, /, ADD, SUBTRACT, MULTIPLY, DIVIDE, MOD
- Aggregates: MEAN, MAX, MIN, SUM
- Type conversion: >INT, >FLOAT, >FIXED, ROUND
- Constants (py extensions): PI, E
- Math functions: ABS, SQRT, FLOOR, CEIL, CLAMP

## Examples
5 3 +
[1 2 3 4] SUM
[10 20 30] MEAN
3.7 ROUND
            """,
        )

    # ==================
    # Arithmetic Operations
    # ==================

    @WordDecorator("( a:number b:number -- sum:number )", "Add two numbers. For arrays use SUM.", "+")
    async def plus(self, a: Any, b: Any) -> Any:
        if isinstance(a, list) or isinstance(b, list):
            raise ValueError("+ takes two numbers. For an array of numbers, use SUM.")
        num_a = 0 if a is None else a
        num_b = 0 if b is None else b
        return num_a + num_b

    @WordDecorator("( a:number b:number -- difference:number )", "Subtract b from a", "-")
    async def minus(self, a: float | int | None, b: float | int | None) -> float | int | None:
        if a is None or b is None:
            return None
        return a - b

    @WordDecorator("( a:number b:number -- product:number )", "Multiply two numbers. For arrays use PRODUCT.", "*")
    async def times(self, a: Any, b: Any) -> Any:
        if isinstance(a, list) or isinstance(b, list):
            raise ValueError("* takes two numbers. For an array of numbers, use PRODUCT.")
        if a is None or b is None:
            return None
        return a * b

    @WordDecorator("( a:number b:number -- quotient:number )", "Divide a by b", "/")
    async def divide_by(self, a: float | int | None, b: float | int | None) -> float | None:
        if a is None or b is None:
            return None
        if b == 0:
            return None
        return a / b

    @WordDecorator("( m:number n:number -- remainder:number )", "Modulo operation (m % n, JS semantics: result takes the sign of m)")
    async def MOD(self, m: float | int | None, n: float | int | None) -> float | int | None:
        if m is None or n is None:
            return None
        # JS % is truncated modulo (sign of the dividend); Python's % is
        # floored (sign of the divisor) — convert
        result = m % n
        if result != 0 and (result < 0) != (m < 0):
            result -= n
        return result

    # ==================
    # Aggregates
    # ==================

    @WordDecorator("( items:any[] -- mean:any )", "Calculate mean of array (handles numbers, strings, objects)")
    async def MEAN(self, items: Any) -> Any:
        # Falsy input (JS truthiness) or an empty array is 0; a truthy
        # non-array passes through as-is (including empty records, which
        # are truthy under the contract)
        if not is_truthy(items) or (isinstance(items, list) and len(items) == 0):
            return 0

        if not isinstance(items, list):
            return items

        if len(items) == 1:
            return items[0]

        # Filter out null/None values
        filtered = [x for x in items if x is not None]

        if len(filtered) == 0:
            return 0

        # Check type of first non-null item
        first = filtered[0]

        # Case 1: Numbers
        if isinstance(first, (int, float)):
            total = sum(filtered)
            return total / len(filtered)

        # Case 2: Strings - return frequency distribution
        if isinstance(first, str):
            counts: dict[str, int] = {}
            for item in filtered:
                counts[item] = counts.get(item, 0) + 1
            result: dict[str, float] = {}
            for key in counts:
                result[key] = counts[key] / len(filtered)
            return result

        # Case 3: Objects - field-wise mean
        if isinstance(first, dict):
            result_dict: dict[str, Any] = {}
            all_keys: dict[str, bool] = {}

            # Collect all keys in first-seen (insertion) order
            for obj in filtered:
                for key in obj.keys():
                    all_keys[key] = True

            # Compute mean for each key
            for key in all_keys:
                values = [obj.get(key) for obj in filtered if obj.get(key) is not None]

                if len(values) == 0:
                    continue

                first_val = values[0]

                if isinstance(first_val, (int, float)):
                    total = sum(values)
                    result_dict[key] = total / len(values)
                elif isinstance(first_val, str):
                    counts_inner: dict[str, int] = {}
                    for val in values:
                        counts_inner[val] = counts_inner.get(val, 0) + 1
                    freqs: dict[str, float] = {}
                    for k in counts_inner:
                        freqs[k] = counts_inner[k] / len(values)
                    result_dict[key] = freqs

            return result_dict

        return 0

    @WordDecorator(
        "( start:number end:number -- numbers:number[] )",
        "Generate inclusive integer range from start to end (e.g. 1 5 RANGE -> [1,2,3,4,5]). Empty if start > end.",
    )
    async def RANGE(self, start: Any, end: Any) -> list:
        if start is None or end is None:
            return []
        start = int(start)
        end = int(end)
        # Guard against a pathological size before allocating. end < start
        # yields an empty range and needs no bound.
        if end >= start and end - start + 1 > MAX_MATERIALIZED_ELEMENTS:
            raise ValueError(
                f"RANGE size {end - start + 1} is too large (limit {MAX_MATERIALIZED_ELEMENTS})"
            )
        return list(range(start, end + 1))

    @WordDecorator(
        "( numbers:number[] -- max:number )",
        "Maximum of an array of numbers. Null elements are skipped. Returns null for empty/all-null array.",
        "MAX",
    )
    async def MAX(self, numbers: Any) -> Any:
        if not isinstance(numbers, list):
            raise ValueError("MAX requires an array of numbers. For two numbers use > with IF.")
        result = None
        for num in numbers:
            if num is None:
                continue
            if result is None or num > result:
                result = num
        return result

    @WordDecorator(
        "( numbers:number[] -- min:number )",
        "Minimum of an array of numbers. Null elements are skipped. Returns null for empty/all-null array.",
        "MIN",
    )
    async def MIN(self, numbers: Any) -> Any:
        if not isinstance(numbers, list):
            raise ValueError("MIN requires an array of numbers. For two numbers use < with IF.")
        result = None
        for num in numbers:
            if num is None:
                continue
            if result is None or num < result:
                result = num
        return result

    @WordDecorator(
        "( numbers:number[] -- product:number )",
        "Product of array of numbers (1 if empty). Null elements yield null.",
        "PRODUCT",
    )
    async def PRODUCT(self, numbers: Any) -> Any:
        if not isinstance(numbers, list):
            return None
        result: Any = 1
        for num in numbers:
            # Null or non-numeric elements null the whole result (deliberate
            # asymmetry with SUM's null-skipping; and no JS string coercion
            # or Python string repetition)
            if num is None or isinstance(num, bool) or not isinstance(num, (int, float)):
                return None
            result *= num
        return result

    @WordDecorator("( numbers:number[] -- sum:number )", "Sum of array (explicit)")
    async def SUM(self, numbers: list | None) -> float | int:
        if not numbers or not isinstance(numbers, list):
            return 0

        result = 0
        for num in numbers:
            if num is not None:
                result += num
        return result

    # ==================
    # Type Conversion
    # ==================

    @WordDecorator("( a:any -- int:number )", "Convert to integer (returns length for arrays/objects, 0 for null)", ">INT")
    async def to_INT(self, a: Any) -> int:
        if a is None:
            return 0

        if isinstance(a, list):
            return len(a)
        if isinstance(a, dict):
            return len(a.keys())

        try:
            return int(math.trunc(float(a)))
        except (ValueError, TypeError):
            return 0

    @WordDecorator("( a:any -- float:number )", "Convert to float", ">FLOAT")
    async def to_FLOAT(self, a: Any) -> float:
        if a is None:
            return 0.0

        try:
            return float(a)
        except (ValueError, TypeError):
            return 0.0

    @WordDecorator(
        "( num:number digits:number -- result:string )",
        "Format number with fixed decimal places (JS toFixed: ties round half away from zero; digits must be 0..100)",
        "FORMAT-FIXED",
    )
    async def FORMAT_FIXED(self, num: Any, digits: Any) -> str | None:
        if num is None:
            return None
        if isinstance(num, bool) or not isinstance(num, (int, float)):
            raise ValueError(f"FORMAT-FIXED requires a number, got {num!r}")
        d = 0 if digits is None else int(digits)
        if d < 0 or d > 100:
            raise ValueError(f"FORMAT-FIXED digits must be between 0 and 100, got {digits!r}")
        # JS toFixed rounds the BINARY double half away from zero: Decimal
        # of the float is its exact binary value, so 1.005 (really
        # 1.00499...) gives "1.00" while an exact 0.5 gives "1". Python's
        # f-string would use ties-to-even ("0").
        from decimal import ROUND_HALF_UP, Decimal

        quantum = Decimal(1).scaleb(-d)
        return str(Decimal(num).quantize(quantum, rounding=ROUND_HALF_UP))

    @WordDecorator("( num:number -- int:number )", "Round to nearest integer (JS Math.round: halves round toward +Infinity)")
    async def ROUND(self, num: float | int | None) -> int | None:
        if num is None:
            return None
        # JS Math.round: floor(x + 0.5) — 0.5 -> 1, 2.5 -> 3, -2.5 -> -2.
        # Python's round() is banker's rounding (2.5 -> 2)
        return math.floor(num + 0.5)

    # ==================
    # Special Values
    # ==================

    # ==================
    # Math Functions
    # ==================

    @WordDecorator("( n:number -- abs:number )", "Absolute value")
    async def ABS(self, n: float | int | None) -> float | int | None:
        if n is None:
            return None
        return abs(n)

    @WordDecorator("( n:number -- sqrt:number )", "Square root")
    async def SQRT(self, n: float | int | None) -> float | None:
        if n is None:
            return None
        # Negative input is NaN (JS Math.sqrt), not an error
        if n < 0:
            return math.nan
        return math.sqrt(n)

    @WordDecorator("( n:number -- floor:number )", "Round down to integer")
    async def FLOOR(self, n: float | int | None) -> int | None:
        if n is None:
            return None
        return math.floor(n)

    @WordDecorator("( n:number -- ceil:number )", "Round up to integer")
    async def CEIL(self, n: float | int | None) -> int | None:
        if n is None:
            return None
        return math.ceil(n)

    @ForthicDirectWord("( value:number min:number max:number -- clamped:number )", "Constrain value to range [min, max]", "CLAMP")
    async def CLAMP(
            self, interp: Interpreter
    ) -> None:
        max_val = interp.stack_pop()
        min_val = interp.stack_pop()
        value = interp.stack_pop()
        if value is None or min_val is None or max_val is None:
            interp.stack_push(None)
        elif any(isinstance(v, float) and math.isnan(v) for v in (value, min_val, max_val)):
            # JS Math.min/max propagate NaN; Python's min/max are
            # order-dependent with NaN — pin the JS behavior
            interp.stack_push(math.nan)
        else:
            interp.stack_push(max(min_val, min(max_val, value)))

    # ==================
    # Constants (from original implementation)
    # ==================

    @WordDecorator("( -- pi:float )", "Push mathematical constant pi (py extension — pending upstreaming to ts/rs)")
    async def PI(self) -> float:
        return math.pi

    @WordDecorator("( -- e:float )", "Push mathematical constant e (py extension — pending upstreaming to ts/rs)")
    async def E(self) -> float:
        return math.e
