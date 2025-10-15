"""Comprehensive integration tests for the standard Forthic interpreter.

This module contains extensive tests covering all major features of the Forthic language
including literals, variables, data structures, control flow, and more.
"""

import pytest
from datetime import datetime, date, time

from forthic import (
    ExtraSemicolonError,
    InvalidVariableNameError,
    MissingSemicolonError,
    PositionedString,
    StackUnderflowError,
    StandardInterpreter,
    UnknownModuleError,
    UnknownWordError,
)


class TestLiteralValues:
    """Test literal value parsing and handling."""

    @pytest.mark.asyncio
    async def test_basic_literal_values(self) -> None:
        """Test basic literal values including booleans, numbers, and dates."""
        interp = StandardInterpreter(timezone="America/Los_Angeles")
        await interp.run("TRUE FALSE 2  3.14 2020-06-05")

        stack = interp.get_stack()
        assert stack[0] is True
        assert stack[1] is False
        assert stack[2] == 2
        assert stack[3] == 3.14
        # Date comparison
        date_val = stack[4]
        assert hasattr(date_val, "year")
        assert date_val.year == 2020
        assert date_val.month == 6
        assert date_val.day == 5

    @pytest.mark.asyncio
    async def test_literal_time_values(self) -> None:
        """Test literal time values."""
        interp = StandardInterpreter()

        await interp.run("9:00")
        time_val = interp.stack_pop()
        assert hasattr(time_val, "hour")
        assert time_val.hour == 9
        assert time_val.minute == 0

        await interp.run("11:30 PM")
        time_val2 = interp.stack_pop()
        assert time_val2.hour == 23
        assert time_val2.minute == 30

        await interp.run("22:15 AM")
        time_val3 = interp.stack_pop()
        assert time_val3.hour == 10
        assert time_val3.minute == 15


class TestVariables:
    """Test variable functionality."""

    @pytest.mark.asyncio
    async def test_declare_variables(self) -> None:
        """Test declaring variables."""
        interp = StandardInterpreter()
        await interp.run("['x' 'y']  VARIABLES")

        app_module = interp.get_app_module()
        variables = app_module.variables

        assert "x" in variables
        assert "y" in variables

    @pytest.mark.asyncio
    async def test_invalid_variable_name(self) -> None:
        """Test that invalid variable names are rejected."""
        interp = StandardInterpreter()

        with pytest.raises(InvalidVariableNameError) as exc_info:
            await interp.run("['__test'] VARIABLES")

        assert exc_info.value.varname == "__test"

    @pytest.mark.asyncio
    async def test_set_and_get_variables(self) -> None:
        """Test setting and getting variable values."""
        interp = StandardInterpreter()
        await interp.run("['x']  VARIABLES")
        await interp.run("24 x !")

        app_module = interp.get_app_module()
        x_var = app_module.variables["x"]
        assert x_var.get_value() == 24

        await interp.run("x @")
        assert interp.stack_pop() == 24

    @pytest.mark.asyncio
    async def test_bang_at(self) -> None:
        """Test !@ operator (set and return)."""
        interp = StandardInterpreter()
        await interp.run("['x']  VARIABLES")
        await interp.run("24 x !@")

        app_module = interp.get_app_module()
        x_var = app_module.variables["x"]
        assert x_var.get_value() == 24
        assert interp.stack_pop() == 24

    @pytest.mark.asyncio
    async def test_auto_create_variables_with_string_names(self) -> None:
        """Test auto-creating variables with string names."""
        interp = StandardInterpreter()

        # Test ! with string variable name (auto-creates variable)
        await interp.run('"hello" "autovar1" !')
        await interp.run('autovar1 @')
        assert interp.stack_pop() == "hello"

        # Verify variable was created in app module
        app_module = interp.get_app_module()
        autovar1 = app_module.variables.get("autovar1")
        assert autovar1 is not None
        assert autovar1.get_value() == "hello"

        # Test @ with string variable name (auto-creates with None)
        await interp.run('"autovar2" @')
        assert interp.stack_pop() is None

        # Verify variable was created
        autovar2 = app_module.variables.get("autovar2")
        assert autovar2 is not None
        assert autovar2.get_value() is None

        # Test !@ with string variable name (auto-creates and returns value)
        await interp.run('"world" "autovar3" !@')
        assert interp.stack_pop() == "world"

        # Verify variable was created with correct value
        autovar3 = app_module.variables.get("autovar3")
        assert autovar3 is not None
        assert autovar3.get_value() == "world"

        # Test that existing variables still work with strings
        await interp.run('"updated" "autovar1" !')
        await interp.run('"autovar1" @')
        assert interp.stack_pop() == "updated"

    @pytest.mark.asyncio
    async def test_auto_create_variables_validation(self) -> None:
        """Test that auto-create variables validation works."""
        interp = StandardInterpreter()

        # Test that __ prefix variables are rejected
        with pytest.raises(Exception):
            await interp.run('"value" "__invalid" !')

        # Test that validation works for @ as well
        with pytest.raises(Exception):
            await interp.run('"__invalid2" @')

        # Test that validation works for !@ as well
        with pytest.raises(Exception):
            await interp.run('"value" "__invalid3" !@')


class TestInterpret:
    """Test INTERPRET word."""

    @pytest.mark.asyncio
    async def test_interpret_literal(self) -> None:
        """Test interpreting a literal."""
        interp = StandardInterpreter()
        await interp.run("'24' INTERPRET")
        assert interp.stack_pop() == 24

    @pytest.mark.asyncio
    async def test_interpret_module(self) -> None:
        """Test interpreting module code."""
        interp = StandardInterpreter()
        await interp.run("""'{module-A  : MESSAGE   "Hi" ;}' INTERPRET""")
        await interp.run("{module-A MESSAGE}")
        assert interp.stack_pop() == "Hi"


