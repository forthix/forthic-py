"""Complete end-to-end integration tests for the Forthic interpreter."""

import pytest

from forthic import (
    Interpreter,
    Module,
    PushValueWord,
    StandardInterpreter,
    dup_interpreter,
)


class TestBasicExecution:
    """Test basic execution."""

    @pytest.mark.asyncio
    async def test_run_simple_string_literals(self) -> None:
        """Test running simple string literals."""
        interp = StandardInterpreter()
        await interp.run("'hello' 'world'")

        assert interp.stack_pop() == "world"
        assert interp.stack_pop() == "hello"

    @pytest.mark.asyncio
    async def test_run_numbers_as_words(self) -> None:
        """Test running numbers as words."""
        interp = StandardInterpreter()

        # Numbers need to be defined as words for this to work
        module = Module("nums")
        module.add_exportable_word(PushValueWord("1", 1))
        module.add_exportable_word(PushValueWord("2", 2))
        module.add_exportable_word(PushValueWord("3", 3))

        interp.register_module(module)
        interp.use_modules([["nums", ""]])

        await interp.run("1 2 3")

        assert interp.get_stack().get_items() == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_run_empty_code(self) -> None:
        """Test running empty code."""
        interp = StandardInterpreter()
        await interp.run("")
        assert len(interp.get_stack()) == 0


class TestWordDefinitions:
    """Test word definitions."""

    @pytest.mark.asyncio
    async def test_define_and_execute_simple_word(self) -> None:
        """Test defining and executing a simple word."""
        interp = StandardInterpreter()

        # First define a simple word that pushes a value
        await interp.run(": FIVE '5' ;")

        # Now execute it
        await interp.run("FIVE")

        assert interp.stack_pop() == "5"

    @pytest.mark.asyncio
    async def test_define_word_with_multiple_instructions(self) -> None:
        """Test defining a word with multiple instructions."""
        interp = StandardInterpreter()
        await interp.run(": THREE-STRINGS 'a' 'b' 'c' ;")

        await interp.run("THREE-STRINGS")

        assert interp.stack_pop() == "c"
        assert interp.stack_pop() == "b"
        assert interp.stack_pop() == "a"

    @pytest.mark.asyncio
    async def test_call_defined_word_multiple_times(self) -> None:
        """Test calling a defined word multiple times."""
        interp = StandardInterpreter()
        await interp.run(": HELLO 'hello' ;")

        await interp.run("HELLO HELLO")

        assert interp.stack_pop() == "hello"
        assert interp.stack_pop() == "hello"


class TestArrays:
    """Test arrays."""

    @pytest.mark.asyncio
    async def test_create_empty_array(self) -> None:
        """Test creating an empty array."""
        interp = StandardInterpreter()
        await interp.run("[ ]")

        result = interp.stack_pop()
        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_create_array_with_string_literals(self) -> None:
        """Test creating an array with string literals."""
        interp = StandardInterpreter()
        await interp.run("[ 'a' 'b' 'c' ]")

        result = interp.stack_pop()
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_nested_arrays(self) -> None:
        """Test nested arrays."""
        interp = StandardInterpreter()
        await interp.run("[ 'x' [ 'y' 'z' ] ]")

        result = interp.stack_pop()
        assert result == ["x", ["y", "z"]]


class TestComments:
    """Test comments."""

    @pytest.mark.asyncio
    async def test_ignore_comment_lines(self) -> None:
        """Test that comment lines are ignored."""
        interp = StandardInterpreter()
        await interp.run("# This is a comment\n'value'")

        assert interp.stack_pop() == "value"

    @pytest.mark.asyncio
    async def test_comments_dont_interfere_with_execution(self) -> None:
        """Test that comments don't interfere with execution."""
        interp = StandardInterpreter()
        await interp.run("'before' # comment\n'after'")

        assert interp.stack_pop() == "after"
        assert interp.stack_pop() == "before"


