"""Integration tests for dot symbol functionality."""

import pytest

from forthic import IntentionalStopError, StandardInterpreter, UnknownWordError


class TestDotSymbol:
    """Test dot symbol functionality in the interpreter."""

    @pytest.mark.asyncio
    async def test_dot_symbols_work_as_strings(self) -> None:
        """Test that dot symbols are pushed as strings onto the stack."""
        interp = StandardInterpreter()

        # Test that dot symbols are pushed as strings onto the stack
        await interp.run(".symbol .test-123")

        stack = interp.get_stack().get_items()
        assert stack == ["symbol", "test-123"]

    @pytest.mark.asyncio
    async def test_peek_and_stack_debug_words(self) -> None:
        """Test that PEEK! and STACK! work as debug words."""
        interp = StandardInterpreter()

        # These should trigger the debugging words and stop execution
        error1 = None
        error2 = None

        try:
            await interp.run("42 PEEK!")
        except Exception as e:
            error1 = e

        try:
            await interp.run("1 2 STACK!")
        except Exception as e:
            error2 = e

        # Both should throw IntentionalStopError, indicating they executed as words
        assert isinstance(error1, IntentionalStopError)
        assert isinstance(error2, IntentionalStopError)

    @pytest.mark.asyncio
    async def test_dot_symbols_mixed_with_regular_tokens(self) -> None:
        """Test dot symbols mixed with regular tokens."""
        interp = StandardInterpreter()

        await interp.run('[ .key1 "value1" .key2 "value2" ]')

        stack = interp.get_stack().get_items()
        assert stack == [["key1", "value1", "key2", "value2"]]

    @pytest.mark.asyncio
    async def test_minimum_length_boundary_cases(self) -> None:
        """Test minimum length boundary cases for dot symbols."""
        interp = StandardInterpreter()

        # .ab should be a dot symbol
        await interp.run(".ab")
        assert interp.get_stack().get_items() == ["ab"]

        # Clear stack
        interp.get_stack().get_raw_items().clear()

        # .a should now also be a dot symbol (one-character symbols supported)
        await interp.run(".a")
        assert interp.get_stack().get_items() == ["a"]

        # Clear stack
        interp.get_stack().get_raw_items().clear()

        # Just a dot by itself should be treated as a word (will cause UnknownWordError)
        error = None
        try:
            await interp.run(".")
        except Exception as e:
            error = e

        assert isinstance(error, UnknownWordError)