class TestRecords:
    """Test record functionality."""

    @pytest.mark.asyncio
    async def test_create_record(self) -> None:
        """Test creating a record."""
        interp = StandardInterpreter()
        await interp.run("""
            [ ["alpha" 2] ["beta" 3] ["gamma" 4] ] REC
        """)

        assert len(interp.get_stack()) == 1

        rec = interp.stack_pop()
        assert rec["alpha"] == 2
        assert rec["gamma"] == 4

    @pytest.mark.asyncio
    async def test_rec_at(self) -> None:
        """Test REC@ (record access)."""
        interp = StandardInterpreter()
        await interp.run("""
            [ ["alpha" 2] ["beta" 3] ["gamma" 4] ] REC
            'beta' REC@
        """)
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == 3

        await interp.run("""
            [10 20 30 40 50] 3 REC@
        """)
        assert interp.stack_pop() == 40

    @pytest.mark.asyncio
    async def test_nested_rec_at(self) -> None:
        """Test nested REC@ operations."""
        interp = StandardInterpreter()
        await interp.run("""
            [ ["alpha" [["alpha1" 20]] REC]
              ["beta" [["beta1"  30]] REC]
            ] REC
            ["beta" "beta1"] REC@
        """)
        assert interp.stack_pop() == 30

        await interp.run("""
            [ [] [] [[3]] ]
            [2 0 0] REC@
        """)
        assert interp.stack_pop() == 3

        await interp.run("""
            [ ["alpha" [["alpha1" 20]] REC]
              ["beta" [["beta1"  [10 20 30]]] REC]
            ] REC
            ["beta" "beta1" 1] REC@
        """)
        assert interp.stack_pop() == 20

    @pytest.mark.asyncio
    async def test_rec_set(self) -> None:
        """Test REC! (record set)."""
        # Case: Set value on a record
        interp = StandardInterpreter()
        await interp.run("""
            [["alpha" 2] ["beta" 3] ["gamma" 4]] REC
            700 'beta' <REC! 'beta' REC@
        """)
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == 700

        # Case: Set a nested value
        interp = StandardInterpreter()
        await interp.run("""
            [] REC "Green" ["2021-03-22" "TEST-1234"] <REC! ["2021-03-22" "TEST-1234"] REC@
        """)
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == "Green"

        # Case: Set value on a NULL
        interp = StandardInterpreter()
        await interp.run("""
            NULL 700 'beta' <REC! 'beta' REC@
        """)
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == 700


class TestArrayOperations:
    """Test array operations."""

    @pytest.mark.asyncio
    async def test_append(self) -> None:
        """Test APPEND operation."""
        interp = StandardInterpreter()

        # Test append to array
        await interp.run("""
            [ 1 2 3 ] 4 APPEND
        """)
        assert len(interp.get_stack()) == 1
        array = interp.stack_pop()
        assert array == [1, 2, 3, 4]

        # Test append to record
        await interp.run("""
            [["a" 1] ["b" 2]] REC  ["c" 3] APPEND
        """)
        assert len(interp.get_stack()) == 1
        rec = interp.stack_pop()
        values = [rec[k] for k in ["a", "b", "c"]]
        assert values == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_reverse(self) -> None:
        """Test REVERSE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [ 1 2 3 ] REVERSE
        """)
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_unique(self) -> None:
        """Test UNIQUE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [ 1 2 3 3 2 ] UNIQUE
        """)
        assert interp.stack_pop() == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test DELETE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [ "a" "b" "c" ] 1 <DEL
        """)
        assert interp.stack_pop() == ["a", "c"]

        await interp.run("""
            [["a" 1] ["b" 2] ["c" 3]] REC  "b" <DEL
        """)
        rec = interp.stack_pop()
        assert sorted(rec.keys()) == ["a", "c"]

        await interp.run("""
            [["a" 1] ["b" 2] ["c" 3]] REC  "d" <DEL
        """)
        rec = interp.stack_pop()
        assert sorted(rec.keys()) == ["a", "b", "c"]


class TestDataStructureOperations:
    """Test operations on data structures."""

    @pytest.mark.asyncio
    async def test_keys(self) -> None:
        """Test KEYS operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b' 'c'] KEYS
        """)
        array = interp.stack_pop()
        assert array == [0, 1, 2]

        # Test with record
        await interp.run("""
            [['a' 1] ['b' 2]] REC KEYS
        """)
        array = interp.stack_pop()
        assert sorted(array) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_values(self) -> None:
        """Test VALUES operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b' 'c'] VALUES
        """)
        array = interp.stack_pop()
        assert array == ["a", "b", "c"]

        # Test with record
        await interp.run("""
            [['a' 1] ['b' 2]] REC VALUES
        """)
        array = interp.stack_pop()
        assert sorted(array) == [1, 2]

    @pytest.mark.asyncio
    async def test_length(self) -> None:
        """Test LENGTH operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b' 'c'] LENGTH
            "Howdy" LENGTH
        """)
        assert interp.stack_pop() == 5
        assert interp.stack_pop() == 3

        # Test record
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 1] ['b' 2]] REC LENGTH
        """)
        length = interp.get_stack()[0]
        assert length == 2


class TestMapAndIteration:
    """Test MAP and iteration operations."""

    @pytest.mark.asyncio
    async def test_map(self) -> None:
        """Test MAP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [1 2 3 4 5] '2 *' MAP
        """)
        array = interp.stack_pop()
        assert array == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_foreach(self) -> None:
        """Test FOREACH operation."""
        interp = StandardInterpreter()
        await interp.run("""
            0 [1 2 3 4 5] '+' FOREACH
        """)
        sum_val = interp.stack_pop()
        assert sum_val == 15

    @pytest.mark.asyncio
    async def test_select(self) -> None:
        """Test SELECT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] "2 MOD 1 ==" SELECT
        """)
        stack = interp.get_stack()
        assert stack[0] == [1, 3, 5]


class TestStringOperations:
    """Test string operations."""

    @pytest.mark.asyncio
    async def test_split(self) -> None:
        """Test SPLIT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            'Now is the time' ' ' SPLIT
        """)
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == ["Now", "is", "the", "time"]

    @pytest.mark.asyncio
    async def test_join(self) -> None:
        """Test JOIN operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ["Now" "is" "the" "time"] "--" JOIN
        """)
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == "Now--is--the--time"

    @pytest.mark.asyncio
    async def test_lowercase(self) -> None:
        """Test LOWERCASE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "HOWDY, Everyone!" LOWERCASE
        """)
        stack = interp.get_stack()
        assert stack[0] == "howdy, everyone!"

    @pytest.mark.asyncio
    async def test_strip(self) -> None:
        """Test STRIP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "  howdy  " STRIP
        """)
        stack = interp.get_stack()
        assert stack[0] == "howdy"

    @pytest.mark.asyncio
    async def test_replace(self) -> None:
        """Test REPLACE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "1-40 2-20" "-" "." REPLACE
        """)
        stack = interp.get_stack()
        assert stack[0] == "1.40 2.20"


class TestStackOperations:
    """Test stack operations."""

    @pytest.mark.asyncio
    async def test_pop(self) -> None:
        """Test POP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            1 2 3 4 5 POP
        """)
        stack = interp.get_stack()
        assert len(stack) == 4
        assert stack[-1] == 4

    @pytest.mark.asyncio
    async def test_dup(self) -> None:
        """Test DUP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            5 DUP
        """)
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 5
        assert stack[1] == 5

    @pytest.mark.asyncio
    async def test_swap(self) -> None:
        """Test SWAP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            6 8 SWAP
        """)
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 8
        assert stack[1] == 6