class TestModules:
    """Test modules."""

    @pytest.mark.asyncio
    async def test_create_and_use_module_with_custom_word(self) -> None:
        """Test creating and using a module with a custom word."""
        interp = StandardInterpreter()

        math_module = Module("math")

        async def add_word(i: Interpreter) -> None:
            b = i.stack_pop()
            a = i.stack_pop()
            i.stack_push(a + b)

        math_module.add_module_word("ADD", add_word)

        interp.register_module(math_module)
        interp.use_modules([["math", ""]])

        # Need to define numbers first
        nums_module = Module("nums")
        nums_module.add_exportable_word(PushValueWord("3", 3))
        nums_module.add_exportable_word(PushValueWord("4", 4))
        interp.register_module(nums_module)
        interp.use_modules([["nums", ""]])

        await interp.run("3 4 ADD")

        assert interp.stack_pop() == 7

    @pytest.mark.asyncio
    async def test_use_module_with_prefix(self) -> None:
        """Test using a module with a prefix."""
        interp = StandardInterpreter()

        test_module = Module("test")
        test_module.add_exportable_word(PushValueWord("VALUE", 42))

        interp.register_module(test_module)
        interp.use_modules([["test", "t"]])

        await interp.run("t.VALUE")

        assert interp.stack_pop() == 42

    @pytest.mark.asyncio
    async def test_use_modules_default_behavior(self) -> None:
        """Test use_modules default behavior (no prefix)."""
        interp = StandardInterpreter()

        test_module = Module("test")
        test_module.add_exportable_word(PushValueWord("ITEM", "value"))

        interp.register_module(test_module)
        interp.use_modules(["test"])  # Now defaults to no prefix

        await interp.run("ITEM")

        assert interp.stack_pop() == "value"


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_unknown_word_throws_error(self) -> None:
        """Test that unknown words throw an error."""
        interp = StandardInterpreter()

        with pytest.raises(Exception):
            await interp.run("UNKNOWN_WORD")

    @pytest.mark.asyncio
    async def test_missing_semicolon_throws_error(self) -> None:
        """Test that missing semicolons throw an error."""
        interp = StandardInterpreter()

        with pytest.raises(Exception) as exc_info:
            await interp.run(": INCOMPLETE")

        assert "Missing semicolon" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extra_semicolon_throws_error(self) -> None:
        """Test that extra semicolons throw an error."""
        interp = StandardInterpreter()

        with pytest.raises(Exception) as exc_info:
            await interp.run(";")

        assert "Extra semicolon" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stack_underflow_throws_error(self) -> None:
        """Test that stack underflow throws an error."""
        interp = StandardInterpreter()

        with pytest.raises(Exception):
            await interp.run("")  # Empty stack
            interp.stack_pop()    # Try to pop


