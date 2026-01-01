"""Module system for Forthic.

Includes Word classes, Variable, Module, and Stack.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from .tokenizer import CodeLocation, PositionedString

if TYPE_CHECKING:
    from .interpreter import Interpreter

# Type alias for word handlers
WordHandler = Callable[["Interpreter"], Coroutine[Any, Any, None]]

# Type alias for error handlers
WordErrorHandler = Callable[[Exception, "Word", "Interpreter"], Coroutine[Any, Any, None]]


# -------------------------------------
# Variable


class Variable:
    """Named mutable value container.

    Represents a variable that can store and retrieve values within a module scope.
    """

    def __init__(self, name: str, value: Any = None):
        self.name = name
        self.value = value

    def get_name(self) -> str:
        return self.name

    def set_value(self, val: Any) -> None:
        self.value = val

    def get_value(self) -> Any:
        return self.value

    def dup(self) -> Variable:
        """Create a duplicate of this variable."""
        return Variable(self.name, self.value)


# -------------------------------------
# Words


class Word:
    """Base class for all executable words in Forthic.

    A word is the fundamental unit of execution. When interpreted,
    it performs an action (typically manipulating the stack or control flow).
    """

    def __init__(self, name: str):
        self.name = name
        self.string = name
        self.location: CodeLocation | None = None
        self.error_handlers: list[WordErrorHandler] = []

    def set_location(self, location: CodeLocation | None) -> None:
        self.location = location

    def get_location(self) -> CodeLocation | None:
        return self.location

    def add_error_handler(self, handler: WordErrorHandler) -> None:
        """Add an error handler to this word."""
        self.error_handlers.append(handler)

    def remove_error_handler(self, handler: WordErrorHandler) -> None:
        """Remove a specific error handler."""
        try:
            self.error_handlers.remove(handler)
        except ValueError:
            pass  # Handler not in list

    def clear_error_handlers(self) -> None:
        """Remove all error handlers."""
        self.error_handlers.clear()

    def get_error_handlers(self) -> list[WordErrorHandler]:
        """Get a copy of the error handlers list."""
        return self.error_handlers.copy()

    async def try_error_handlers(self, error: Exception, interp: Interpreter) -> bool:
        """
        Try error handlers in order until one succeeds.
        Returns True if any handler succeeded, False otherwise.
        """
        for handler in self.error_handlers:
            try:
                await handler(error, self, interp)
                return True  # Handler succeeded
            except Exception:
                continue  # Try next handler
        return False  # No handler succeeded

    async def execute(self, interp: Interpreter) -> None:
        """Execute this word. Must be overridden by subclasses."""
        raise NotImplementedError("Must override Word.execute")


class PushValueWord(Word):
    """Word that pushes a value onto the stack.

    Used for literals, variables, and constants.
    """

    def __init__(self, name: str, value: Any):
        super().__init__(name)
        self.value = value

    async def execute(self, interp: Interpreter) -> None:
        interp.stack_push(self.value)


class DefinitionWord(Word):
    """User-defined word composed of other words.

    Represents a word defined in Forthic code using `:`.
    Contains a sequence of words that are executed in order.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.words: list[Word] = []

    def add_word(self, word: Word) -> None:
        self.words.append(word)

    async def execute(self, interp: Interpreter) -> None:
        from .errors import WordExecutionError

        for word in self.words:
            try:
                await word.execute(interp)
            except Exception as e:
                tokenizer = interp.get_tokenizer()
                raise WordExecutionError(
                    f"Error executing {self.name}",
                    e,
                    tokenizer.get_token_location(),  # Where the word was called
                    word.get_location(),  # Where the word was defined
                ) from e


class ModuleMemoWord(Word):
    """Memoized word that caches its result.

    Executes the wrapped word once and caches the result.
    Subsequent calls return the cached value without re-executing.
    Defined in Forthic using `@:`.
    """

    def __init__(self, word: Word):
        super().__init__(word.name)
        self.word = word
        self.has_value = False
        self.value: Any = None

    async def refresh(self, interp: Interpreter) -> None:
        """Re-execute the word and update cached value."""
        await self.word.execute(interp)
        self.value = interp.stack_pop()
        self.has_value = True

    async def execute(self, interp: Interpreter) -> None:
        if not self.has_value:
            await self.refresh(interp)
        interp.stack_push(self.value)


