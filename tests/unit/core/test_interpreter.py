"""Tests for Forthic interpreter."""

import pytest

from forthic import Interpreter, Module, PushValueWord, StackUnderflowError, UnknownWordError


class TestBasicExecution:
    """Test basic interpreter execution."""

    @pytest.mark.asyncio
    async def test_push_literal_integers(self) -> None:
        interp = Interpreter()
        await interp.run("42 100")
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 42
        assert stack[1] == 100

    @pytest.mark.asyncio
    async def test_push_literal_floats(self) -> None:
        interp = Interpreter()
        await interp.run("3.14 2.5")
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 3.14
        assert stack[1] == 2.5

    @pytest.mark.asyncio
    async def test_push_literal_booleans(self) -> None:
        interp = Interpreter()
        await interp.run("TRUE FALSE")
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] is True
        assert stack[1] is False

    @pytest.mark.asyncio
    async def test_push_strings(self) -> None:
        interp = Interpreter()
        await interp.run('"Hello" "World"')
        stack = interp.get_stack()
        assert len(stack) == 2
        # PositionedStrings are stored on stack
        from forthic import PositionedString
        assert isinstance(stack[0], PositionedString)
        assert str(stack[0]) == "Hello"
        assert str(stack[1]) == "World"

    @pytest.mark.asyncio
    async def test_create_array(self) -> None:
        interp = Interpreter()
        await interp.run("[1 2 3]")
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_nested_arrays(self) -> None:
        interp = Interpreter()
        await interp.run("[[1 2] [3 4]]")
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == [[1, 2], [3, 4]]


class TestDefinitions:
    """Test word definitions."""

    @pytest.mark.asyncio
    async def test_simple_definition(self) -> None:
        interp = Interpreter()

        # Create a simple word that pushes 42
        await interp.run(": ANSWER 42 ;")

        # Execute it
        await interp.run("ANSWER")
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == 42

    @pytest.mark.asyncio
    async def test_definition_with_multiple_words(self) -> None:
        interp = Interpreter()

        # Define a word that pushes two numbers
        await interp.run(": TWO_NUMS 10 20 ;")

        await interp.run("TWO_NUMS")
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 10
        assert stack[1] == 20

    @pytest.mark.asyncio
    async def test_calling_defined_word_in_definition(self) -> None:
        interp = Interpreter()

        # Define a word
        await interp.run(": BASE 5 ;")

        # Define another word that uses the first
        await interp.run(": DERIVED BASE BASE ;")

        await interp.run("DERIVED")
        stack = interp.get_stack()
        assert len(stack) == 2
        assert stack[0] == 5
        assert stack[1] == 5


class TestModules:
    """Test module system."""

    @pytest.mark.asyncio
    async def test_inline_module(self) -> None:
        interp = Interpreter()

        # Create inline module
        await interp.run("{mymodule : WORD 42 ; }")

        # Module should be registered but word not accessible yet
        module = interp.find_module("mymodule")
        assert module is not None
        assert module.name == "mymodule"

    @pytest.mark.asyncio
    async def test_module_with_custom_word(self) -> None:
        interp = Interpreter()

        # Create a custom module with a word
        module = Module("test")

        async def push_hello(interp: Interpreter) -> None:
            interp.stack_push("hello")

        word = PushValueWord("HELLO", "hello")
        module.add_exportable_word(word)

        # Register and import module
        interp.register_module(module)
        interp.use_modules(["test"])

        # Use the word
        await interp.run("HELLO")
        stack = interp.get_stack()
        assert len(stack) == 1
        assert stack[0] == "hello"


class TestStackOperations:
    """Test stack-related operations."""

    @pytest.mark.asyncio
    async def test_stack_underflow(self) -> None:
        interp = Interpreter()

        # Create a word that pops from stack
        async def pop_word(interp: Interpreter) -> None:
            interp.stack_pop()

        module = Module("test")
        word = PushValueWord("POP", None)
        word.execute = pop_word  # type: ignore
        module.add_exportable_word(word)
        interp.import_module(module)

        # Try to pop from empty stack
        with pytest.raises(StackUnderflowError):
            await interp.run("POP")

    @pytest.mark.asyncio
    async def test_unknown_word(self) -> None:
        interp = Interpreter()

        with pytest.raises(UnknownWordError) as exc_info:
            await interp.run("UNDEFINED_WORD")

        assert "UNDEFINED_WORD" in str(exc_info.value)


class TestVariables:
    """Test variable system."""

    @pytest.mark.asyncio
    async def test_add_variable(self) -> None:
        interp = Interpreter()
        module = interp.get_app_module()

        # Add a variable
        module.add_variable("MY_VAR", 42)

        # Access it (variables push themselves when accessed)
        await interp.run("MY_VAR")

        # The variable object should be on the stack
        stack = interp.get_stack()
        assert len(stack) == 1
        from forthic import Variable

        var = stack[0]
        assert isinstance(var, Variable)
        assert var.get_value() == 42


class TestMemoWords:
    """Test memoized words."""

    @pytest.mark.asyncio
    async def test_memo_definition(self) -> None:
        interp = Interpreter()

        # Create a memo word
        await interp.run("@: MEMO_DATA 42 ;")

        # First access should execute and cache
        await interp.run("MEMO_DATA")
        stack = interp.get_stack()
        assert stack[0] == 42

        # Clear stack
        interp.get_stack().pop()

        # Second access should return cached value
        await interp.run("MEMO_DATA")
        assert stack[0] == 42


class TestReset:
    """Test interpreter reset."""

    @pytest.mark.asyncio
    async def test_reset_clears_stack(self) -> None:
        interp = Interpreter()
        await interp.run("1 2 3")
        assert len(interp.get_stack()) == 3

        interp.reset()
        assert len(interp.get_stack()) == 0

    @pytest.mark.asyncio
    async def test_reset_clears_variables(self) -> None:
        interp = Interpreter()
        module = interp.get_app_module()
        module.add_variable("VAR", 42)

        interp.reset()
        assert len(module.variables) == 0