class TestReset:
    """Test reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_clears_stack(self) -> None:
        """Test that reset clears the stack."""
        interp = StandardInterpreter()
        await interp.run("'a' 'b' 'c'")
        assert len(interp.get_stack()) == 3

        interp.reset()

        assert len(interp.get_stack()) == 0

    @pytest.mark.asyncio
    async def test_reset_clears_stack_and_variables(self) -> None:
        """Test that reset clears stack and variables."""
        interp = StandardInterpreter()
        await interp.run("'a' 'b' 'c'")
        assert len(interp.get_stack()) == 3

        interp.reset()

        assert len(interp.get_stack()) == 0
        # Note: reset does NOT clear word definitions, only variables and stack


class TestInterpreterDuplication:
    """Test interpreter duplication."""

    @pytest.mark.asyncio
    async def test_dup_interpreter_creates_independent_copy(self) -> None:
        """Test that dup_interpreter creates an independent copy."""
        interp = StandardInterpreter()
        await interp.run("'original'")

        dup = dup_interpreter(interp)

        await dup.run("'duplicated'")

        assert len(interp.get_stack()) == 1
        assert len(dup.get_stack()) == 2

    @pytest.mark.asyncio
    async def test_dup_interpreter_preserves_timezone(self) -> None:
        """Test that dup_interpreter preserves timezone."""
        from zoneinfo import ZoneInfo

        original = StandardInterpreter(timezone="America/New_York")
        duplicate = dup_interpreter(original)

        assert duplicate.get_timezone() == ZoneInfo("America/New_York")

    @pytest.mark.asyncio
    async def test_dup_interpreter_preserves_error_handler(self) -> None:
        """Test that dup_interpreter preserves error handler."""
        async def handler(e: Exception, i: StandardInterpreter) -> None:
            pass

        interp = StandardInterpreter()
        interp.set_error_handler(handler)

        dup = dup_interpreter(interp)

        assert dup.get_error_handler() == handler


class TestProfiling:
    """Test profiling."""

    @pytest.mark.asyncio
    async def test_profile_word_execution(self) -> None:
        """Test profiling word execution."""
        interp = StandardInterpreter()
        interp.start_profiling()

        await interp.run(": WORD1 'a' ;")
        await interp.run("WORD1 WORD1")

        interp.stop_profiling()

        histogram = interp.word_histogram()
        word1_entry = next((e for e in histogram if e.get("word") == "WORD1"), None)

        assert word1_entry is not None
        assert word1_entry.get("count") == 2

    @pytest.mark.asyncio
    async def test_timestamps_track_execution(self) -> None:
        """Test that timestamps track execution."""
        interp = StandardInterpreter()
        interp.start_profiling()
        interp.add_timestamp("CHECKPOINT")
        interp.stop_profiling()

        timestamps = interp.profile_timestamps()

        assert len(timestamps) >= 1  # At least CHECKPOINT
        labels = [t.get("label") for t in timestamps]
        assert "CHECKPOINT" in labels


class TestStringLocationTracking:
    """Test string location tracking."""

    @pytest.mark.asyncio
    async def test_string_location_is_none_initially(self) -> None:
        """Test that string_location is None initially."""
        interp = StandardInterpreter()
        assert interp.get_string_location() is None

    @pytest.mark.asyncio
    async def test_string_location_tracks_positioned_strings(self) -> None:
        """Test that string_location tracks positioned strings."""
        interp = StandardInterpreter()
        await interp.run("'test'")
        interp.stack_pop()  # This sets string_location

        location = interp.get_string_location()
        assert location is not None


class TestTripleQuotedStrings:
    """Test triple-quoted strings."""

    @pytest.mark.asyncio
    async def test_handle_triple_quoted_strings(self) -> None:
        """Test handling triple-quoted strings."""
        interp = StandardInterpreter()
        await interp.run("'''hello'''")

        assert interp.stack_pop() == "hello"

    @pytest.mark.asyncio
    async def test_triple_quoted_strings_preserve_internal_quotes(self) -> None:
        """Test that triple-quoted strings preserve internal quotes."""
        interp = StandardInterpreter()
        await interp.run('"""He said "hello" there"""')

        assert interp.stack_pop() == 'He said "hello" there'


class TestMemoDefinitions:
    """Test memo definitions."""

    @pytest.mark.asyncio
    async def test_define_and_use_memo_word(self) -> None:
        """Test defining and using a memo word."""
        interp = StandardInterpreter()
        await interp.run("@: MEMO 'value' ;")

        await interp.run("MEMO")

        assert interp.stack_pop() == "value"


class TestComplexScenarios:
    """Test complex integration scenarios."""

    @pytest.mark.asyncio
    async def test_define_word_that_uses_another_word(self) -> None:
        """Test defining a word that uses another word."""
        interp = StandardInterpreter()
        await interp.run(": GREET 'Hello' ;")
        await interp.run(": GREET-TWICE GREET GREET ;")

        await interp.run("GREET-TWICE")

        assert interp.stack_pop() == "Hello"
        assert interp.stack_pop() == "Hello"

    @pytest.mark.asyncio
    async def test_arrays_with_defined_words(self) -> None:
        """Test arrays with defined words."""
        interp = StandardInterpreter()
        await interp.run(": ONE '1' ;")
        await interp.run(": TWO '2' ;")

        await interp.run("[ ONE TWO ]")

        # Note: Words in arrays get executed during array creation
        result = interp.stack_pop()
        assert result == ["1", "2"]

    @pytest.mark.asyncio
    async def test_composed_definitions(self) -> None:
        """Test composed definitions."""
        interp = StandardInterpreter()
        # Define INNER first, then OUTER that uses INNER
        await interp.run(": INNER 'nested' ;")
        await interp.run(": OUTER INNER ;")

        await interp.run("OUTER")

        assert interp.stack_pop() == "nested"
