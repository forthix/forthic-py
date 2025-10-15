"""Tests for Core Module."""

import pytest

from forthic import IntentionalStopError, StandardInterpreter, WordOptions


class TestStackOperations:
    """Test stack manipulation words."""

    @pytest.mark.asyncio
    async def test_pop(self) -> None:
        """Test POP removes top item."""
        interp = StandardInterpreter()

        await interp.run("1 2 3 POP")
        stack = interp.get_stack().get_items()
        assert stack == [1, 2]

    @pytest.mark.asyncio
    async def test_dup(self) -> None:
        """Test DUP duplicates top item."""
        interp = StandardInterpreter()

        await interp.run("42 DUP")
        stack = interp.get_stack().get_items()
        assert stack == [42, 42]

    @pytest.mark.asyncio
    async def test_swap(self) -> None:
        """Test SWAP exchanges top two items."""
        interp = StandardInterpreter()

        await interp.run("1 2 SWAP")
        stack = interp.get_stack().get_items()
        assert stack == [2, 1]


class TestVariables:
    """Test variable operations."""

    @pytest.mark.asyncio
    async def test_bang_store_variable(self) -> None:
        """Test ! stores value in variable."""
        interp = StandardInterpreter()

        await interp.run("42 .x !")
        await interp.run(".x @")
        result = interp.stack_pop()
        assert result == 42

    @pytest.mark.asyncio
    async def test_at_retrieve_variable(self) -> None:
        """Test @ retrieves variable value."""
        interp = StandardInterpreter()

        await interp.run("100 .count !")
        await interp.run(".count @")
        result = interp.stack_pop()
        assert result == 100

    @pytest.mark.asyncio
    async def test_bang_at_store_and_return(self) -> None:
        """Test !@ stores and returns value."""
        interp = StandardInterpreter()

        await interp.run("55 .value !@")
        result = interp.stack_pop()
        assert result == 55
        # Verify it was stored
        await interp.run(".value @")
        stored = interp.stack_pop()
        assert stored == 55

    @pytest.mark.asyncio
    async def test_variables_creates_multiple(self) -> None:
        """Test VARIABLES creates multiple variables."""
        interp = StandardInterpreter()

        await interp.run("[.a .b .c] VARIABLES")
        await interp.run("1 .a ! 2 .b ! 3 .c !")
        await interp.run(".a @ .b @ .c @")
        stack = interp.get_stack().get_items()
        assert stack == [1, 2, 3]


class TestControlFlow:
    """Test control flow words."""

    @pytest.mark.asyncio
    async def test_identity(self) -> None:
        """Test IDENTITY does nothing."""
        interp = StandardInterpreter()

        await interp.run("1 2 IDENTITY")
        stack = interp.get_stack().get_items()
        assert stack == [1, 2]

    @pytest.mark.asyncio
    async def test_nop(self) -> None:
        """Test NOP does nothing."""
        interp = StandardInterpreter()

        await interp.run("3 4 NOP")
        stack = interp.get_stack().get_items()
        assert stack == [3, 4]

    @pytest.mark.asyncio
    async def test_null(self) -> None:
        """Test NULL pushes None."""
        interp = StandardInterpreter()

        await interp.run("NULL")
        result = interp.stack_pop()
        assert result is None

    @pytest.mark.asyncio
    async def test_array_question_true(self) -> None:
        """Test ARRAY? returns true for arrays."""
        interp = StandardInterpreter()

        await interp.run("[1 2 3] ARRAY?")
        result = interp.stack_pop()
        assert result is True

    @pytest.mark.asyncio
    async def test_array_question_false(self) -> None:
        """Test ARRAY? returns false for non-arrays."""
        interp = StandardInterpreter()

        await interp.run("42 ARRAY?")
        result = interp.stack_pop()
        assert result is False

    @pytest.mark.asyncio
    async def test_default_with_value(self) -> None:
        """Test DEFAULT returns value if not None/empty."""
        interp = StandardInterpreter()

        await interp.run("42 99 DEFAULT")
        result = interp.stack_pop()
        assert result == 42

    @pytest.mark.asyncio
    async def test_default_with_none(self) -> None:
        """Test DEFAULT returns default if None."""
        interp = StandardInterpreter()

        await interp.run("NULL 99 DEFAULT")
        result = interp.stack_pop()
        assert result == 99

    @pytest.mark.asyncio
    async def test_default_with_empty_string(self) -> None:
        """Test DEFAULT returns default if empty string."""
        interp = StandardInterpreter()

        await interp.run('\"\" 99 DEFAULT')
        result = interp.stack_pop()
        assert result == 99

    @pytest.mark.asyncio
    async def test_star_default_with_value(self) -> None:
        """Test *DEFAULT returns value if not None/empty."""
        interp = StandardInterpreter()

        await interp.run('42 \"100\" *DEFAULT')
        result = interp.stack_pop()
        assert result == 42

    @pytest.mark.asyncio
    async def test_star_default_with_none(self) -> None:
        """Test *DEFAULT executes Forthic if None."""
        interp = StandardInterpreter()

        await interp.run('NULL \"50 50 +\" *DEFAULT')
        result = interp.stack_pop()
        assert result == 100


