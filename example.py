#!/usr/bin/env python3
"""Example demonstrating Phase 1 Forthic Python runtime."""

import asyncio

from forthic import Interpreter, Module, PushValueWord


async def main() -> None:
    print("=== Forthic Python Runtime - Phase 1 Demo ===\n")

    # Create interpreter
    interp = Interpreter()

    # 1. Push literals
    print("1. Pushing literals:")
    await interp.run("42 3.14 TRUE FALSE")
    print(f"   Stack: {interp.get_stack().get_items()}\n")
    interp.reset()

    # 2. Push strings
    print("2. Pushing strings:")
    await interp.run('"Hello" "Forthic"')
    stack = interp.get_stack()
    print(f"   Stack: [{str(stack[0])}, {str(stack[1])}]\n")
    interp.reset()

    # 3. Create arrays
    print("3. Creating arrays:")
    await interp.run("[1 2 3] [[4 5] [6 7]]")
    print(f"   Stack: {interp.get_stack().get_items()}\n")
    interp.reset()

    # 4. Define and use words
    print("4. Word definitions:")
    await interp.run(": GREET 'Hello, World!' ;")
    await interp.run("GREET")
    print(f"   Stack: {str(interp.get_stack()[0])}\n")
    interp.reset()

    # 5. Nested definitions
    print("5. Nested definitions:")
    await interp.run(": BASE 10 ;")
    await interp.run(": DERIVED BASE BASE ;")
    await interp.run("DERIVED")
    print(f"   Stack: {interp.get_stack().get_items()}\n")
    interp.reset()

    # 6. Memoized words
    print("6. Memoized words:")
    await interp.run("@: DATA [1 2 3 4 5] ;")
    await interp.run("DATA DATA")  # Both should return same array
    print(f"   Stack: {interp.get_stack().get_items()}\n")
    interp.reset()

    # 7. Custom module
    print("7. Custom module:")
    module = Module("math")

    # Add a simple DOUBLE word (just pushes number twice for demo)
    async def double_word(interp: Interpreter) -> None:
        val = interp.stack_pop()
        interp.stack_push(val)
        interp.stack_push(val)

    word = PushValueWord("DOUBLE", None)
    word.execute = double_word  # type: ignore
    module.add_exportable_word(word)

    interp.register_module(module)
    interp.use_modules(["math"])

    await interp.run("5 DOUBLE")
    print(f"   Stack: {interp.get_stack().get_items()}\n")
    interp.reset()

    # 8. Inline module
    print("8. Inline module:")
    await interp.run("{mymodule : WORD 42 ; }")
    module = interp.find_module("mymodule")
    print(f"   Created module: {module.get_name()}\n")

    print("=== Phase 1 Complete! ===")
    print("\nNext: Phase 2 will add the @Word decorator system")


if __name__ == "__main__":
    asyncio.run(main())
