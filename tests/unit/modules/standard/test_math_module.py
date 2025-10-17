"""Tests for Math Module - ported from TypeScript."""

import math

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


class TestArithmetic:
    """Test basic arithmetic operations."""

    @pytest.mark.asyncio
    async def test_arithmetic(self, interp):
        """Test basic arithmetic operations."""
        await interp.run("""
            2 4 +
            2 4 -
            2 4 *
            2 4 /
            5 3 MOD
            2.51 ROUND
        """)
        stack = interp.get_stack().get_items()
        assert stack[0] == 6
        assert stack[1] == -2
        assert stack[2] == 8
        assert stack[3] == 0.5
        assert stack[4] == 2
        assert stack[5] == 3

    @pytest.mark.asyncio
    async def test_divide(self, interp):
        """Test division."""
        interp.stack_push(10)
        interp.stack_push(2)
        await interp.run("/")
        assert interp.stack_pop() == 5


class TestComparison:
    """Test comparison operations."""

    @pytest.mark.asyncio
    async def test_less_than(self, interp):
        """Test < operator."""
        await interp.run("2 4 <")
        assert interp.stack_pop() is True

        await interp.run("4 2 <")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_greater_than(self, interp):
        """Test > operator."""
        await interp.run("4 2 >")
        assert interp.stack_pop() is True

        await interp.run("2 4 >")
        assert interp.stack_pop() is False


class TestMaxMin:
    """Test MAX and MIN operations."""

    @pytest.mark.asyncio
    async def test_max_of_array(self, interp):
        """Test MAX of an array of numbers."""
        interp.stack_push([14, 8, 55, 4, 5])
        await interp.run("MAX")
        assert interp.stack_pop() == 55

    @pytest.mark.asyncio
    async def test_min_of_array(self, interp):
        """Test MIN of an array of numbers."""
        interp.stack_push([14, 8, 55, 4, 5])
        await interp.run("MIN")
        assert interp.stack_pop() == 4


class TestRounding:
    """Test rounding operations."""

    @pytest.mark.asyncio
    async def test_abs(self, interp):
        """Test ABS function."""
        await interp.run("5 ABS")
        assert interp.stack_pop() == 5

        await interp.run("-10 ABS")
        assert interp.stack_pop() == 10

        await interp.run("0 ABS")
        assert interp.stack_pop() == 0

    @pytest.mark.asyncio
    async def test_sqrt(self, interp):
        """Test SQRT function."""
        await interp.run("16 SQRT")
        assert interp.stack_pop() == 4

        await interp.run("25 SQRT")
        assert interp.stack_pop() == 5

        await interp.run("2 SQRT")
        result = interp.stack_pop()
        assert abs(result - 1.414) < 0.001

    @pytest.mark.asyncio
    async def test_floor(self, interp):
        """Test FLOOR function."""
        await interp.run("3.7 FLOOR")
        assert interp.stack_pop() == 3

        await interp.run("-2.3 FLOOR")
        assert interp.stack_pop() == -3

        await interp.run("5 FLOOR")
        assert interp.stack_pop() == 5

    @pytest.mark.asyncio
    async def test_ceil(self, interp):
        """Test CEIL function."""
        await interp.run("3.1 CEIL")
        assert interp.stack_pop() == 4

        await interp.run("-2.9 CEIL")
        assert interp.stack_pop() == -2

        await interp.run("5 CEIL")
        assert interp.stack_pop() == 5


class TestConstants:
    """Test mathematical constants."""

    @pytest.mark.asyncio
    async def test_pi(self, interp):
        """Test PI constant."""
        await interp.run("PI")
        result = interp.stack_pop()
        assert abs(result - math.pi) < 0.0001

    @pytest.mark.asyncio
    async def test_e(self, interp):
        """Test E constant."""
        await interp.run("E")
        result = interp.stack_pop()
        assert abs(result - math.e) < 0.0001

    @pytest.mark.asyncio
    async def test_infinity(self, interp):
        """Test INFINITY constant."""
        await interp.run("INFINITY")
        assert interp.stack_pop() == float('inf')


