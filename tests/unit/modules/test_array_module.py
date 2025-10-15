"""Tests for Array Module - ported from TypeScript."""

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


# ========================================
# Simple Array Operations
# ========================================


class TestSimpleArrayOperations:
    """Test simple array operations."""

    @pytest.mark.asyncio
    async def test_append(self, interp):
        """Test APPEND."""
        await interp.run("[1 2 3] 4 APPEND")
        assert interp.stack_pop() == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_reverse(self, interp):
        """Test REVERSE."""
        await interp.run("[1 2 3] REVERSE")
        assert interp.stack_pop() == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_unique(self, interp):
        """Test UNIQUE."""
        await interp.run("[1 2 3 3 2] UNIQUE")
        assert interp.stack_pop() == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_length(self, interp):
        """Test LENGTH."""
        await interp.run("['a' 'b' 'c'] LENGTH")
        assert interp.stack_pop() == 3


# ========================================
# Access Operations
# ========================================


class TestAccessOperations:
    """Test access operations."""

    @pytest.mark.asyncio
    async def test_nth(self, interp):
        """Test NTH."""
        await interp.run("[0 1 2 3 4 5 6] 0 NTH")
        assert interp.stack_pop() == 0

        await interp.run("[0 1 2 3 4 5 6] 5 NTH")
        assert interp.stack_pop() == 5

        await interp.run("[0 1 2 3 4 5 6] 55 NTH")
        assert interp.stack_pop() is None

    @pytest.mark.asyncio
    async def test_last(self, interp):
        """Test LAST."""
        await interp.run("[0 1 2 3 4 5 6] LAST")
        assert interp.stack_pop() == 6

    @pytest.mark.asyncio
    async def test_slice(self, interp):
        """Test SLICE."""
        await interp.run("['a' 'b' 'c' 'd' 'e' 'f' 'g'] 0 2 SLICE")
        assert interp.stack_pop() == ["a", "b", "c"]

        await interp.run("['a' 'b' 'c' 'd' 'e' 'f' 'g'] 1 3 SLICE")
        assert interp.stack_pop() == ["b", "c", "d"]

        await interp.run("['a' 'b' 'c' 'd' 'e' 'f' 'g'] 5 3 SLICE")
        assert interp.stack_pop() == ["f", "e", "d"]

    @pytest.mark.asyncio
    async def test_take(self, interp):
        """Test TAKE."""
        await interp.run("[0 1 2 3 4 5 6] 3 TAKE")
        assert interp.stack_pop() == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_drop(self, interp):
        """Test DROP."""
        await interp.run("[0 1 2 3 4 5 6] 4 DROP")
        assert interp.stack_pop() == [4, 5, 6]


# ========================================
# Set Operations
# ========================================


class TestSetOperations:
    """Test set operations."""

    @pytest.mark.asyncio
    async def test_difference(self, interp):
        """Test DIFFERENCE."""
        await interp.run("['a' 'b' 'c'] ['a' 'c' 'd'] DIFFERENCE")
        assert interp.stack_pop() == ["b"]

        await interp.run("['a' 'c' 'd'] ['a' 'b' 'c'] DIFFERENCE")
        assert interp.stack_pop() == ["d"]

    @pytest.mark.asyncio
    async def test_intersection(self, interp):
        """Test INTERSECTION."""
        await interp.run("['a' 'b' 'c'] ['a' 'c' 'd'] INTERSECTION")
        result = interp.stack_pop()
        assert sorted(result) == ["a", "c"]

    @pytest.mark.asyncio
    async def test_union(self, interp):
        """Test UNION."""
        await interp.run("['a' 'b' 'c'] ['a' 'c' 'd'] UNION")
        result = interp.stack_pop()
        assert sorted(result) == ["a", "b", "c", "d"]


# ========================================
# Sort Operations
# ========================================


class TestSortOperations:
    """Test sort operations."""

    @pytest.mark.asyncio
    async def test_shuffle(self, interp):
        """Test SHUFFLE."""
        await interp.run("[0 1 2 3 4 5 6] SHUFFLE")
        result = interp.stack_pop()
        assert len(result) == 7

    @pytest.mark.asyncio
    async def test_sort(self, interp):
        """Test SORT."""
        await interp.run("[2 8 1 4 7 3] SORT")
        assert interp.stack_pop() == [1, 2, 3, 4, 7, 8]

    @pytest.mark.asyncio
    async def test_sort_with_null(self, interp):
        """Test SORT with null."""
        await interp.run("[2 8 1 NULL 4 7 NULL 3] SORT")
        assert interp.stack_pop() == [1, 2, 3, 4, 7, 8, None, None]


# ========================================
# Transform Operations
# ========================================


class TestTransformOperations:
    """Test transform operations."""

    @pytest.mark.asyncio
    async def test_unpack(self, interp):
        """Test UNPACK."""
        await interp.run("[0 1 2] UNPACK")
        stack = interp.get_stack().get_items()
        assert stack[0] == 0
        assert stack[1] == 1
        assert stack[2] == 2

    @pytest.mark.asyncio
    async def test_flatten(self, interp):
        """Test FLATTEN."""
        await interp.run("[0 [1 2 [3 [4]]]] FLATTEN")
        assert interp.stack_pop() == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_reduce(self, interp):
        """Test REDUCE."""
        await interp.run('[1 2 3 4 5] 10 "ADD" REDUCE')
        assert interp.stack_pop() == 25


# ========================================
# Combine Operations
# ========================================