class ModuleMemoBangWord(Word):
    """Forces refresh of a memoized word.

    Re-executes the memoized word and updates its cached value.
    Named with a `!` suffix.
    """

    def __init__(self, memo_word: ModuleMemoWord):
        super().__init__(f"{memo_word.name}!")
        self.memo_word = memo_word

    async def execute(self, interp: Interpreter) -> None:
        await self.memo_word.refresh(interp)


class ModuleMemoBangAtWord(Word):
    """Refreshes a memoized word and returns its value.

    Re-executes the memoized word, updates cached value, and pushes it.
    Named with a `!@` suffix.
    """

    def __init__(self, memo_word: ModuleMemoWord):
        super().__init__(f"{memo_word.name}!@")
        self.memo_word = memo_word

    async def execute(self, interp: Interpreter) -> None:
        await self.memo_word.refresh(interp)
        interp.stack_push(self.memo_word.value)


class ExecuteWord(Word):
    """Wrapper word that executes another word.

    Used for prefixed module imports to create words like `prefix.word`.
    """

    def __init__(self, name: str, target_word: Word):
        super().__init__(name)
        self.target_word = target_word

    async def execute(self, interp: Interpreter) -> None:
        await self.target_word.execute(interp)


class ModuleWord(Word):
    """Word that executes a handler function with error handling support.

    Used for module words created via decorators or add_module_word().
    Integrates per-word error handler functionality.
    """

    def __init__(self, name: str, handler: WordHandler):
        super().__init__(name)
        self.handler = handler

    async def execute(self, interp: Interpreter) -> None:
        from .errors import IntentionalStopError

        try:
            await self.handler(interp)
        except IntentionalStopError:
            # Never handle intentional flow control errors
            raise
        except Exception as e:
            # Try error handlers
            handled = await self.try_error_handlers(e, interp)
            if not handled:
                raise  # Re-raise if not handled
            # If handled, execution continues (error suppressed)


# -------------------------------------
# Module


