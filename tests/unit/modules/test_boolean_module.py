"""Tests for Boolean Module - ported from TypeScript."""

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


# ========================================
# Comparison Operations
# ========================================


class TestComparisonOperations:
    """Test comparison operations."""

    @pytest.mark.asyncio
    async def test_comparison(self, interp):
        """Test all comparison operators."""
        await interp.run("""
            2 4 ==
            2 4 !=
            2 4 <
            2 4 <=
            2 4 >
            2 4 >=
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is True
        assert stack[3] is True
        assert stack[4] is False
        assert stack[5] is False

    @pytest.mark.asyncio
    async def test_equality_with_different_types(self, interp):
        """Test equality with different types."""
        await interp.run("2 2 ==")
        assert interp.stack_pop() is True

        await interp.run("'hello' 'hello' ==")
        assert interp.stack_pop() is True

        await interp.run("TRUE TRUE ==")
        assert interp.stack_pop() is True


# ========================================
# Logic Operations
# ========================================


class TestLogicOperations:
    """Test logical operations."""

    @pytest.mark.asyncio
    async def test_logic(self, interp):
        """Test logical operators."""
        await interp.run("""
            FALSE FALSE OR
            [FALSE FALSE TRUE FALSE] OR
            FALSE TRUE AND
            [FALSE FALSE TRUE FALSE] AND
            FALSE NOT
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is False
        assert stack[3] is False
        assert stack[4] is True

    @pytest.mark.asyncio
    async def test_or_with_two_values(self, interp):
        """Test OR with two boolean values."""
        await interp.run("TRUE FALSE OR")
        assert interp.stack_pop() is True

        await interp.run("FALSE FALSE OR")
        assert interp.stack_pop() is False

        await interp.run("TRUE TRUE OR")
        assert interp.stack_pop() is True

    @pytest.mark.asyncio
    async def test_or_with_array(self, interp):
        """Test OR with array of booleans."""
        await interp.run("[FALSE FALSE FALSE] OR")
        assert interp.stack_pop() is False

        await interp.run("[TRUE FALSE FALSE] OR")
        assert interp.stack_pop() is True

        await interp.run("[FALSE TRUE FALSE] OR")
        assert interp.stack_pop() is True

    @pytest.mark.asyncio
    async def test_and_with_two_values(self, interp):
        """Test AND with two boolean values."""
        await interp.run("TRUE TRUE AND")
        assert interp.stack_pop() is True

        await interp.run("TRUE FALSE AND")
        assert interp.stack_pop() is False

        await interp.run("FALSE FALSE AND")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_and_with_array(self, interp):
        """Test AND with array of booleans."""
        await interp.run("[TRUE TRUE TRUE] AND")
        assert interp.stack_pop() is True

        await interp.run("[TRUE FALSE TRUE] AND")
        assert interp.stack_pop() is False

        await interp.run("[FALSE FALSE FALSE] AND")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_not(self, interp):
        """Test NOT operator."""
        await interp.run("TRUE NOT")
        assert interp.stack_pop() is False

        await interp.run("FALSE NOT")
        assert interp.stack_pop() is True

    @pytest.mark.asyncio
    async def test_xor(self, interp):
        """Test XOR operator."""
        await interp.run("TRUE TRUE XOR")
        assert interp.stack_pop() is False

        await interp.run("TRUE FALSE XOR")
        assert interp.stack_pop() is True

        await interp.run("FALSE TRUE XOR")
        assert interp.stack_pop() is True

        await interp.run("FALSE FALSE XOR")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_nand(self, interp):
        """Test NAND operator."""
        await interp.run("TRUE TRUE NAND")
        assert interp.stack_pop() is False

        await interp.run("TRUE FALSE NAND")
        assert interp.stack_pop() is True

        await interp.run("FALSE TRUE NAND")
        assert interp.stack_pop() is True

        await interp.run("FALSE FALSE NAND")
        assert interp.stack_pop() is True


# ========================================
# Membership Operations
# ========================================


class TestMembershipOperations:
    """Test membership operations."""

    @pytest.mark.asyncio
    async def test_in(self, interp):
        """Test IN operator."""
        await interp.run("""
            'alpha' ['beta' 'gamma'] IN
            'alpha' ['beta' 'gamma' 'alpha'] IN
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is False
        assert stack[1] is True

    @pytest.mark.asyncio
    async def test_in_with_numbers(self, interp):
        """Test IN with numbers."""
        await interp.run("5 [1 2 3 4 5] IN")
        assert interp.stack_pop() is True

        await interp.run("10 [1 2 3 4 5] IN")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_in_with_empty_array(self, interp):
        """Test IN with empty array."""
        await interp.run("'test' [] IN")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_any(self, interp):
        """Test ANY operator."""
        await interp.run("""
            ['alpha' 'beta'] ['beta' 'gamma'] ANY
            ['delta' 'beta'] ['gamma' 'alpha'] ANY
            ['alpha' 'beta'] [] ANY
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is True
        assert stack[1] is False
        assert stack[2] is True

    @pytest.mark.asyncio
    async def test_any_with_numbers(self, interp):
        """Test ANY with numbers."""
        await interp.run("[1 2 3] [3 4 5] ANY")
        assert interp.stack_pop() is True

        await interp.run("[1 2 3] [4 5 6] ANY")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_all(self, interp):
        """Test ALL operator."""
        await interp.run("""
            ['alpha' 'beta'] ['beta' 'gamma'] ALL
            ['delta' 'beta'] ['beta'] ALL
            ['alpha' 'beta'] [] ALL
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is True

    @pytest.mark.asyncio
    async def test_all_with_numbers(self, interp):
        """Test ALL with numbers."""
        await interp.run("[1 2 3 4 5] [2 3 4] ALL")
        assert interp.stack_pop() is True

        await interp.run("[1 2 3] [2 3 4] ALL")
        assert interp.stack_pop() is False


# ========================================
# Type Conversion
# ========================================


class TestTypeConversion:
    """Test type conversion operations."""

    @pytest.mark.asyncio
    async def test_to_bool(self, interp):
        """Test >BOOL conversion."""
        await interp.run("""
            NULL >BOOL
            0 >BOOL
            1 >BOOL
            '' >BOOL
            'Hi' >BOOL
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] is False
        assert stack[1] is False
        assert stack[2] is True
        assert stack[3] is False
        assert stack[4] is True

    @pytest.mark.asyncio
    async def test_to_bool_with_arrays(self, interp):
        """Test >BOOL with arrays."""
        # Note: In Python, empty arrays are falsy: bool([]) == False
        # This differs from JavaScript where empty arrays are truthy
        await interp.run("[] >BOOL")
        assert interp.stack_pop() is False

        await interp.run("[1] >BOOL")
        assert interp.stack_pop() is True

    @pytest.mark.asyncio
    async def test_to_bool_with_objects(self, interp):
        """Test >BOOL with objects."""
        await interp.run("[['a' 1]] REC >BOOL")
        assert interp.stack_pop() is True
