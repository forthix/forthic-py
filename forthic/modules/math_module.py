"""Math module - Mathematical operations.

Provides arithmetic, comparison, and mathematical utility functions.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..interpreter import Interpreter

from ..decorators import DecoratedModule, DirectWord, register_module_doc
from ..decorators import Word as WordDecorator


class MathModule(DecoratedModule):
    """Mathematical operations and utilities including arithmetic, aggregation, and conversions."""

    def __init__(self):
        super().__init__("math")
        register_module_doc(
            MathModule,
            """
Mathematical operations and utilities including arithmetic, aggregation, and conversions.

## Categories
- Arithmetic: +, -, *, /, ADD, SUBTRACT, MULTIPLY, DIVIDE, MOD
- Aggregates: MEAN, MAX, MIN, SUM
- Type conversion: >INT, >FLOAT, >FIXED, ROUND
- Special values: INFINITY, UNIFORM-RANDOM
- Math functions: ABS, SQRT, FLOOR, CEIL, CLAMP

## Examples
5 3 +
[1 2 3 4] SUM
[10 20 30] MEAN
3.7 ROUND
0 100 UNIFORM-RANDOM
            """,
        )

    # ==================
    # Arithmetic Operations
    # ==================

    @DirectWord(
        "( a:number b:number -- sum:number ) OR ( numbers:number[] -- sum:number )",
        "Add two numbers or sum array",
        "+",
    )
    async def plus(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            result = 0
            for num in b:
                if num is not None:
                    result += num
            interp.stack_push(result)
            return

        # Case 2: Two numbers
        a = interp.stack_pop()
        num_a = 0 if a is None else a
        num_b = 0 if b is None else b
        interp.stack_push(num_a + num_b)

    @DirectWord(
        "( a:number b:number -- sum:number ) OR ( numbers:number[] -- sum:number )", "Add two numbers or sum array", "ADD"
    )
    async def plus_ADD(self, interp: Interpreter) -> None:
        return await self.plus(interp)

    @WordDecorator("( a:number b:number -- difference:number )", "Subtract b from a", "-")
    async def minus(self, a: float | int | None, b: float | int | None) -> float | int | None:
        if a is None or b is None:
            return None
        return a - b

    @WordDecorator("( a:number b:number -- difference:number )", "Subtract b from a", "SUBTRACT")
    async def minus_SUBTRACT(self, a: float | int | None, b: float | int | None) -> float | int | None:
        if a is None or b is None:
            return None
        return a - b

    @DirectWord(
        "( a:number b:number -- product:number ) OR ( numbers:number[] -- product:number )",
        "Multiply two numbers or product of array",
        "*",
    )
    async def times(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            result = 1
            for num in b:
                if num is None:
                    interp.stack_push(None)
                    return
                result *= num
            interp.stack_push(result)
            return

        # Case 2: Two numbers
        a = interp.stack_pop()
        if a is None or b is None:
            interp.stack_push(None)
            return
        interp.stack_push(a * b)

    @DirectWord(
        "( a:number b:number -- product:number ) OR ( numbers:number[] -- product:number )",
        "Multiply two numbers or product of array",
        "MULTIPLY",
    )
    async def times_MULTIPLY(self, interp: Interpreter) -> None:
        return await self.times(interp)

    @WordDecorator("( a:number b:number -- quotient:number )", "Divide a by b", "/")
    async def divide_by(self, a: float | int | None, b: float | int | None) -> float | None:
        if a is None or b is None:
            return None
        if b == 0:
            return None
        return a / b

    @WordDecorator("( a:number b:number -- quotient:number )", "Divide a by b", "DIVIDE")
    async def divide_by_DIVIDE(self, a: float | int | None, b: float | int | None) -> float | None:
        if a is None or b is None:
            return None
        if b == 0:
            return None
        return a / b

    @WordDecorator("( m:number n:number -- remainder:number )", "Modulo operation (m % n)")
    async def MOD(self, m: float | int | None, n: float | int | None) -> float | int | None:
        if m is None or n is None:
            return None
        return m % n

    # ==================
    # Aggregates
    # ==================

    @WordDecorator("( items:any[] -- mean:any )", "Calculate mean of array (handles numbers, strings, objects)")
    async def MEAN(self, items: Any) -> Any:
        if not items or (isinstance(items, list) and len(items) == 0):
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
            all_keys: set[str] = set()

            # Collect all keys
            for obj in filtered:
                for key in obj.keys():
                    all_keys.add(key)

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

    @DirectWord(
        "( a:number b:number -- max:number ) OR ( items:number[] -- max:number )", "Maximum of two numbers or array", "MAX"
    )
    async def MAX(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            if len(b) == 0:
                interp.stack_push(None)
                return
            interp.stack_push(max(b))
            return

        # Case 2: Two values
        a = interp.stack_pop()
        interp.stack_push(max(a, b))

    @DirectWord(
        "( a:number b:number -- min:number ) OR ( items:number[] -- min:number )", "Minimum of two numbers or array", "MIN"
    )
    async def MIN(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            if len(b) == 0:
                interp.stack_push(None)
                return
            interp.stack_push(min(b))
            return

        # Case 2: Two values
        a = interp.stack_pop()
        interp.stack_push(min(a, b))

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

    @WordDecorator("( num:number digits:number -- result:string )", "Format number with fixed decimal places", ">FIXED")
    async def to_FIXED(self, num: float | int | None, digits: int) -> str | None:
        if num is None:
            return None

        return f"{num:.{digits}f}"

    @WordDecorator("( num:number -- int:number )", "Round to nearest integer")
    async def ROUND(self, num: float | int | None) -> int | None:
        if num is None:
            return None

        return round(num)

    # ==================
    # Special Values
    # ==================

    @WordDecorator("( -- infinity:number )", "Push Infinity value")
    async def INFINITY(self) -> float:
        return float("inf")

    @WordDecorator(
        "( low:number high:number -- random:number )", "Generate random number in range [low, high)", "UNIFORM-RANDOM"
    )
    async def UNIFORM_RANDOM(self, low: float | int, high: float | int) -> float:
        import random

        return random.random() * (high - low) + low

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

    @DirectWord("( value:number min:number max:number -- clamped:number )", "Constrain value to range [min, max]", "CLAMP")
    async def CLAMP(
            self, interp: Interpreter
    ) -> None:
        max_val = interp.stack_pop()
        min_val = interp.stack_pop()
        value = interp.stack_pop()
        if value is None or min_val is None or max_val is None:
            interp.stack_push(None)
        else:
            interp.stack_push(max(min_val, min(max_val, value)))

    # ==================
    # Comparison (from original implementation)
    # ==================

    @WordDecorator("( a:any b:any -- result:bool )", "Less than", "<")
    async def less_than(self, a: Any, b: Any) -> bool:
        return a < b

    @WordDecorator("( a:any b:any -- result:bool )", "Greater than", ">")
    async def greater_than(self, a: Any, b: Any) -> bool:
        return a > b

    @WordDecorator("( a:any b:any -- result:bool )", "Less than or equal", "<=")
    async def less_equal(self, a: Any, b: Any) -> bool:
        return a <= b

    @WordDecorator("( a:any b:any -- result:bool )", "Greater than or equal", ">=")
    async def greater_equal(self, a: Any, b: Any) -> bool:
        return a >= b

    # ==================
    # Constants (from original implementation)
    # ==================

    @WordDecorator("( -- pi:float )", "Push mathematical constant pi")
    async def PI(self) -> float:
        return math.pi

    @WordDecorator("( -- e:float )", "Push mathematical constant e")
    async def E(self) -> float:
        return math.e