class TestWordOptions:
    """Test WordOptions and ~> operator."""

    @pytest.mark.asyncio
    async def test_tilde_gt_creates_word_options(self) -> None:
        """Test ~> converts array to WordOptions."""
        interp = StandardInterpreter()

        await interp.run("[.key1 .value1 .key2 42] ~>")
        result = interp.stack_pop()
        assert isinstance(result, WordOptions)
        assert result.get("key1") == "value1"
        assert result.get("key2") == 42


class TestStringOperations:
    """Test string and printing operations."""

    @pytest.mark.asyncio
    async def test_interpolate_simple(self, capsys) -> None:
        """Test INTERPOLATE with simple variable."""
        interp = StandardInterpreter()

        await interp.run('\"Alice\" .name ! \"Hello .name\" INTERPOLATE')
        result = interp.stack_pop()
        assert result == "Hello Alice"

    @pytest.mark.asyncio
    async def test_interpolate_with_separator(self, capsys) -> None:
        """Test INTERPOLATE with array and custom separator."""
        interp = StandardInterpreter()

        await interp.run('[1 2 3] .items ! \".items\" [.separator \" | \"] ~> INTERPOLATE')
        result = interp.stack_pop()
        assert result == "1 | 2 | 3"

    @pytest.mark.asyncio
    async def test_print_string(self, capsys) -> None:
        """Test PRINT with string interpolation."""
        interp = StandardInterpreter()

        await interp.run('5 .count ! \"Count: .count\" PRINT')
        captured = capsys.readouterr()
        assert "Count: 5" in captured.out

    @pytest.mark.asyncio
    async def test_print_array(self, capsys) -> None:
        """Test PRINT with array."""
        interp = StandardInterpreter()

        await interp.run("[1 2 3] PRINT")
        captured = capsys.readouterr()
        assert "1, 2, 3" in captured.out

    @pytest.mark.asyncio
    async def test_print_with_custom_separator(self, capsys) -> None:
        """Test PRINT with custom separator option."""
        interp = StandardInterpreter()

        await interp.run('[1 2 3] [.separator \" | \"] ~> PRINT')
        captured = capsys.readouterr()
        assert "1 | 2 | 3" in captured.out

    @pytest.mark.asyncio
    async def test_interpolate_multiple_variables(self) -> None:
        """Test INTERPOLATE with multiple variables in one string."""
        interp = StandardInterpreter()

        await interp.run('3 .number ! ["apple" "banana"] .queue !')
        await interp.run('"There are .number items: .queue" INTERPOLATE')
        result = interp.stack_pop()
        assert result == "There are 3 items: apple, banana"

    @pytest.mark.asyncio
    async def test_interpolate_with_string_operations(self) -> None:
        """Test INTERPOLATE can be used with string operations."""
        interp = StandardInterpreter()

        await interp.run('"hello" .word !')
        await interp.run('"Say .word" INTERPOLATE UPPERCASE')
        result = interp.stack_pop()
        assert result == "SAY HELLO"

    @pytest.mark.asyncio
    async def test_interpolate_custom_null_text(self) -> None:
        """Test INTERPOLATE with custom null_text option."""
        interp = StandardInterpreter()

        await interp.run('"Missing: .missing" [.null_text "N/A"] ~> INTERPOLATE')
        result = interp.stack_pop()
        assert result == "Missing: N/A"

    @pytest.mark.asyncio
    async def test_interpolate_escaped_dots(self) -> None:
        """Test INTERPOLATE with escaped dots."""
        interp = StandardInterpreter()

        await interp.run('42 .linecount !')
        await interp.run(r'"Config: \.bashrc has .linecount lines" INTERPOLATE')
        result = interp.stack_pop()
        assert result == "Config: .bashrc has 42 lines"

    @pytest.mark.asyncio
    async def test_interpolate_decimal_numbers(self) -> None:
        """Test INTERPOLATE doesn't interpolate decimal numbers."""
        interp = StandardInterpreter()

        await interp.run('5 .count !')
        await interp.run('"Price is $10.50 for .count items" INTERPOLATE')
        result = interp.stack_pop()
        assert result == "Price is $10.50 for 5 items"

    @pytest.mark.asyncio
    async def test_print_multiple_variables(self, capsys) -> None:
        """Test PRINT with multiple variables."""
        interp = StandardInterpreter()

        await interp.run('3 .number ! ["apple" "banana"] .queue !')
        await interp.run('"There are .number items in the queue: .queue" PRINT')
        captured = capsys.readouterr()
        assert "There are 3 items in the queue: apple, banana" in captured.out

    @pytest.mark.asyncio
    async def test_print_decimal_numbers(self, capsys) -> None:
        """Test PRINT doesn't interpolate decimal numbers."""
        interp = StandardInterpreter()

        await interp.run('5 .count !')
        await interp.run('"Price is $10.50 for .count items" PRINT')
        captured = capsys.readouterr()
        assert "Price is $10.50 for 5 items" in captured.out

    @pytest.mark.asyncio
    async def test_print_variable_at_start(self, capsys) -> None:
        """Test PRINT with variable at start of string."""
        interp = StandardInterpreter()

        await interp.run('["apple" "banana"] .items !')
        await interp.run('".items are available" PRINT')
        captured = capsys.readouterr()
        assert "apple, banana are available" in captured.out

    @pytest.mark.asyncio
    async def test_print_undefined_variable(self, capsys) -> None:
        """Test PRINT with undefined variable creates null."""
        interp = StandardInterpreter()

        await interp.run('"Value: .undefined" PRINT')
        captured = capsys.readouterr()
        assert "Value: null" in captured.out or "Value: None" in captured.out

    @pytest.mark.asyncio
    async def test_print_custom_null_text(self, capsys) -> None:
        """Test PRINT with custom null_text option."""
        interp = StandardInterpreter()

        await interp.run('"Missing: .missing" [.null_text "N/A"] ~> PRINT')
        captured = capsys.readouterr()
        assert "Missing: N/A" in captured.out

    @pytest.mark.asyncio
    async def test_print_escaped_dots(self, capsys) -> None:
        """Test PRINT with escaped dots."""
        interp = StandardInterpreter()

        await interp.run('42 .linecount !')
        await interp.run(r'"Config file: \.bashrc has .linecount lines" PRINT')
        captured = capsys.readouterr()
        assert "Config file: .bashrc has 42 lines" in captured.out

    @pytest.mark.asyncio
    async def test_print_empty_string(self, capsys) -> None:
        """Test PRINT with empty string."""
        interp = StandardInterpreter()

        await interp.run('"" PRINT')
        captured = capsys.readouterr()
        # Just verify it didn't crash - output will be empty or newline

    @pytest.mark.asyncio
    async def test_print_boolean_values(self, capsys) -> None:
        """Test PRINT with boolean values."""
        interp = StandardInterpreter()

        await interp.run('TRUE .flag !')
        await interp.run('"Flag is: .flag" PRINT')
        captured = capsys.readouterr()
        assert "Flag is: true" in captured.out or "Flag is: True" in captured.out