class TestMean:
    """Test MEAN operations."""

    @pytest.mark.asyncio
    async def test_mean_of_numbers(self, interp):
        """Test MEAN of an array of numbers."""
        interp.stack_push([1, 2, 3, 4, 5])
        await interp.run("MEAN")
        assert interp.stack_pop() == 3

    @pytest.mark.asyncio
    async def test_mean_of_letters(self, interp):
        """Test MEAN of an array of letters."""
        interp.stack_push(["a", "a", "b", "c"])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 0.5, "b": 0.25, "c": 0.25}

    @pytest.mark.asyncio
    async def test_mean_with_null_values(self, interp):
        """Test MEAN of an array with null values."""
        interp.stack_push([1, 2, 3, None, 4, None, 5])
        await interp.run("MEAN")
        assert interp.stack_pop() == 3

    @pytest.mark.asyncio
    async def test_mean_of_letters_with_nulls(self, interp):
        """Test MEAN of letters array with null values."""
        interp.stack_push(["a", "a", None, "b", None, "c"])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 0.5, "b": 0.25, "c": 0.25}

    @pytest.mark.asyncio
    async def test_mean_of_objects(self, interp):
        """Test MEAN of an array of objects."""
        interp.stack_push([
            {"a": 1, "b": 0},
            {"a": 2, "b": 0},
            {"a": 3, "b": 0},
        ])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 2, "b": 0}

    @pytest.mark.asyncio
    async def test_mean_of_objects_with_mixed_types(self, interp):
        """Test MEAN of objects with both numbers and strings."""
        interp.stack_push([
            {"a": 0},
            {"a": 1, "b": "To Do"},
            {"a": 2, "b": "To Do"},
            {"a": 3, "b": "In Progress"},
            {"a": 4, "b": "Done"},
        ])
        await interp.run("MEAN")
        assert interp.stack_pop() == {
            "a": 2,
            "b": {"To Do": 0.5, "In Progress": 0.25, "Done": 0.25},
        }


class TestConverters:
    """Test type conversion functions."""

    @pytest.mark.asyncio
    async def test_to_int(self, interp):
        """Test >INT converter."""
        await interp.run('"3" >INT')
        assert interp.stack_pop() == 3

        await interp.run("4 >INT")
        assert interp.stack_pop() == 4

        await interp.run("4.6 >INT")
        assert interp.stack_pop() == 4

    @pytest.mark.asyncio
    async def test_to_float(self, interp):
        """Test >FLOAT converter."""
        await interp.run('"1.2" >FLOAT')
        assert interp.stack_pop() == 1.2

        await interp.run("2 >FLOAT")
        assert interp.stack_pop() == 2.0

    @pytest.mark.asyncio
    async def test_to_fixed(self, interp):
        """Test >FIXED converter."""
        await interp.run("22 7 / 2 >FIXED")
        assert interp.stack_pop() == "3.14"


class TestAdvancedMath:
    """Test advanced math functions."""

    @pytest.mark.asyncio
    async def test_clamp(self, interp):
        """Test CLAMP function."""
        await interp.run("5 0 10 CLAMP")
        assert interp.stack_pop() == 5

        await interp.run("-5 0 10 CLAMP")
        assert interp.stack_pop() == 0

        await interp.run("15 0 10 CLAMP")
        assert interp.stack_pop() == 10

        await interp.run("0 0 10 CLAMP")
        assert interp.stack_pop() == 0

        await interp.run("10 0 10 CLAMP")
        assert interp.stack_pop() == 10

        await interp.run("NULL 0 10 CLAMP")
        assert interp.stack_pop() is None

    @pytest.mark.asyncio
    async def test_sum(self, interp):
        """Test SUM function."""
        await interp.run("[1 2 3 4 5] SUM")
        assert interp.stack_pop() == 15

        await interp.run("[] SUM")
        assert interp.stack_pop() == 0

        await interp.run("[10] SUM")
        assert interp.stack_pop() == 10

        await interp.run("[1 2 NULL 3 4] SUM")
        assert interp.stack_pop() == 10