class TestArithmetic:
    """Test arithmetic operations."""

    @pytest.mark.asyncio
    async def test_arithmetic(self) -> None:
        """Test basic arithmetic operations."""
        interp = StandardInterpreter()
        await interp.run("""
            2 4 +
            2 4 -
            2 4 *
            2 4 /
            5 3 MOD
            2.51 ROUND
            [1 2 3] +
            [2 3 4] *
        """)
        stack = interp.get_stack()
        assert stack[0] == 6
        assert stack[1] == -2
        assert stack[2] == 8
        assert stack[3] == 0.5
        assert stack[4] == 2
        assert stack[5] == 3
        assert stack[6] == 6
        assert stack[7] == 24


class TestComparison:
    """Test comparison operations."""

    @pytest.mark.asyncio
    async def test_comparison(self) -> None:
        """Test comparison operations."""
        interp = StandardInterpreter()
        await interp.run("""
            2 4 ==
            2 4 !=
            2 4 <
            2 4 <=
            2 4 >
            2 4 >=
        """)
        stack = interp.get_stack()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is True
        assert stack[3] is True
        assert stack[4] is False
        assert stack[5] is False


class TestLogic:
    """Test logical operations."""

    @pytest.mark.asyncio
    async def test_logic(self) -> None:
        """Test logical operations."""
        interp = StandardInterpreter()
        await interp.run("""
            FALSE FALSE OR
            [FALSE FALSE TRUE FALSE] OR
            FALSE TRUE AND
            [FALSE FALSE TRUE FALSE] AND
            FALSE NOT
        """)
        stack = interp.get_stack()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is False
        assert stack[3] is False
        assert stack[4] is True


class TestAdvancedMapAndIteration:
    """Test advanced MAP and iteration features."""

    @pytest.mark.asyncio
    async def test_map_over_records(self) -> None:
        """Test MAP over records."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        records = make_records()
        by_key = {rec["key"]: rec for rec in records}
        interp.stack_push(by_key)

        await interp.run("""
            "'status' REC@" MAP
        """)
        record = interp.stack_pop()
        assert record[100] == "OPEN"
        assert record[102] == "IN PROGRESS"
        assert record[106] == "CLOSED"

    @pytest.mark.asyncio
    async def test_map_in_module(self) -> None:
        """Test MAP in module."""
        interp = StandardInterpreter()
        await interp.run("""
            {my-module
              : DOUBLE   2 *;
              : RUN   [1 2 3 4 5] "DOUBLE" MAP;
            }
            {my-module RUN}
        """)
        array = interp.stack_pop()
        assert array == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_map_depth(self) -> None:
        """Test MAP with depth option."""
        interp = StandardInterpreter()
        await interp.run("""
            : k1-REC   [
              ["l1"  [["m"  2]] REC]
              ["l2"  [["m"  3]] REC]
            ] REC;

            : k2-REC   [
              ["l1"  [["m"  3]] REC]
              ["l2"  [["m"  4]] REC]
            ] REC;

            : DEEP-RECORD [
              ["k1"  k1-REC]
              ["k2"  k2-REC]
            ] REC;

            DEEP-RECORD "2 *" [.depth 2] ~> MAP
        """)
        record = interp.stack_pop()
        assert record == {
            "k1": {"l1": {"m": 4}, "l2": {"m": 6}},
            "k2": {"l1": {"m": 6}, "l2": {"m": 8}},
        }

    @pytest.mark.asyncio
    async def test_map_depth_over_array(self) -> None:
        """Test MAP depth over array."""
        interp = StandardInterpreter()
        await interp.run("""
            : DEEP-LIST [ [ [[["m"  2]] REC [["m"  3]] REC] ] [ [[["m"  3]] REC [["m"  4]] REC] ] ];

            DEEP-LIST "2 *" [.depth 3] ~> MAP
        """)
        array = interp.stack_pop()
        assert array == [[[{"m": 4}, {"m": 6}]], [[{"m": 6}, {"m": 8}]]]

    @pytest.mark.asyncio
    async def test_map_depth_over_array_of_maps(self) -> None:
        """Test MAP depth over array of maps."""
        interp = StandardInterpreter()
        await interp.run("""
            : DEEP-LIST [ [ [2 3] ] [ [3 4] ] ];

            DEEP-LIST "2 *" [.depth 2] ~> MAP
        """)
        array = interp.stack_pop()
        assert array == [[[4, 6]], [[6, 8]]]

    @pytest.mark.asyncio
    async def test_map_depth_with_error(self) -> None:
        """Test MAP depth with error handling."""
        interp = StandardInterpreter()
        await interp.run("""
            : k1-REC   [
              ["l1"  [["m"  2]] REC]
              ["l2"  [["m"  3]] REC]
            ] REC;

            : k2-REC   [
              ["l1"  [["m"  'GARBAGE']] REC]
              ["l2"  [["m"  4]] REC]
            ] REC;

            : DEEP-RECORD [
              ["k1"  k1-REC]
              ["k2"  k2-REC]
            ] REC;

            DEEP-RECORD ">STR INTERPRET" [.depth 2 .push_error TRUE] ~> MAP
        """)
        errors = interp.stack_pop()
        record = interp.stack_pop()

        assert record == {
            "k1": {"l1": {"m": 2}, "l2": {"m": 3}},
            "k2": {"l1": {"m": None}, "l2": {"m": 4}},
        }
        assert errors[0] is None
        assert errors[1] is None
        assert errors[2] is not None
        assert errors[3] is None

    @pytest.mark.asyncio
    async def test_map_with_key(self) -> None:
        """Test MAP with key option."""
        interp = StandardInterpreter()
        await interp.run("""
            [1 2 3 4 5] '+ 2 *' [.with_key TRUE] ~> MAP
        """)
        array = interp.stack_pop()
        assert array == [2, 6, 10, 14, 18]

    @pytest.mark.asyncio
    async def test_foreach_over_records(self) -> None:
        """Test FOREACH over records."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        records = make_records()
        by_key = {rec["key"]: rec for rec in records}
        interp.stack_push(by_key)

        await interp.run("""
            "" SWAP "'status' REC@ CONCAT" FOREACH
        """)
        string = interp.stack_pop()
        assert string == "OPENOPENIN PROGRESSCLOSEDIN PROGRESSOPENCLOSED"

    @pytest.mark.asyncio
    async def test_foreach_with_key(self) -> None:
        """Test FOREACH with key option."""
        interp = StandardInterpreter()
        await interp.run("""
            0 [1 2 3 4 5] '+ +' [.with_key TRUE] ~> FOREACH
        """)
        sum_val = interp.stack_pop()
        assert sum_val == 25

    @pytest.mark.asyncio
    async def test_foreach_to_errors(self) -> None:
        """Test FOREACH with error handling."""
        interp = StandardInterpreter()
        await interp.run("""
            ['2' '3' 'GARBAGE' '+'] 'INTERPRET' [.push_error TRUE] ~> FOREACH
        """)
        errors = interp.stack_pop()
        assert errors[0] is None
        assert errors[1] is None
        assert errors[2] is not None
        assert errors[3] is None
        res = interp.stack_pop()
        assert res == 5


