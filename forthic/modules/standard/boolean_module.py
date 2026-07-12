"""Boolean module - Boolean and logical operations.

Provides comparison, logical operations, and membership tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    pass

from ...decorators import DecoratedModule, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...utils import is_truthy, values_equal


class BooleanModule(DecoratedModule):
    """Comparison, logic, and membership operations for boolean values and conditions."""

    def __init__(self) -> None:
        super().__init__("boolean")
        register_module_doc(
            BooleanModule,
            """
Comparison, logic, and membership operations for boolean values and conditions.

## Categories
- Comparison: ==, !=, <, <=, >, >=
- Logic: OR, AND, NOT, XOR, NAND
- Membership: CONTAINS?, ANY, ALL, ANY?, ALL?
- Conversion: >BOOL

## Examples
5 3 >
"hello" "hello" ==
FALSE TRUE OR
[1 2 3] 2 CONTAINS?
            """,
        )

    # ==================
    # Comparison
    # ==================

    @WordDecorator("( a:any b:any -- equal:boolean )", "Test equality", "==")
    async def equals(self, a: Any, b: Any) -> bool:
        return values_equal(a, b)

    @WordDecorator("( a:any b:any -- not_equal:boolean )", "Test inequality", "!=")
    async def not_equals(self, a: Any, b: Any) -> bool:
        return not values_equal(a, b)

    @WordDecorator("( a:any b:any -- less_than:boolean )", "Less than", "<")
    async def less_than(self, a: Any, b: Any) -> bool:
        return cast(bool, a < b)

    @WordDecorator("( a:any b:any -- less_equal:boolean )", "Less than or equal", "<=")
    async def less_than_or_equal(self, a: Any, b: Any) -> bool:
        return cast(bool, a <= b)

    @WordDecorator("( a:any b:any -- greater_than:boolean )", "Greater than", ">")
    async def greater_than(self, a: Any, b: Any) -> bool:
        return cast(bool, a > b)

    @WordDecorator("( a:any b:any -- greater_equal:boolean )", "Greater than or equal", ">=")
    async def greater_than_or_equal(self, a: Any, b: Any) -> bool:
        return cast(bool, a >= b)

    # ==================
    # Logic
    # ==================

    @WordDecorator(
        "( a:boolean b:boolean -- result:boolean )",
        "Logical OR of two values. For arrays use ANY?.",
        "OR",
    )
    async def OR(self, a: Any, b: Any) -> Any:
        if isinstance(a, list) or isinstance(b, list):
            raise ValueError("OR takes two values. For an array of booleans, use ANY?.")
        # JS ||: first operand if truthy, else second
        return a if is_truthy(a) else b

    @WordDecorator(
        "( a:boolean b:boolean -- result:boolean )",
        "Logical AND of two values. For arrays use ALL?.",
        "AND",
    )
    async def AND(self, a: Any, b: Any) -> Any:
        if isinstance(a, list) or isinstance(b, list):
            raise ValueError("AND takes two values. For an array of booleans, use ALL?.")
        # JS &&: first operand if falsy, else second
        return b if is_truthy(a) else a

    @WordDecorator("( bool:boolean -- result:boolean )", "Logical NOT")
    async def NOT(self, bool_val: Any) -> bool:
        return not is_truthy(bool_val)

    @WordDecorator("( a:boolean b:boolean -- result:boolean )", "Logical XOR (exclusive or)")
    async def XOR(self, a: Any, b: Any) -> bool:
        return is_truthy(a) != is_truthy(b)

    @WordDecorator("( a:boolean b:boolean -- result:boolean )", "Logical NAND (not and)")
    async def NAND(self, a: Any, b: Any) -> bool:
        return not (is_truthy(a) and is_truthy(b))

    # ==================
    # Membership
    # ==================

    @WordDecorator(
        "( haystack:any[] needle:any -- bool:boolean )",
        "Check if haystack array contains needle. Container-first arg order.",
        "CONTAINS?",
    )
    async def CONTAINS_q(self, haystack: Any, needle: Any) -> bool:
        if not isinstance(haystack, list):
            return False
        return any(values_equal(needle, element) for element in haystack)

    @WordDecorator(
        "( bools:boolean[] -- result:boolean )",
        "Returns true if any element of the array is truthy. False for empty array.",
        "ANY?",
    )
    async def ANY_q(self, bools: Any) -> bool:
        if not isinstance(bools, list):
            raise ValueError("ANY? requires an array of booleans.")
        return any(is_truthy(v) for v in bools)

    @WordDecorator(
        "( bools:boolean[] -- result:boolean )",
        "Returns true if all elements of the array are truthy. True for empty array.",
        "ALL?",
    )
    async def ALL_q(self, bools: Any) -> bool:
        if not isinstance(bools, list):
            raise ValueError("ALL? requires an array of booleans.")
        return all(is_truthy(v) for v in bools)

    @WordDecorator("( items1:any[] items2:any[] -- any:boolean )", "Check if any item from items1 is in items2")
    async def ANY(self, items1: Any, items2: Any) -> bool:
        if not isinstance(items1, list) or not isinstance(items2, list):
            return False

        # Nothing can match against an empty set (ts #31)
        if len(items2) == 0:
            return False

        # Check if any item from items1 is in items2
        for item in items1:
            if any(values_equal(item, element) for element in items2):
                return True
        return False

    @WordDecorator("( items1:any[] items2:any[] -- all:boolean )", "Check if all items from items2 are in items1")
    async def ALL(self, items1: Any, items2: Any) -> bool:
        if not isinstance(items1, list) or not isinstance(items2, list):
            return False

        # Vacuously true: all zero items are in items1 (matches ts)
        if len(items2) == 0:
            return True

        # Check if all items from items2 are in items1
        for item in items2:
            if not any(values_equal(item, element) for element in items1):
                return False
        return True

    # ==================
    # Conversion
    # ==================

    @WordDecorator("( a:any -- bool:boolean )", "Convert to boolean (JS truthiness: empty containers truthy, NaN falsy)", ">BOOL")
    async def to_BOOL(self, a: Any) -> bool:
        return is_truthy(a)
