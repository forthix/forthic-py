"""Tests for decorator system (@Word, @DirectWord, DecoratedModule)."""

import pytest

from forthic import (
    DecoratedModule,
    DirectWord,
    Interpreter,
    WordOptions,
    register_module_doc,
)
from forthic import (
    WordDecorator as Word,
)


class TestWordDecorator:
    """Test @Word decorator functionality."""

    @pytest.mark.asyncio
    async def test_simple_word(self) -> None:
        """Test basic @Word decorator with simple parameters."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @Word("( a:number b:number -- sum:number )", "Add two numbers")
            async def ADD(self, a: int, b: int) -> int:
                return a + b

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        await interp.run("5 3 ADD")
        result = interp.stack_pop()
        assert result == 8

    @pytest.mark.asyncio
    async def test_word_with_custom_name(self) -> None:
        """Test @Word decorator with custom word name."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @Word("( a:number b:number -- product:number )", "Multiply", "*")
            async def MULTIPLY(self, a: int, b: int) -> int:
                return a * b

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        await interp.run("4 3 *")
        result = interp.stack_pop()
        assert result == 12

    @pytest.mark.asyncio
    async def test_word_no_inputs(self) -> None:
        """Test @Word with no inputs."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @Word("( -- value:number )", "Push 42")
            async def ANSWER(self) -> int:
                return 42

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        await interp.run("ANSWER")
        result = interp.stack_pop()
        assert result == 42

    @pytest.mark.asyncio
    async def test_word_returns_none(self) -> None:
        """Test @Word that returns None (nothing pushed to stack)."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")
                self.called = False

            @Word("( -- )", "Set flag")
            async def SET_FLAG(self) -> None:
                self.called = True
                return None

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        stack_len_before = len(interp.get_stack())
        await interp.run("SET_FLAG")
        stack_len_after = len(interp.get_stack())

        assert module.called is True
        assert stack_len_before == stack_len_after

    @pytest.mark.asyncio
    async def test_word_with_options(self) -> None:
        """Test @Word with WordOptions parameter."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @Word(
                "( array:list [options:WordOptions] -- result:list )", "Process array with options"
            )
            async def PROCESS(self, array: list, options: dict) -> list:
                multiplier = options.get("multiplier", 1)
                return [x * multiplier for x in array]

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        # Without options
        await interp.run("[1 2 3] PROCESS")
        result = interp.stack_pop()
        assert result == [1, 2, 3]

        # With options (Note: need to push WordOptions object)
        interp.stack_push([1, 2, 3])
        interp.stack_push(WordOptions(["multiplier", 2]))
        await interp.run("PROCESS")
        result = interp.stack_pop()
        assert result == [2, 4, 6]


class TestDirectWordDecorator:
    """Test @DirectWord decorator functionality."""

    @pytest.mark.asyncio
    async def test_direct_word_manual_stack(self) -> None:
        """Test @DirectWord with manual stack manipulation."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @DirectWord("( a:number b:number -- result:number )", "Swap and subtract")
            async def SWAP_SUB(self, interp: Interpreter) -> None:
                b = interp.stack_pop()
                a = interp.stack_pop()
                # Swap order and subtract
                interp.stack_push(b - a)

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        await interp.run("3 7 SWAP_SUB")
        result = interp.stack_pop()
        assert result == 4  # 7 - 3

    @pytest.mark.asyncio
    async def test_direct_word_custom_name(self) -> None:
        """Test @DirectWord with custom name."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @DirectWord("( item:any n:number -- )", "Duplicate n times", "<DUP")
            async def l_DUP(self, interp: Interpreter) -> None:
                n = interp.stack_pop()
                item = interp.stack_pop()
                for _ in range(n):
                    interp.stack_push(item)

        interp = Interpreter()
        module = TestModule()
        interp.import_module(module._module)

        await interp.run("5 3 <DUP")
        stack = interp.get_stack()
        assert len(stack) == 3
        assert all(stack[i] == 5 for i in range(3))


class TestDecoratedModule:
    """Test DecoratedModule functionality."""

    @pytest.mark.asyncio
    async def test_module_with_multiple_words(self) -> None:
        """Test module with multiple decorated words."""

        class MathModule(DecoratedModule):
            def __init__(self):
                super().__init__("math")

            @Word("( a:number b:number -- sum:number )", "Add")
            async def ADD(self, a: int, b: int) -> int:
                return a + b

            @Word("( a:number b:number -- diff:number )", "Subtract")
            async def SUB(self, a: int, b: int) -> int:
                return a - b

            @Word("( a:number b:number -- product:number )", "Multiply")
            async def MUL(self, a: int, b: int) -> int:
                return a * b

        interp = Interpreter()
        module = MathModule()
        interp.import_module(module._module)

        await interp.run("10 3 ADD")
        assert interp.stack_pop() == 13

        await interp.run("10 3 SUB")
        assert interp.stack_pop() == 7

        await interp.run("10 3 MUL")
        assert interp.stack_pop() == 30

    @pytest.mark.asyncio
    async def test_get_word_docs(self) -> None:
        """Test getting documentation from decorated module."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")

            @Word("( a:number b:number -- sum:number )", "Add two numbers")
            async def ADD(self, a: int, b: int) -> int:
                return a + b

            @DirectWord("( -- )", "Do nothing")
            async def NOP(self, interp: Interpreter) -> None:
                pass

        module = TestModule()
        docs = module.get_word_docs()

        assert len(docs) == 2
        # Check ADD doc
        add_doc = next(d for d in docs if d["name"] == "ADD")
        assert add_doc["stackEffect"] == "( a:number b:number -- sum:number )"
        assert add_doc["description"] == "Add two numbers"

        # Check NOP doc
        nop_doc = next(d for d in docs if d["name"] == "NOP")
        assert nop_doc["stackEffect"] == "( -- )"
        assert nop_doc["description"] == "Do nothing"