class TestGroupingAndRelabeling:
    """Test grouping and relabeling operations."""

    @pytest.mark.asyncio
    async def test_relabel_array(self) -> None:
        """Test RELABEL operation on array."""
        interp = StandardInterpreter()
        await interp.run("""
            [ "a" "b" "c" ] [0 2] [25 23] RELABEL
        """)
        assert len(interp.get_stack()) == 1
        array = interp.stack_pop()
        assert array == ["c", "a"]

    @pytest.mark.asyncio
    async def test_relabel_record(self) -> None:
        """Test RELABEL operation on record."""
        interp = StandardInterpreter()
        await interp.run("""
            [["a" 1] ["b" 2] ["c" 3]] REC  ["a" "c"] ["alpha" "gamma"] RELABEL
        """)
        assert len(interp.get_stack()) == 1
        rec = interp.stack_pop()
        assert sorted(rec.keys()) == ["alpha", "gamma"]
        assert [rec[k] for k in ["alpha", "gamma"]] == [1, 3]

    @pytest.mark.asyncio
    async def test_by_field(self) -> None:
        """Test BY_FIELD operation."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        interp.stack_push(make_records())
        await interp.run("'key' BY_FIELD")
        grouped = interp.stack_pop()
        assert grouped[104]["status"] == "IN PROGRESS"

    @pytest.mark.asyncio
    async def test_by_field_with_nulls(self) -> None:
        """Test BY_FIELD with null values."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        records = make_records()
        records.extend([None, None])
        interp.stack_push(records)
        await interp.run("'key' BY_FIELD")
        grouped = interp.stack_pop()
        assert grouped[104]["status"] == "IN PROGRESS"

    @pytest.mark.asyncio
    async def test_group_by_field_array(self) -> None:
        """Test GROUP_BY_FIELD operation on array."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        interp.stack_push(make_records())
        await interp.run("'assignee' GROUP_BY_FIELD")
        grouped = interp.stack_pop()
        assert sorted(grouped.keys()) == ["user1", "user2"]
        assert len(grouped["user1"]) == 4
        assert len(grouped["user2"]) == 3

    @pytest.mark.asyncio
    async def test_group_by_field_record(self) -> None:
        """Test GROUP_BY_FIELD operation on record."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        records = make_records()
        by_key = {rec["key"]: rec for rec in records}
        interp.stack_push(by_key)

        await interp.run("'assignee' GROUP_BY_FIELD")
        grouped_rec = interp.stack_pop()
        assert sorted(grouped_rec.keys()) == ["user1", "user2"]
        assert len(grouped_rec["user1"]) == 4
        assert len(grouped_rec["user2"]) == 3

    @pytest.mark.asyncio
    async def test_group_by_field_list_valued(self) -> None:
        """Test GROUP_BY_FIELD on list-valued field."""
        interp = StandardInterpreter()
        interp.stack_push([
            {"id": 1, "attrs": ["blue", "important"]},
            {"id": 2, "attrs": ["red"]},
        ])
        await interp.run("'attrs' GROUP_BY_FIELD")
        grouped_rec = interp.stack_pop()
        assert grouped_rec["blue"][0]["id"] == 1
        assert grouped_rec["important"][0]["id"] == 1
        assert grouped_rec["red"][0]["id"] == 2

    @pytest.mark.asyncio
    async def test_group_by(self) -> None:
        """Test GROUP_BY operation."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        interp.stack_push(make_records())
        await interp.run("""
            "'assignee' REC@" GROUP_BY
        """)
        grouped = interp.stack_pop()
        assert sorted(grouped.keys()) == ["user1", "user2"]
        assert len(grouped["user1"]) == 4
        assert len(grouped["user2"]) == 3

    @pytest.mark.asyncio
    async def test_group_by_with_key(self) -> None:
        """Test GROUP_BY with key option."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        interp.stack_push(make_records())
        await interp.run("""
            ['key' 'val'] VARIABLES
            "val ! key ! key @ 3 MOD" [.with_key TRUE] ~> GROUP_BY
        """)
        grouped = interp.stack_pop()
        assert sorted(grouped.keys()) == ["0", "1", "2"]
        assert len(grouped["0"]) == 3
        assert len(grouped["1"]) == 2
        assert len(grouped["2"]) == 2

    @pytest.mark.asyncio
    async def test_groups_of_array(self) -> None:
        """Test GROUPS_OF on array."""
        interp = StandardInterpreter()
        await interp.run("""
            [1 2 3 4 5 6 7 8] 3 GROUPS_OF
        """)
        groups = interp.stack_pop()
        assert groups[0] == [1, 2, 3]
        assert groups[1] == [4, 5, 6]
        assert groups[2] == [7, 8]

    @pytest.mark.asyncio
    async def test_groups_of_record_direct(self) -> None:
        """Test GROUPS_OF on record."""
        interp = StandardInterpreter()
        await interp.run("""
            [
              ['a' 1]
              ['b' 2]
              ['c' 3]
              ['d' 4]
              ['e' 5]
              ['f' 6]
              ['g' 7]
              ['h' 8]
            ] REC 3 GROUPS_OF
        """)
        groups = interp.stack_pop()
        assert groups[0] == {"a": 1, "b": 2, "c": 3}
        assert groups[1] == {"d": 4, "e": 5, "f": 6}
        assert groups[2] == {"g": 7, "h": 8}

    @pytest.mark.asyncio
    async def test_groups_of_using_record(self) -> None:
        """Test GROUPS_OF using record."""
        def make_records():
            return [
                {"key": 100, "assignee": "user1", "status": "OPEN"},
                {"key": 101, "assignee": "user1", "status": "OPEN"},
                {"key": 102, "assignee": "user1", "status": "IN PROGRESS"},
                {"key": 103, "assignee": "user1", "status": "CLOSED"},
                {"key": 104, "assignee": "user2", "status": "IN PROGRESS"},
                {"key": 105, "assignee": "user2", "status": "OPEN"},
                {"key": 106, "assignee": "user2", "status": "CLOSED"},
            ]

        interp = StandardInterpreter()
        records = make_records()
        by_key = {rec["key"]: rec for rec in records}
        interp.stack_push(by_key)

        await interp.run("""
            3 GROUPS_OF
        """)
        recs = interp.stack_pop()
        assert len(recs[0].keys()) == 3
        assert len(recs[1].keys()) == 3
        assert len(recs[2].keys()) == 1

    @pytest.mark.asyncio
    async def test_index(self) -> None:
        """Test INDEX operation."""
        interp = StandardInterpreter()
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
    async def test_invert_keys(self) -> None:
        """Test INVERT_KEYS operation."""
        def make_status_to_manager_to_ids():
            return {
                "open": {
                    "manager1": [101, 102],
                    "manager2": [103],
                },
                "blocked": {
                    "manager3": [104],
                },
                "closed": {
                    "manager1": [10, 11],
                    "manager2": [12, 13],
                },
            }

        interp = StandardInterpreter()
        status_to_manager_to_ids = make_status_to_manager_to_ids()
        interp.stack_push(status_to_manager_to_ids)
        await interp.run("INVERT_KEYS")
        res = interp.stack_pop()
        expected = {
            "manager1": {
                "open": [101, 102],
                "closed": [10, 11],
            },
            "manager2": {
                "open": [103],
                "closed": [12, 13],
            },
            "manager3": {
                "blocked": [104],
            },
        }
        assert res == expected


