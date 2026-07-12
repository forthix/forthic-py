"""Boolean module - Boolean and logical operations.

Provides comparison, logical operations, and membership tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
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
- Membership: IN, ANY, ALL
- Conversion: >BOOL

## Examples
5 3 >
"hello" "hello" ==
[1 2 3] [4 5 6] OR
2 [1 2 3] IN
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

    @ForthicDirectWord(
        "( a:boolean b:boolean -- result:boolean ) OR ( bools:boolean[] -- result:boolean )",
        "Logical OR of two values or array",
        "OR",
    )
    async def OR(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            for val in b:
                if is_truthy(val):
                    interp.stack_push(True)
                    return
            interp.stack_push(False)
            return

        # Case 2: Two values (JS ||: first operand if truthy, else second)
        a = interp.stack_pop()
        interp.stack_push(a if is_truthy(a) else b)

    @ForthicDirectWord(
        "( a:boolean b:boolean -- result:boolean ) OR ( bools:boolean[] -- result:boolean )",
        "Logical AND of two values or array",
        "AND",
    )
    async def AND(self, interp: Interpreter) -> None:
        b = interp.stack_pop()

        # Case 1: Array on top of stack
        if isinstance(b, list):
            for val in b:
                if not is_truthy(val):
                    interp.stack_push(False)
                    return
            interp.stack_push(True)
            return

        # Case 2: Two values (JS &&: first operand if falsy, else second)
        a = interp.stack_pop()
        interp.stack_push(b if is_truthy(a) else a)

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

    @WordDecorator("( item:any array:any[] -- in:boolean )", "Check if item is in array")
    async def IN(self, item: Any, array: Any) -> bool:
        if not isinstance(array, list):
            return False
        return any(values_equal(item, element) for element in array)

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