class TestModuleDocumentation:
    """Test module documentation system."""

    def test_register_module_doc(self) -> None:
        """Test registering module documentation."""

        class TestModule(DecoratedModule):
            def __init__(self):
                super().__init__("test")
                register_module_doc(
                    TestModule,
                    """
                    Test module for documentation

                    ## Categories
                    - Math: ADD, SUB, MUL
                    - Logic: AND, OR, NOT

                    ## Options
                    Some words support options via ~> operator

                    ## Examples
                    5 3 ADD
                    TRUE FALSE AND
                    """,
                )

            @Word("( a:number b:number -- sum:number )", "Add")
            async def ADD(self, a: int, b: int) -> int:
                return a + b

        module = TestModule()
        metadata = module.get_module_metadata()

        assert metadata is not None
        assert metadata["name"] == "test"
        assert "Test module for documentation" in metadata["description"]
        assert len(metadata["categories"]) == 2
        assert metadata["categories"][0]["name"] == "Math"
        assert metadata["categories"][0]["words"] == "ADD, SUB, MUL"
        assert "Some words support options" in metadata["optionsInfo"]
        assert len(metadata["examples"]) == 2


class TestWordOptions:
    """Test WordOptions class."""

    def test_word_options_creation(self) -> None:
        """Test creating WordOptions from flat array."""
        opts = WordOptions(["key1", "value1", "key2", 42])
        assert opts.get("key1") == "value1"
        assert opts.get("key2") == 42

    def test_word_options_has(self) -> None:
        """Test checking if option exists."""
        opts = WordOptions(["key1", "value1"])
        assert opts.has("key1") is True
        assert opts.has("key2") is False

    def test_word_options_default(self) -> None:
        """Test getting option with default value."""
        opts = WordOptions(["key1", "value1"])
        assert opts.get("key1", "default") == "value1"
        assert opts.get("key2", "default") == "default"

    def test_word_options_to_dict(self) -> None:
        """Test converting to dict."""
        opts = WordOptions(["key1", "value1", "key2", 42])
        d = opts.to_dict()
        assert d == {"key1": "value1", "key2": 42}

    def test_word_options_keys(self) -> None:
        """Test getting all keys."""
        opts = WordOptions(["key1", "value1", "key2", 42])
        keys = opts.keys()
        assert set(keys) == {"key1", "key2"}

    def test_word_options_invalid_length(self) -> None:
        """Test that odd-length array raises error."""
        with pytest.raises(ValueError, match="even length"):
            WordOptions(["key1", "value1", "key2"])

    def test_word_options_invalid_key_type(self) -> None:
        """Test that non-string key raises error."""
        with pytest.raises(TypeError, match="must be a string"):
            WordOptions([42, "value1"])


class TestStackNotationParsing:
    """Test parsing of stack notation strings."""

    def test_parse_simple_notation(self) -> None:
        """Test parsing simple stack notation."""
        from forthic.decorators.word import parse_stack_notation

        count, has_opts = parse_stack_notation("( a:any b:any -- result:any )")
        assert count == 2
        assert has_opts is False

    def test_parse_no_inputs(self) -> None:
        """Test parsing notation with no inputs."""
        from forthic.decorators.word import parse_stack_notation

        count, has_opts = parse_stack_notation("( -- value:any )")
        assert count == 0
        assert has_opts is False

    def test_parse_with_options(self) -> None:
        """Test parsing notation with options."""
        from forthic.decorators.word import parse_stack_notation

        count, has_opts = parse_stack_notation(
            "( items:list [options:WordOptions] -- result:list )"
        )
        assert count == 1
        assert has_opts is True

    def test_parse_invalid_notation(self) -> None:
        """Test that invalid notation raises error."""
        from forthic.decorators.word import parse_stack_notation

        with pytest.raises(ValueError, match="parentheses"):
            parse_stack_notation("a:any b:any -- result:any")

        with pytest.raises(ValueError, match="Invalid stack notation"):
            parse_stack_notation("( a:any b:any )")