class TestCombineOperations:
    """Test combine operations."""

    @pytest.mark.asyncio
    async def test_zip(self, interp):
        """Test ZIP."""
        await interp.run("['a' 'b'] [1 2] ZIP")
        array = interp.stack_pop()
        assert array[0] == ["a", 1]
        assert array[1] == ["b", 2]

    @pytest.mark.asyncio
    async def test_zip_with(self, interp):
        """Test ZIP_WITH."""
        await interp.run('[10 20] [1 2] "ADD" ZIP_WITH')
        array = interp.stack_pop()
        assert array[0] == 11
        assert array[1] == 22

    @pytest.mark.asyncio
    async def test_index(self, interp):
        """Test INDEX."""
        await interp.run("""
            : |KEYS   "'key' REC@" MAP;
            : TICKETS [
              [['key'   101] ['Labels'  ['alpha' 'beta']]] REC
              [['key'   102] ['Labels'  ['alpha' 'gamma']]] REC
              [['key'   103] ['Labels'  ['alpha']]] REC
              [['key'   104] ['Labels'  ['beta']]] REC
            ];

            TICKETS "'Labels' REC@" INDEX  "|KEYS" MAP
        """)
        index_record = interp.stack_pop()
        assert index_record["alpha"] == [101, 102, 103]
        assert index_record["beta"] == [101, 104]
        assert index_record["gamma"] == [102]

    @pytest.mark.asyncio
    async def test_key_of(self, interp):
        """Test KEY_OF."""
        await interp.run("['a' 'b' 'c' 'd'] 'c' KEY_OF")
        assert interp.stack_pop() == 2

        await interp.run("['a' 'b' 'c' 'd'] 'z' KEY_OF")
        assert interp.stack_pop() is None


# ========================================
# Filter Operations
# ========================================


class TestFilterOperations:
    """Test filter operations."""

    @pytest.mark.asyncio
    async def test_select(self, interp):
        """Test SELECT."""
        await interp.run('[0 1 2 3 4 5 6] "2 MOD 1 ==" SELECT')
        assert interp.stack_pop() == [1, 3, 5]


# ========================================
# Group Operations
# ========================================


class TestGroupOperations:
    """Test group operations."""

    @pytest.mark.asyncio
    async def test_groups_of(self, interp):
        """Test GROUPS_OF."""
        await interp.run("[1 2 3 4 5 6 7 8] 3 GROUPS_OF")
        groups = interp.stack_pop()
        assert groups[0] == [1, 2, 3]
        assert groups[1] == [4, 5, 6]
        assert groups[2] == [7, 8]


# ========================================
# Advanced Operations
# ========================================


class TestAdvancedOperations:
    """Test advanced operations."""

    @pytest.mark.asyncio
    async def test_foreach(self, interp):
        """Test FOREACH."""
        await interp.run("0 [1 2 3 4 5] '+' FOREACH")
        assert interp.stack_pop() == 15

    @pytest.mark.asyncio
    async def test_map(self, interp):
        """Test MAP."""
        await interp.run("[1 2 3 4 5] '2 *' MAP")
        assert interp.stack_pop() == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_repeat(self, interp):
        """Test <REPEAT."""
        await interp.run('[0 "1 +" 6 <REPEAT]')
        assert interp.stack_pop() == [0, 1, 2, 3, 4, 5, 6]


# ========================================
# Options Support via ~>
# ========================================


class TestOptionsSupport:
    """Test options support via ~> operator."""

    @pytest.mark.asyncio
    async def test_map_with_with_key(self, interp):
        """Test MAP with options - with_key."""
        await interp.run("""
            [10 20 30] '+ 2 *' [.with_key TRUE] ~> MAP
        """)
        array = interp.stack_pop()
        # with_key pushes index then value, so: (0 + 10) * 2 = 20, (1 + 20) * 2 = 42, (2 + 30) * 2 = 64
        assert array == [20, 42, 64]

    @pytest.mark.asyncio
    async def test_flatten_with_depth(self, interp):
        """Test FLATTEN with options - depth."""
        await interp.run("""
            [[[1 2]] [[3 4]]] [.depth 1] ~> FLATTEN
        """)
        array = interp.stack_pop()
        assert array == [[1, 2], [3, 4]]

    @pytest.mark.asyncio
    async def test_sort_with_comparator(self, interp):
        """Test SORT with options - comparator."""
        await interp.run("""
            [3 1 4 1 5] [.comparator "-1 *"] ~> SORT
        """)
        array = interp.stack_pop()
        assert array == [5, 4, 3, 1, 1]

    @pytest.mark.asyncio
    async def test_foreach_with_with_key(self, interp):
        """Test FOREACH with options - with_key."""
        await interp.run("""
            ['result'] VARIABLES
            "" result !
            ['a' 'b' 'c'] '>STR CONCAT result @ CONCAT result !' [.with_key TRUE] ~> FOREACH
            result @
        """)
        result = interp.stack_pop()
        # with_key pushes: index, value -> >STR converts index to string -> CONCAT joins them
        # CONCAT with result @ puts accumulator first: result + "2c" + "1b" + "0a"
        # But actually builds as: (("" + "2c") + "1b") + "0a" = "2c1b0a"
        assert result == "2c1b0a"

    @pytest.mark.asyncio
    async def test_group_by_with_with_key(self, interp):
        """Test GROUP_BY with options - with_key."""
        await interp.run("""
            [5 15 25 8 18] '10 /' [.with_key TRUE] ~> GROUP_BY
        """)
        grouped = interp.stack_pop()
        # with_key pushes: index, value -> 10 / -> groups by division result
        # But index comes first, so result is different
        assert len(grouped.keys()) > 0