class TestAdvancedArrayOperations:
    """Test advanced array operations."""

    @pytest.mark.asyncio
    async def test_zip_arrays(self) -> None:
        """Test ZIP operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b'] [1 2] ZIP
        """)
        array = interp.stack_pop()
        assert array[0] == ["a", 1]
        assert array[1] == ["b", 2]

    @pytest.mark.asyncio
    async def test_zip_records(self) -> None:
        """Test ZIP operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 100] ['b' 200] ['z' 300]] REC [['a' 'Hi'] ['b' 'Bye'] ['c' '?']] REC ZIP
        """)
        record = interp.stack_pop()
        assert sorted(record.keys()) == ["a", "b", "z"]
        assert record["a"] == [100, "Hi"]
        assert record["b"] == [200, "Bye"]
        assert record["z"] == [300, None]

    @pytest.mark.asyncio
    async def test_zip_with_arrays(self) -> None:
        """Test ZIP_WITH operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            [10 20] [1 2] "+" ZIP_WITH
        """)
        array = interp.stack_pop()
        assert array[0] == 11
        assert array[1] == 22

    @pytest.mark.asyncio
    async def test_zip_with_records(self) -> None:
        """Test ZIP_WITH operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 1] ['b' 2]] REC [['a' 10] ['b' 20]] REC "+" ZIP_WITH
        """)
        record = interp.stack_pop()
        assert sorted(record.keys()) == ["a", "b"]
        assert record["a"] == 11
        assert record["b"] == 22

    @pytest.mark.asyncio
    async def test_slice_array(self) -> None:
        """Test SLICE operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x'] VARIABLES
            ['a' 'b' 'c' 'd' 'e' 'f' 'g'] x !
            x @ 0 2 SLICE
            x @ 1 3 SLICE
            x @ 5 3 SLICE
            x @ -1 -2 SLICE
            x @ 4 -2 SLICE
            x @ 5 8 SLICE
        """)
        stack = interp.get_stack()
        assert stack[0] == ["a", "b", "c"]
        assert stack[1] == ["b", "c", "d"]
        assert stack[2] == ["f", "e", "d"]
        assert stack[3] == ["g", "f"]
        assert stack[4] == ["e", "f"]
        assert stack[5] == ["f", "g", None, None]

    @pytest.mark.asyncio
    async def test_slice_record(self) -> None:
        """Test SLICE operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x'] VARIABLES
            [['a' 1] ['b' 2] ['c' 3]] REC x !
            x @ 0 1 SLICE
            x @ -1 -2 SLICE
            x @ 5 7 SLICE
        """)
        stack = interp.get_stack()
        assert sorted(stack[0].keys()) == ["a", "b"]
        assert sorted(stack[1].keys()) == ["b", "c"]
        assert stack[2] == {}

    @pytest.mark.asyncio
    async def test_difference_array(self) -> None:
        """Test DIFFERENCE operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            ['a' 'b' 'c'] x !
            ['a' 'c' 'd'] y !
            x @ y @ DIFFERENCE
            y @ x @ DIFFERENCE
        """)
        stack = interp.get_stack()
        assert stack[0] == ["b"]
        assert stack[1] == ["d"]

    @pytest.mark.asyncio
    async def test_difference_record(self) -> None:
        """Test DIFFERENCE operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            [['a' 1] ['b' 2] ['c' 3]] REC x !
            [['a' 20] ['c' 40] ['d' 10]] REC y !
            x @ y @ DIFFERENCE
            y @ x @ DIFFERENCE
        """)
        stack = interp.get_stack()
        assert list(stack[0].keys()) == ["b"]
        assert list(stack[0].values()) == [2]
        assert list(stack[1].keys()) == ["d"]
        assert list(stack[1].values()) == [10]

    @pytest.mark.asyncio
    async def test_intersection_array(self) -> None:
        """Test INTERSECTION operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            ['a' 'b' 'c'] x !
            ['a' 'c' 'd'] y !
            x @ y @ INTERSECTION
        """)
        stack = interp.get_stack()
        assert sorted(stack[0]) == ["a", "c"]

    @pytest.mark.asyncio
    async def test_intersection_record(self) -> None:
        """Test INTERSECTION operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            [['a' 1] ['b' 2] ['f' 3]] REC x !
            [['a' 20] ['c' 40] ['d' 10]] REC y !
            x @ y @ INTERSECTION
        """)
        stack = interp.get_stack()
        assert list(stack[0].keys()) == ["a"]
        assert list(stack[0].values()) == [1]

    @pytest.mark.asyncio
    async def test_union_array(self) -> None:
        """Test UNION operation on arrays."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            ['a' 'b' 'c'] x !
            ['a' 'c' 'd'] y !
            x @ y @ UNION
        """)
        stack = interp.get_stack()
        assert sorted(stack[0]) == ["a", "b", "c", "d"]

    @pytest.mark.asyncio
    async def test_union_record(self) -> None:
        """Test UNION operation on records."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x' 'y'] VARIABLES
            [['a' 1] ['b' 2] ['f' 3]] REC x !
            [['a' 20] ['c' 40] ['d' 10]] REC y !
            x @ y @ UNION
        """)
        stack = interp.get_stack()
        assert sorted(stack[0].keys()) == ["a", "b", "c", "d", "f"]
        assert sorted(stack[0].values()) == [1, 2, 3, 10, 40]

    @pytest.mark.asyncio
    async def test_select_record(self) -> None:
        """Test SELECT on records."""
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC  "2 MOD 0 ==" SELECT
        """)
        stack = interp.get_stack()
        assert list(stack[0].keys()) == ["b"]
        assert list(stack[0].values()) == [2]

    @pytest.mark.asyncio
    async def test_select_with_key(self) -> None:
        """Test SELECT with key option."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] "+ 3 MOD 1 ==" [.with_key TRUE] ~> SELECT
        """)
        stack = interp.get_stack()
        assert stack[0] == [2, 5]

    @pytest.mark.asyncio
    async def test_take(self) -> None:
        """Test TAKE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] 3 TAKE
        """)
        stack = interp.get_stack()
        assert stack[0] == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_take_with_rest(self) -> None:
        """Test TAKE with rest option."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] 3 [.push_rest TRUE] ~> TAKE
        """)
        stack = interp.get_stack()
        assert stack[0] == [0, 1, 2]
        assert stack[1] == [3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_drop(self) -> None:
        """Test DROP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] 4 DROP
        """)
        stack = interp.get_stack()
        assert stack[0] == [4, 5, 6]

    @pytest.mark.asyncio
    async def test_rotate(self) -> None:
        """Test ROTATE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b' 'c' 'd'] ROTATE
            ['b'] ROTATE
            [] ROTATE
        """)
        stack = interp.get_stack()
        assert stack[0] == ["d", "a", "b", "c"]
        assert stack[1] == ["b"]
        assert stack[2] == []

    @pytest.mark.asyncio
    async def test_array_predicate(self) -> None:
        """Test ARRAY? predicate."""
        interp = StandardInterpreter()
        await interp.run("""
            ['a' 'b' 'c' 'd'] ARRAY?
            'b' ARRAY?
            0 ARRAY?
        """)
        stack = interp.get_stack()
        assert stack[0] is True
        assert stack[1] is False
        assert stack[2] is False

    @pytest.mark.asyncio
    async def test_shuffle(self) -> None:
        """Test SHUFFLE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] SHUFFLE
        """)
        stack = interp.get_stack()
        assert len(stack[0]) == 7

    @pytest.mark.asyncio
    async def test_sort(self) -> None:
        """Test SORT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [2 8 1 4 7 3] SORT
        """)
        stack = interp.get_stack()
        assert stack[0] == [1, 2, 3, 4, 7, 8]

    @pytest.mark.asyncio
    async def test_sort_with_null(self) -> None:
        """Test SORT with null values."""
        interp = StandardInterpreter()
        await interp.run("""
            [2 8 1 NULL 4 7 NULL 3] SORT
        """)
        stack = interp.get_stack()
        assert stack[0] == [1, 2, 3, 4, 7, 8, None, None]

    @pytest.mark.asyncio
    async def test_sort_with_forthic(self) -> None:
        """Test SORT with forthic comparator."""
        interp = StandardInterpreter()
        await interp.run("""
            [2 8 1 4 7 3] [.comparator "-1 *"] ~> SORT
        """)
        stack = interp.get_stack()
        assert stack[0] == [8, 7, 4, 3, 2, 1]

    @pytest.mark.asyncio
    async def test_nth(self) -> None:
        """Test NTH operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ["x"] VARIABLES
            [0 1 2 3 4 5 6] x !
            x @ 0 NTH
            x @ 5 NTH
            x @ 55 NTH
        """)
        stack = interp.get_stack()
        assert stack[0] == 0
        assert stack[1] == 5
        assert stack[2] is None

    @pytest.mark.asyncio
    async def test_last(self) -> None:
        """Test LAST operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2 3 4 5 6] LAST
        """)
        stack = interp.get_stack()
        assert stack[0] == 6

    @pytest.mark.asyncio
    async def test_unpack_array(self) -> None:
        """Test UNPACK operation on array."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 1 2] UNPACK
        """)
        stack = interp.get_stack()
        assert stack[0] == 0
        assert stack[1] == 1
        assert stack[2] == 2

    @pytest.mark.asyncio
    async def test_unpack_record(self) -> None:
        """Test UNPACK operation on record."""
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC UNPACK
        """)
        stack = interp.get_stack()
        assert stack[0] == 1
        assert stack[1] == 2
        assert stack[2] == 3

    @pytest.mark.asyncio
    async def test_flatten(self) -> None:
        """Test FLATTEN operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 [1 2 [3 [4]] ]] FLATTEN
        """)
        stack = interp.get_stack()
        assert stack[0] == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_flatten_depth(self) -> None:
        """Test FLATTEN with depth option."""
        interp = StandardInterpreter()
        await interp.run("""
            [ [ [0 1] [2 3] ]
              [ [4 5]       ] ] [.depth 1] ~> FLATTEN
        """)
        array = interp.get_stack()[-1]
        assert array == [[0, 1], [2, 3], [4, 5]]

        await interp.run("""
            [ [ [0 1] [2 3] ]
              [ [4 5]       ] ] [.depth 0] ~> FLATTEN
        """)
        array = interp.get_stack()[-1]
        assert array == [[[0, 1], [2, 3]], [[4, 5]]]

        await interp.run("""
            [ [ [0 1] [2 3] ]
              [ [4 5]       ] ] [.depth 2] ~> FLATTEN
        """)
        array = interp.get_stack()[-1]
        assert array == [0, 1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_key_of_array(self) -> None:
        """Test KEY_OF operation on array."""
        interp = StandardInterpreter()
        await interp.run("""
            ['x'] VARIABLES
            ['a' 'b' 'c' 'd'] x !
            x @  'c' KEY_OF
            x @  'z' KEY_OF
        """)
        stack = interp.get_stack()
        assert stack[0] == 2
        assert stack[1] is None

    @pytest.mark.asyncio
    async def test_key_of_record(self) -> None:
        """Test KEY_OF operation on record."""
        interp = StandardInterpreter()
        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC  2 KEY_OF
        """)
        stack = interp.get_stack()
        assert stack[0] == "b"

    @pytest.mark.asyncio
    async def test_reduce(self) -> None:
        """Test REDUCE operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [1 2 3 4 5] 10 "+" REDUCE
        """)
        assert interp.stack_pop() == 25

        await interp.run("""
            [['a' 1] ['b' 2] ['c' 3]] REC  20 "+" REDUCE
        """)
        assert interp.stack_pop() == 26


class TestSpecialAndMiscOperations:
    """Test special characters and miscellaneous operations."""

    @pytest.mark.asyncio
    async def test_special_chars(self) -> None:
        """Test special character constants."""
        interp = StandardInterpreter()
        await interp.run("""
            /R /N /T
        """)
        stack = interp.get_stack()
        assert stack[0] == "\r"
        assert stack[1] == "\n"
        assert stack[2] == "\t"

    @pytest.mark.asyncio
    async def test_ascii(self) -> None:
        """Test ASCII operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "\u201cHOWDY, Everyone!\u201d" ASCII
        """)
        stack = interp.get_stack()
        assert stack[0] == "HOWDY, Everyone!"

    @pytest.mark.asyncio
    async def test_re_match(self) -> None:
        """Test RE_MATCH operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "123message456" "\\d{3}.*\\d{3}" RE_MATCH
        """)
        stack = interp.get_stack()
        assert stack[0] is not None

    @pytest.mark.asyncio
    async def test_re_match_group(self) -> None:
        """Test RE_MATCH_GROUP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "123message456" "\\d{3}(.*)\\d{3}" RE_MATCH 1 RE_MATCH_GROUP
        """)
        stack = interp.get_stack()
        assert stack[0] == "message"

    @pytest.mark.asyncio
    async def test_re_match_all(self) -> None:
        """Test RE_MATCH_ALL operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "mr-android ios my-android web test-web" ".*?(android|ios|web|seo)" RE_MATCH_ALL
        """)
        stack = interp.get_stack()
        assert stack[0] == ["android", "ios", "android", "web", "web"]

    @pytest.mark.asyncio
    async def test_default(self) -> None:
        """Test DEFAULT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            NULL 22.4 DEFAULT
            0 22.4 DEFAULT
            "" "Howdy" DEFAULT
        """)
        stack = interp.get_stack()
        assert stack[0] == 22.4
        assert stack[1] == 0
        assert stack[2] == "Howdy"

    @pytest.mark.asyncio
    async def test_star_default(self) -> None:
        """Test *DEFAULT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            NULL "3.1 5 +" *DEFAULT
            0 "22.4" *DEFAULT
            "" "['Howdy, ' 'Everyone!'] CONCAT" *DEFAULT
        """)
        stack = interp.get_stack()
        assert abs(stack[0] - 8.1) < 0.01
        assert stack[1] == 0
        assert stack[2] == "Howdy, Everyone!"

    @pytest.mark.asyncio
    async def test_repeat(self) -> None:
        """Test <REPEAT operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [0 "1 +" 6 <REPEAT]
        """)
        stack = interp.get_stack()
        assert stack[0] == [0, 1, 2, 3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_to_fixed(self) -> None:
        """Test >FIXED converter."""
        interp = StandardInterpreter()
        await interp.run("""
            22 7 / 2 >FIXED
        """)
        stack = interp.get_stack()
        assert stack[0] == "3.14"

    @pytest.mark.asyncio
    async def test_to_json(self) -> None:
        """Test >JSON converter."""
        import json
        interp = StandardInterpreter()
        await interp.run("""
            [["a" 1] ["b" 2]] REC >JSON
        """)
        result = interp.stack_pop()
        assert json.loads(result) == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_json_to(self) -> None:
        """Test JSON> converter."""
        interp = StandardInterpreter()
        await interp.run("""
            '{"a": 1, "b": 2}' JSON>
        """)
        stack = interp.get_stack()
        assert sorted(stack[0].keys()) == ["a", "b"]
        assert stack[0]["a"] == 1
        assert stack[0]["b"] == 2

    @pytest.mark.asyncio
    async def test_date_to_str(self) -> None:
        """Test DATE>STR operation."""
        interp = StandardInterpreter()
        await interp.run("""2021-01-01 DATE>STR""")
        assert interp.stack_pop() == "2021-01-01"

    @pytest.mark.asyncio
    async def test_pipe_rec_at(self) -> None:
        """Test |REC@| operation."""
        interp = StandardInterpreter()
        interp.stack_push([{"a": 1}, {"a": 2}, {"a": 3}])
        await interp.run("""'a' |REC@""")
        assert interp.stack_pop() == [1, 2, 3]

        interp.stack_push([{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 3}}])
        await interp.run("""['a' 'b'] |REC@""")
        assert interp.stack_pop() == [1, 2, 3]


class TestLogicAndComparison:
    """Test logical and comparison operations."""

    @pytest.mark.asyncio
    async def test_in_operation(self) -> None:
        """Test IN operation."""
        interp = StandardInterpreter()
        await interp.run("""
            "alpha" ["beta" "gamma"] IN
            "alpha" ["beta" "gamma" "alpha"] IN
        """)
        stack = interp.get_stack()
        assert stack[0] is False
        assert stack[1] is True

    @pytest.mark.asyncio
    async def test_any_operation(self) -> None:
        """Test ANY operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ["alpha" "beta"] ["beta" "gamma"] ANY
            ["delta" "beta"] ["gamma" "alpha"] ANY
            ["alpha" "beta"] [] ANY
        """)
        stack = interp.get_stack()
        assert stack[0] is True
        assert stack[1] is False
        assert stack[2] is True

    @pytest.mark.asyncio
    async def test_all_operation(self) -> None:
        """Test ALL operation."""
        interp = StandardInterpreter()
        await interp.run("""
            ["alpha" "beta"] ["beta" "gamma"] ALL
            ["delta" "beta"] ["beta"] ALL
            ["alpha" "beta"] [] ALL
        """)
        stack = interp.get_stack()
        assert stack[0] is False
        assert stack[1] is True
        assert stack[2] is True


class TestMathConverters:
    """Test math type converters."""

    @pytest.mark.asyncio
    async def test_math_converters(self) -> None:
        """Test math converter operations."""
        interp = StandardInterpreter()
        await interp.run("""
            NULL >BOOL
            0 >BOOL
            1 >BOOL
            "" >BOOL
            "Hi" >BOOL
            "3" >INT
            4 >INT
            4.6 >INT
            "1.2" >FLOAT
            2 >FLOAT
        """)
        stack = interp.get_stack()
        assert stack[0] is False
        assert stack[1] is False
        assert stack[2] is True
        assert stack[3] is False
        assert stack[4] is True
        assert stack[5] == 3
        assert stack[6] == 4
        assert stack[7] == 4
        assert stack[8] == 1.2
        assert stack[9] == 2.0


class TestMaxMinMean:
    """Test MAX, MIN, and MEAN operations."""

    @pytest.mark.asyncio
    async def test_max_two_numbers(self) -> None:
        """Test MAX of two numbers."""
        interp = StandardInterpreter()
        interp.stack_push(4)
        interp.stack_push(18)
        await interp.run("MAX")
        assert interp.stack_pop() == 18

    @pytest.mark.asyncio
    async def test_max_array(self) -> None:
        """Test MAX of an array."""
        interp = StandardInterpreter()
        interp.stack_push([14, 8, 55, 4, 5])
        await interp.run("MAX")
        assert interp.stack_pop() == 55

    @pytest.mark.asyncio
    async def test_min_two_numbers(self) -> None:
        """Test MIN of two numbers."""
        interp = StandardInterpreter()
        interp.stack_push(4)
        interp.stack_push(18)
        await interp.run("MIN")
        assert interp.stack_pop() == 4

    @pytest.mark.asyncio
    async def test_min_array(self) -> None:
        """Test MIN of an array."""
        interp = StandardInterpreter()
        interp.stack_push([14, 8, 55, 4, 5])
        await interp.run("MIN")
        assert interp.stack_pop() == 4

    @pytest.mark.asyncio
    async def test_mean_numbers(self) -> None:
        """Test MEAN of numbers."""
        interp = StandardInterpreter()
        await interp.run("[1 2 3 4 5] MEAN")
        assert interp.stack_pop() == 3

        await interp.run("[4] MEAN")
        assert interp.stack_pop() == 4

        await interp.run("[] MEAN")
        assert interp.stack_pop() == 0

        await interp.run("NULL MEAN")
        assert interp.stack_pop() == 0

    @pytest.mark.asyncio
    async def test_mean_letters(self) -> None:
        """Test MEAN of letters."""
        interp = StandardInterpreter()
        interp.stack_push(["a", "a", "b", "c"])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 0.5, "b": 0.25, "c": 0.25}

    @pytest.mark.asyncio
    async def test_mean_with_nulls(self) -> None:
        """Test MEAN with null values."""
        interp = StandardInterpreter()
        interp.stack_push([1, 2, 3, None, 4, None, 5])
        await interp.run("MEAN")
        assert interp.stack_pop() == 3

    @pytest.mark.asyncio
    async def test_mean_letters_with_nulls(self) -> None:
        """Test MEAN of letters with nulls."""
        interp = StandardInterpreter()
        interp.stack_push(["a", "a", None, "b", None, "c"])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 0.5, "b": 0.25, "c": 0.25}

    @pytest.mark.asyncio
    async def test_mean_objects(self) -> None:
        """Test MEAN of objects."""
        interp = StandardInterpreter()
        interp.stack_push([
            {"a": 1, "b": 0},
            {"a": 2, "b": 0},
            {"a": 3, "b": 0},
        ])
        await interp.run("MEAN")
        assert interp.stack_pop() == {"a": 2, "b": 0}

    @pytest.mark.asyncio
    async def test_mean_objects_mixed(self) -> None:
        """Test MEAN of objects with mixed types."""
        interp = StandardInterpreter()
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

    @pytest.mark.asyncio
    async def test_divide(self) -> None:
        """Test DIVIDE operation."""
        interp = StandardInterpreter()
        interp.stack_push(10)
        interp.stack_push(2)
        await interp.run("DIVIDE")
        assert interp.stack_pop() == 5


class TestDateTimeOperations:
    """Test date and time operations."""

    @pytest.mark.asyncio
    async def test_add_days(self) -> None:
        """Test ADD-DAYS operation."""
        interp = StandardInterpreter()
        await interp.run("""
            2020-10-21 12 ADD-DAYS
        """)
        stack = interp.get_stack()
        date = stack[0]
        assert date.year == 2020
        assert date.month == 11
        assert date.day == 2

    @pytest.mark.asyncio
    async def test_subtract_dates(self) -> None:
        """Test SUBTRACT-DATES operation."""
        interp = StandardInterpreter()
        await interp.run("""
            2020-10-21 2020-11-02 SUBTRACT-DATES
        """)
        stack = interp.get_stack()
        assert stack[0] == -12


class TestProfiling:
    """Test profiling operations."""

    @pytest.mark.asyncio
    async def test_profiling(self) -> None:
        """Test PROFILE operations."""
        interp = StandardInterpreter()
        await interp.run("""
            PROFILE-START
            [1 "1 +" 6 <REPEAT]
            PROFILE-END POP
            PROFILE-DATA
        """)
        stack = interp.get_stack()
        profile_data = stack[-1]
        assert profile_data["word_counts"][0]["word"] == "1"
        assert profile_data["word_counts"][0]["count"] == 7


class TestParallelOperations:
    """Test parallel operations."""

    @pytest.mark.asyncio
    async def test_parallel_map(self) -> None:
        """Test parallel MAP operation."""
        interp = StandardInterpreter()
        await interp.run("""
            [ 1 2 3 4 5 ] "DUP *" [.interps 2] ~> MAP
        """)
        assert interp.stack_pop() == [1, 4, 9, 16, 25]

    @pytest.mark.asyncio
    async def test_parallel_map_over_record(self) -> None:
        """Test parallel MAP over record."""
        interp = StandardInterpreter()
        await interp.run("""
            [
              ['a' 1]
              ['b' 2]
              ['c' 3]
              ['d' 4]
            ] REC "3 *" [.interps 2] ~> MAP
        """)
        assert interp.stack_pop() == {"a": 3, "b": 6, "c": 9, "d": 12}


class TestErrors:
    """Test error conditions."""

    @pytest.mark.asyncio
    async def test_unknown_word(self) -> None:
        """Test unknown word error."""
        interp = StandardInterpreter()
        with pytest.raises(UnknownWordError) as exc_info:
            await interp.run("GARBAGE")

        assert exc_info.value.word == "GARBAGE"

    @pytest.mark.asyncio
    async def test_unknown_module(self) -> None:
        """Test unknown module error."""
        interp = StandardInterpreter()
        with pytest.raises(UnknownModuleError) as exc_info:
            await interp.run("['garbage'] USE_MODULES")

        assert exc_info.value.module_name == "garbage"

    @pytest.mark.asyncio
    async def test_stack_underflow(self) -> None:
        """Test stack underflow error."""
        interp = StandardInterpreter()
        with pytest.raises(StackUnderflowError):
            await interp.run("POP")

    @pytest.mark.asyncio
    async def test_missing_semicolon(self) -> None:
        """Test missing semicolon error."""
        interp = StandardInterpreter()
        with pytest.raises(MissingSemicolonError):
            await interp.run(": UNFINISHED   1 2 3  : NEW-WORD 'howdy' ;")

        with pytest.raises(MissingSemicolonError):
            await interp.run("@: UNFINISHED   1 2 3  : NEW-WORD 'howdy' ;")

    @pytest.mark.asyncio
    async def test_extra_semicolon_error(self) -> None:
        """Test extra semicolon error."""
        interp = StandardInterpreter()
        with pytest.raises(ExtraSemicolonError):
            await interp.run("1 2 3 ;")