class Module:
    """Container for words, variables, and imported modules.

    Modules provide namespacing and code organization in Forthic.
    Each module maintains its own dictionary of words, variables, and imported modules.
    """

    def __init__(self, name: str, forthic_code: str = ""):
        self.words: list[Word] = []
        self.exportable: list[str] = []
        self.variables: dict[str, Variable] = {}
        self.modules: dict[str, Module] = {}
        self.module_prefixes: dict[str, set[str]] = {}
        self.name = name
        self.forthic_code = forthic_code
        self.interp: Interpreter | None = None

    def get_name(self) -> str:
        return self.name

    def set_interp(self, interp: Interpreter) -> None:
        self.interp = interp

    def get_interp(self) -> Interpreter:
        if self.interp is None:
            raise ValueError(f"Module {self.name} has no interpreter")
        return self.interp

    # Duplication methods

    def dup(self) -> Module:
        """Create a shallow duplicate of this module."""
        result = Module(self.name)
        result.words = self.words.copy()
        result.exportable = self.exportable.copy()
        result.variables = {k: v.dup() for k, v in self.variables.items()}
        result.modules = self.modules.copy()
        result.forthic_code = self.forthic_code
        return result

    def copy(self, interp: Interpreter) -> Module:
        """Create a copy with module prefixes restored."""
        result = Module(self.name)
        result.words = self.words.copy()
        result.exportable = self.exportable.copy()
        result.variables = {k: v.dup() for k, v in self.variables.items()}
        result.modules = self.modules.copy()

        # Restore module_prefixes
        for module_name, prefixes in self.module_prefixes.items():
            for prefix in prefixes:
                result.import_module(prefix, self.modules[module_name], interp)

        result.forthic_code = self.forthic_code
        return result

    # Module management

    def find_module(self, name: str) -> Module | None:
        return self.modules.get(name)

    def register_module(self, module_name: str, prefix: str, module: Module) -> None:
        self.modules[module_name] = module

        if module_name not in self.module_prefixes:
            self.module_prefixes[module_name] = set()
        self.module_prefixes[module_name].add(prefix)

    def import_module(self, prefix: str, module: Module, interp: Interpreter) -> None:
        new_module = module.dup()

        words = new_module.exportable_words()
        for word in words:
            # For unprefixed imports, add word directly
            if prefix == "":
                self.add_word(word)
            else:
                # For prefixed imports, create ExecuteWord
                prefixed_word = ExecuteWord(f"{prefix}.{word.name}", word)
                self.add_word(prefixed_word)
        self.register_module(module.name, prefix, new_module)

    # Word management

    def add_word(self, word: Word) -> None:
        self.words.append(word)

    def add_memo_words(self, word: Word) -> ModuleMemoWord:
        """Add a memo word and its ! and !@ variants."""
        memo_word = ModuleMemoWord(word)
        self.words.append(memo_word)
        self.words.append(ModuleMemoBangWord(memo_word))
        self.words.append(ModuleMemoBangAtWord(memo_word))
        return memo_word

    def add_exportable(self, names: list[str]) -> None:
        self.exportable.extend(names)

    def add_exportable_word(self, word: Word) -> None:
        self.words.append(word)
        self.exportable.append(word.name)

    def add_module_word(
        self, word_name: str, word_func: Callable[[Interpreter], Coroutine[Any, Any, None]]
    ) -> ModuleWord:
        """Add a word with a handler function."""
        word = ModuleWord(word_name, word_func)
        self.add_exportable_word(word)
        return word

    def exportable_words(self) -> list[Word]:
        """Get list of exportable words."""
        result: list[Word] = []
        for word in self.words:
            if word.name in self.exportable:
                result.append(word)
        return result

    def find_word(self, name: str) -> Word | None:
        """Find a word by name (checks dictionary words and variables)."""
        result = self.find_dictionary_word(name)
        if result is None:
            result = self.find_variable(name)
        return result

    def find_dictionary_word(self, word_name: str) -> Word | None:
        """Find a word in the module's dictionary."""
        # Search from most recent to oldest
        for word in reversed(self.words):
            if word.name == word_name:
                return word
        return None

    def find_variable(self, varname: str) -> PushValueWord | None:
        """Find a variable and return it as a PushValueWord."""
        var_result = self.variables.get(varname)
        if var_result:
            return PushValueWord(varname, var_result)
        return None

    # Variable management

    def add_variable(self, name: str, value: Any = None) -> None:
        """Add a variable if it doesn't already exist."""
        if name not in self.variables:
            self.variables[name] = Variable(name, value)


# -------------------------------------
# Stack


class Stack:
    """Wrapper for the interpreter's data stack.

    Provides stack operations with support for PositionedString unwrapping.
    """

    def __init__(self, items: list[Any] | None = None):
        self._items: list[Any] = items if items is not None else []

    def get_items(self) -> list[Any]:
        """Get stack items with PositionedStrings unwrapped."""
        return [
            item.string if isinstance(item, PositionedString) else item
            for item in self._items
        ]

    def get_raw_items(self) -> list[Any]:
        """Get raw stack items (including PositionedStrings)."""
        return self._items

    def set_raw_items(self, items: list[Any]) -> None:
        """Set raw stack items."""
        self._items = items

    def pop(self) -> Any:
        """Pop an item from the stack."""
        return self._items.pop()

    def push(self, item: Any) -> None:
        """Push an item onto the stack."""
        self._items.append(item)

    def __len__(self) -> int:
        """Get stack length."""
        return len(self._items)

    def __getitem__(self, index: int) -> Any:
        """Get item at index."""
        return self._items[index]

    def __setitem__(self, index: int, value: Any) -> None:
        """Set item at index."""
        self._items[index] = value

    def dup(self) -> Stack:
        """Create a shallow copy of the stack."""
        return Stack(self._items.copy())
