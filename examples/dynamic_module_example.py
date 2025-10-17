"""
Example dynamic Forthic module for testing configuration-based loading.

This demonstrates how to create a custom module that can be loaded
via the module configuration system.

Usage:
    1. Create a modules config file pointing to this module
    2. Start the server with --modules-config
    3. Use the module from TypeScript via USE-PY-MODULES
"""

from forthic.decorators import DecoratedModule, Word, DirectWord


class ExampleModule(DecoratedModule):
    """Example module with math and string operations"""

    def __init__(self):
        super().__init__("example")

    # ==================
    # Math Operations
    # ==================

    @Word("( a:int b:int -- c:int )", "Multiply two numbers")
    async def MULTIPLY(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    @Word("( n:int -- n:int )", "Square a number")
    async def SQUARE(self, n: int) -> int:
        """Square a number (n * n)."""
        return n * n

    @Word("( a:int b:int -- c:int )", "Calculate power (a^b)")
    async def POWER(self, a: int, b: int) -> int:
        """Calculate a raised to the power of b."""
        return a ** b

    # ==================
    # String Operations
    # ==================

    @Word("( text:str -- text:str )", "Reverse a string")
    async def REVERSE_TEXT(self, text: str) -> str:
        """Reverse a string."""
        return text[::-1]

    @Word("( text:str char:str -- count:int )", "Count character occurrences")
    async def COUNT_CHAR(self, text: str, char: str) -> int:
        """Count occurrences of a character in text."""
        return text.count(char)

    @Word("( words:list -- sentence:str )", "Join words into sentence")
    async def MAKE_SENTENCE(self, words: list) -> str:
        """Join list of words into a sentence."""
        return " ".join(str(w) for w in words)

    # ==================
    # List Operations
    # ==================

    @Word("( items:list -- sum:int )", "Sum all numbers in list")
    async def SUM_LIST(self, items: list) -> int:
        """Sum all numbers in a list."""
        return sum(items)

    @Word("( items:list -- avg:float )", "Average of numbers in list")
    async def AVG_LIST(self, items: list) -> float:
        """Calculate average of numbers in list."""
        if not items:
            return 0.0
        return sum(items) / len(items)

    @Word("( items:list n:int -- chunks:list )", "Chunk list into groups of n")
    async def CHUNK_LIST(self, items: list, n: int) -> list:
        """Split list into chunks of size n."""
        return [items[i:i + n] for i in range(0, len(items), n)]

    # ==================
    # Utility Operations
    # ==================

    @Word("( n:int -- fibonacci:int )", "Calculate nth Fibonacci number")
    async def FIBONACCI(self, n: int) -> int:
        """Calculate nth Fibonacci number (0-indexed)."""
        if n <= 0:
            return 0
        elif n == 1:
            return 1

        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @Word("( n:int -- is_prime:bool )", "Check if number is prime")
    async def IS_PRIME(self, n: int) -> bool:
        """Check if a number is prime."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False

        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True

    @DirectWord("( n:int forthic:str -- results:list )", "Map Forthic over range")
    async def MAP_RANGE(self, interp) -> None:
        """
        Map Forthic code over range(n).

        Example: 5 "DUP *" MAP-RANGE  # [0, 1, 4, 9, 16]
        """
        forthic = interp.stack_pop()
        n = interp.stack_pop()

        string_location = interp.get_string_location()
        results = []

        for i in range(n):
            interp.stack_push(i)
            await interp.run(forthic, string_location)
            results.append(interp.stack_pop())

        interp.stack_push(results)