class TestExecution:
    """Test code execution."""

    @pytest.mark.asyncio
    async def test_interpret(self) -> None:
        """Test INTERPRET executes Forthic string."""
        interp = StandardInterpreter()

        await interp.run('\"10 20 +\" INTERPRET')
        result = interp.stack_pop()
        assert result == 30



class TestDebug:
    """Test debug operations."""

    @pytest.mark.asyncio
    async def test_peek_bang_stops_execution(self, capsys) -> None:
        """Test PEEK! prints top of stack and stops."""
        interp = StandardInterpreter()

        with pytest.raises(IntentionalStopError):
            await interp.run("42 PEEK!")
        captured = capsys.readouterr()
        assert "42" in captured.out

    @pytest.mark.asyncio
    async def test_stack_bang_stops_execution(self, capsys) -> None:
        """Test STACK! prints entire stack and stops."""
        interp = StandardInterpreter()

        with pytest.raises(IntentionalStopError):
            await interp.run("1 2 3 STACK!")
        captured = capsys.readouterr()
        assert "3" in captured.out
        assert "2" in captured.out
        assert "1" in captured.out


class TestProfiling:
    """Test profiling operations."""

    @pytest.mark.asyncio
    async def test_profiling_basic(self) -> None:
        """Test basic profiling workflow."""
        interp = StandardInterpreter()

        await interp.run("PROFILE-START")
        await interp.run("1 2 + 3 4 +")
        await interp.run("PROFILE-END")
        await interp.run("PROFILE-DATA")

        result = interp.stack_pop()
        assert "word_counts" in result
        assert "timestamps" in result
        assert len(result["word_counts"]) > 0

    @pytest.mark.asyncio
    async def test_profiling_timestamps(self) -> None:
        """Test profiling with timestamps."""
        interp = StandardInterpreter()

        await interp.run("PROFILE-START")
        await interp.run('\"start\" PROFILE-TIMESTAMP')
        await interp.run("1 2 +")
        await interp.run('\"end\" PROFILE-TIMESTAMP')
        await interp.run("PROFILE-DATA")

        result = interp.stack_pop()
        timestamps = result["timestamps"]
        assert len(timestamps) == 2
        assert timestamps[0]["label"] == "start"
        assert timestamps[1]["label"] == "end"
        assert "delta" in timestamps[0]
        assert "time_ms" in timestamps[0]
