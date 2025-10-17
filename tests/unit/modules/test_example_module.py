"""
Unit tests for ExampleModule
"""
import pytest

from examples.dynamic_module_example import ExampleModule
from forthic.interpreter import StandardInterpreter


class TestExampleModule:
    """Test suite for ExampleModule"""

    @pytest.mark.asyncio
    async def test_multiply(self):
        """Test MULTIPLY word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push(5)
        interp.stack_push(3)
        await interp.run('MULTIPLY')

        result = interp.stack_pop()
        assert result == 15

    @pytest.mark.asyncio
    async def test_square(self):
        """Test SQUARE word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push(7)
        await interp.run('SQUARE')

        result = interp.stack_pop()
        assert result == 49

    @pytest.mark.asyncio
    async def test_power(self):
        """Test POWER word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push(2)
        interp.stack_push(8)
        await interp.run('POWER')

        result = interp.stack_pop()
        assert result == 256

    @pytest.mark.asyncio
    async def test_reverse_text(self):
        """Test REVERSE-TEXT word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push("hello")
        await interp.run('REVERSE_TEXT')

        result = interp.stack_pop()
        assert result == "olleh"

    @pytest.mark.asyncio
    async def test_count_char(self):
        """Test COUNT_CHAR word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push("hello world")
        interp.stack_push("l")
        await interp.run('COUNT_CHAR')

        result = interp.stack_pop()
        assert result == 3

    @pytest.mark.asyncio
    async def test_make_sentence(self):
        """Test MAKE_SENTENCE word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push(["Hello", "world", "from", "Forthic"])
        await interp.run('MAKE_SENTENCE')

        result = interp.stack_pop()
        assert result == "Hello world from Forthic"

    @pytest.mark.asyncio
    async def test_sum_list(self):
        """Test SUM_LIST word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push([1, 2, 3, 4, 5])
        await interp.run('SUM_LIST')

        result = interp.stack_pop()
        assert result == 15

    @pytest.mark.asyncio
    async def test_avg_list(self):
        """Test AVG_LIST word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push([1, 2, 3, 4, 5])
        await interp.run('AVG_LIST')

        result = interp.stack_pop()
        assert result == 3.0

    @pytest.mark.asyncio
    async def test_avg_list_empty(self):
        """Test AVG_LIST with empty list"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push([])
        await interp.run('AVG_LIST')

        result = interp.stack_pop()
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_chunk_list(self):
        """Test CHUNK_LIST word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        interp.stack_push([1, 2, 3, 4, 5, 6, 7])
        interp.stack_push(3)
        await interp.run('CHUNK_LIST')

        result = interp.stack_pop()
        assert result == [[1, 2, 3], [4, 5, 6], [7]]

    @pytest.mark.asyncio
    async def test_fibonacci(self):
        """Test FIBONACCI word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        # Test a few Fibonacci numbers
        test_cases = [
            (0, 0),
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 3),
            (5, 5),
            (6, 8),
            (10, 55)
        ]

        for n, expected in test_cases:
            interp.stack_push(n)
            await interp.run('FIBONACCI')
            result = interp.stack_pop()
            assert result == expected, f"FIBONACCI({n}) should be {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_is_prime(self):
        """Test IS_PRIME word"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        # Test prime numbers
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        for p in primes:
            interp.stack_push(p)
            await interp.run('IS_PRIME')
            result = interp.stack_pop()
            assert result is True, f"{p} should be prime"

        # Test non-prime numbers
        non_primes = [0, 1, 4, 6, 8, 9, 10, 12, 15, 20]
        for n in non_primes:
            interp.stack_push(n)
            await interp.run('IS_PRIME')
            result = interp.stack_pop()
            assert result is False, f"{n} should not be prime"

    @pytest.mark.asyncio
    async def test_map_range(self):
        """Test MAP_RANGE DirectWord"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        # Test squaring numbers 0-4
        interp.stack_push(5)
        interp.stack_push("DUP *")
        await interp.run('MAP_RANGE')

        result = interp.stack_pop()
        assert result == [0, 1, 4, 9, 16]

    @pytest.mark.asyncio
    async def test_complex_operations(self):
        """Test chaining multiple operations"""
        interp = StandardInterpreter()
        example_mod = ExampleModule()
        interp.register_module(example_mod)
        interp.use_modules(['example'])

        # Complex: sum list, square result
        await interp.run('[1 2 3 4 5] SUM_LIST SQUARE')

        result = interp.stack_pop()
        assert result == 225  # (1+2+3+4+5)^2 = 15^2 = 225

    @pytest.mark.asyncio
    async def test_module_metadata(self):
        """Test that module has proper metadata"""
        example_mod = ExampleModule()

        # Check module has name
        assert example_mod.name == "example"

        # Check it has word docs
        assert hasattr(example_mod, 'get_word_docs')
        word_docs = example_mod.get_word_docs()

        # Should have all the words we defined
        word_names = [doc['name'] for doc in word_docs]
        expected_words = [
            'MULTIPLY', 'SQUARE', 'POWER',
            'REVERSE_TEXT', 'COUNT_CHAR', 'MAKE_SENTENCE',
            'SUM_LIST', 'AVG_LIST', 'CHUNK_LIST',
            'FIBONACCI', 'IS_PRIME', 'MAP_RANGE'
        ]

        for word in expected_words:
            assert word in word_names, f"Word {word} not found in module"
