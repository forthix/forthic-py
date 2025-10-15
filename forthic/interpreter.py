"""Forthic interpreter.

Core interpreter that tokenizes and executes Forthic code.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo

from .errors import (
    ExtraSemicolonError,
    MissingSemicolonError,
    ModuleError,
    StackUnderflowError,
    TooManyAttemptsError,
    UnknownModuleError,
    UnknownTokenError,
    UnknownWordError,
)
from .literals import (
    LiteralHandler,
    to_bool,
    to_float,
    to_int,
    to_literal_date,
    to_time,
    to_zoned_datetime,
)
from .module import (
    DefinitionWord,
    Module,
    PushValueWord,
    Stack,
    Word,
)
from .tokenizer import CodeLocation, PositionedString, Token, Tokenizer, TokenType

# Type alias for error handlers
HandleErrorFunction = Callable[[Exception, "Interpreter"], Coroutine[Any, Any, None]]


# -------------------------------------
# Special Words for Interpreter


class StartModuleWord(Word):
    """Handles module creation and switching.

    Pushes a module onto the module stack, creating it if necessary.
    Empty name refers to the app module.
    """

    async def execute(self, interp: Interpreter) -> None:
        # The app module is the only module with a blank name
        if self.name == "":
            interp.module_stack_push(interp.get_app_module())
            return

        # If the module is used by the current module, push it, otherwise create new
        module = interp.cur_module().find_module(self.name)
        if module is None:
            module = Module(self.name)
            interp.cur_module().register_module(module.name, module.name, module)

            # If we're at the app module, also register with interpreter
            if interp.cur_module().name == "":
                interp.register_module(module)
        interp.module_stack_push(module)


class EndModuleWord(Word):
    """Pops the current module from the module stack."""

    def __init__(self) -> None:
        super().__init__("}")

    async def execute(self, interp: Interpreter) -> None:
        interp.module_stack_pop()


class EndArrayWord(Word):
    """Collects items from stack into an array.

    Pops items from the stack until a START_ARRAY token is found,
    then pushes them as a single array in the correct order.
    """

    def __init__(self) -> None:
        super().__init__("]")

    async def execute(self, interp: Interpreter) -> None:
        items: list[Any] = []
        while True:
            item = interp.stack_pop()
            if isinstance(item, Token) and item.type == TokenType.START_ARRAY:
                break
            items.append(item)
        items.reverse()
        interp.stack_push(items)


# -------------------------------------
# Interpreter


class Interpreter:
    """Base Forthic interpreter.

    Core interpreter that tokenizes and executes Forthic code.
    Manages the data stack, module stack, and execution context.

    Note: This is the base interpreter without standard library modules.
    """

    def __init__(self, modules: list[Module] | None = None, timezone: str | ZoneInfo = "UTC"):
        self._timezone = ZoneInfo(timezone) if isinstance(timezone, str) else timezone
        self._stack = Stack()
        self._app_module = Module("")
        self._app_module.set_interp(self)
        self._module_stack: list[Module] = [self._app_module]
        self._registered_modules: dict[str, Module] = {}
        self._tokenizer_stack: list[Tokenizer] = []
        self._previous_token: Token | None = None
        self._handle_error: HandleErrorFunction | None = None
        self._max_attempts = 3

        # Compilation state
        self._is_compiling = False
        self._is_memo_definition = False
        self._cur_definition: DefinitionWord | None = None

        # Debug support
        self._string_location: CodeLocation | None = None

        # Profiling support
        self._word_counts: dict[str, int] = {}
        self._is_profiling = False
        self._timestamps: list[dict[str, Any]] = []

        # Literal handlers
        self._literal_handlers: list[LiteralHandler] = []
        self._register_standard_literals()

        # Import provided modules
        if modules:
            self.import_modules(modules)

    # ======================
    # Basic getters/setters

    def get_app_module(self) -> Module:
        return self._app_module

    def get_top_input_string(self) -> str:
        if len(self._tokenizer_stack) == 0:
            return ""
        return self._tokenizer_stack[0].get_input_string()

    def get_tokenizer(self) -> Tokenizer:
        return self._tokenizer_stack[-1]

    def get_string_location(self) -> CodeLocation | None:
        return self._string_location

    def get_timezone(self) -> ZoneInfo:
        return self._timezone

    def set_timezone(self, timezone: str | ZoneInfo) -> None:
        self._timezone = ZoneInfo(timezone) if isinstance(timezone, str) else timezone

    def set_max_attempts(self, max_attempts: int) -> None:
        self._max_attempts = max_attempts

    def set_error_handler(self, handle_error: HandleErrorFunction) -> None:
        self._handle_error = handle_error

    def get_max_attempts(self) -> int:
        return self._max_attempts

    def get_error_handler(self) -> HandleErrorFunction | None:
        return self._handle_error

    def reset(self) -> None:
        """Reset interpreter state."""
        self._stack = Stack()
        self._app_module.variables = {}
        self._module_stack = [self._app_module]
        self._is_compiling = False
        self._is_memo_definition = False
        self._cur_definition = None
        self._string_location = None

    # ======================
    # Execution

    async def run(
        self, string: str, reference_location: CodeLocation | None = None
    ) -> bool:
        """Execute Forthic code."""
        self._tokenizer_stack.append(Tokenizer(string, reference_location))

        if self._handle_error:
            await self._execute_with_recovery()
        else:
            await self._run_with_tokenizer(self._tokenizer_stack[-1])

        self._tokenizer_stack.pop()
        return True

    async def _execute_with_recovery(self, num_attempts: int = 0) -> int:
        """Execute with error recovery."""
        try:
            num_attempts += 1
            if num_attempts > self._max_attempts:
                raise TooManyAttemptsError(
                    self.get_top_input_string(), num_attempts, self._max_attempts
                )
            await self._continue()
            return num_attempts
        except Exception as e:
            if not self._handle_error:
                raise
            await self._handle_error(e, self)
            return await self._execute_with_recovery(num_attempts)

    async def _continue(self) -> None:
        """Continue execution with current tokenizer."""
        await self._run_with_tokenizer(self._tokenizer_stack[-1])

    async def _run_with_tokenizer(self, tokenizer: Tokenizer) -> bool:
        """Execute tokens from a tokenizer."""
        while True:
            token = tokenizer.next_token()
            self._previous_token = token
            await self._handle_token(token)
            if token.type == TokenType.EOS:
                break
        return True

    # ======================
    # Module management

    def cur_module(self) -> Module:
        """Get the current module."""
        return self._module_stack[-1]

    def find_module(self, name: str) -> Module:
        """Find a registered module by name."""
        result = self._registered_modules.get(name)
        if result is None:
            raise UnknownModuleError(
                self.get_top_input_string(), name, self._string_location
            )
        return result

    def module_stack_push(self, module: Module) -> None:
        self._module_stack.append(module)

    def module_stack_pop(self) -> Module:
        return self._module_stack.pop()

    def register_module(self, module: Module) -> None:
        """Register a module with the interpreter."""
        self._registered_modules[module.name] = module
        module.set_interp(self)

    def use_modules(self, names: list[Any]) -> None:
        """Import modules into app module.

        If names is a list of strings, import each without prefix.
        If names is a list of [name, prefix] pairs, use specified prefix.
        """
        for name in names:
            module_name = name
            prefix = ""
            if isinstance(name, list):
                module_name = name[0]
                prefix = name[1]
            module = self.find_module(module_name)
            self.get_app_module().import_module(prefix, module, self)

    def import_module(self, module: Module, prefix: str = "") -> None:
        """Convenience method to register and use a module."""
        self.register_module(module)
        self.use_modules([[module.name, prefix]])

    def import_modules(self, modules: list[Module]) -> None:
        """Import multiple modules without prefixes."""
        for module in modules:
            self.import_module(module)

    async def run_module_code(self, module: Module) -> None:
        """Execute the forthic code of a module."""
        self.module_stack_push(module)
        try:
            module_location = CodeLocation(source=module.name)
            await self.run(module.forthic_code, module_location)
        except Exception as e:
            raise ModuleError(
                self.get_top_input_string(), module.name, e, self._string_location
            ) from e

        self.module_stack_pop()

    # ======================
    # Stack operations

    def stack_peek(self) -> Any:
        """Peek at top of stack."""
        top = self._stack[len(self._stack) - 1]
        result = top
        if isinstance(top, PositionedString):
            result = str(top)
        return result

    def stack_push(self, val: Any) -> None:
        """Push value onto stack."""
        self._stack.push(val)

    def stack_pop(self) -> Any:
        """Pop value from stack."""
        if len(self._stack) == 0:
            tokenizer = self.get_tokenizer() if self._tokenizer_stack else None
            location = tokenizer.get_token_location() if tokenizer else None
            raise StackUnderflowError(self.get_top_input_string(), location)

        result = self._stack.pop()

        # If we have a PositionedString, record the location
        self._string_location = None
        if isinstance(result, PositionedString):
            positioned_string = result
            result = str(positioned_string)
            self._string_location = positioned_string.location

        return result

    def get_stack(self) -> Stack:
        """Get the stack object."""
        return self._stack

    def set_stack(self, stack: Stack) -> None:
        """Set the stack object."""
        self._stack = stack

    # ======================
    # Literal handlers

    def _register_standard_literals(self) -> None:
        """Register standard literal handlers."""
        self._literal_handlers = [
            to_bool,  # TRUE, FALSE
            to_float,  # 3.14
            to_zoned_datetime(self._timezone),  # 2020-06-05T10:15:00Z
            to_literal_date(self._timezone),  # 2020-06-05, YYYY-MM-DD
            to_time,  # 9:00, 11:30 PM
            to_int,  # 42
        ]

    def register_literal_handler(self, handler: LiteralHandler) -> None:
        """Register a custom literal handler."""
        self._literal_handlers.append(handler)

    def unregister_literal_handler(self, handler: LiteralHandler) -> None:
        """Unregister a literal handler."""
        if handler in self._literal_handlers:
            self._literal_handlers.remove(handler)

    def find_literal_word(self, name: str) -> Word | None:
        """Try to parse string as a literal value."""
        for handler in self._literal_handlers:
            value = handler(name)
            if value is not None:
                return PushValueWord(name, value)
        return None

    # ======================
    # Find Word

    def find_word(self, name: str) -> Word:
        """Find a word by name.

        Checks module stack (dictionary words + variables), then literal handlers.
        """
        # 1. Check module stack
        result: Word | None = None
        for module in reversed(self._module_stack):
            result = module.find_word(name)
            if result:
                break

        # 2. Check literal handlers as fallback
        if result is None:
            result = self.find_literal_word(name)

        # 3. Throw error if still not found
        if result is None:
            raise UnknownWordError(
                self.get_top_input_string(), name, self.get_string_location()
            )

        return result

    # ======================
    # Profiling

    def start_profiling(self) -> None:
        """Start profiling word execution."""
        self._is_profiling = True
        self._word_counts = {}
        self._timestamps = []

    def count_word(self, word: Word) -> None:
        """Count word execution (for profiling)."""
        if not self._is_profiling:
            return
        name = word.name
        if name not in self._word_counts:
            self._word_counts[name] = 0
        self._word_counts[name] += 1

    def stop_profiling(self) -> None:
        """Stop profiling."""
        self._is_profiling = False

    def word_histogram(self) -> list[dict[str, Any]]:
        """Get word execution histogram."""
        items = [{"word": name, "count": count} for name, count in self._word_counts.items()]
        return sorted(items, key=lambda x: x["count"], reverse=True)

    def add_timestamp(self, label: str) -> None:
        """Add a profiling timestamp with label."""
        import time

        time_ms = time.time() * 1000
        self._timestamps.append({"label": label, "time_ms": time_ms})

    def profile_timestamps(self) -> list[dict[str, Any]]:
        """Get profiling timestamps."""
        return self._timestamps

    # ======================
    # Token handling

    async def _handle_token(self, token: Token) -> None:
        """Handle a single token."""
        if token.type == TokenType.STRING:
            await self._handle_string_token(token)
        elif token.type == TokenType.COMMENT:
            self._handle_comment_token(token)
        elif token.type == TokenType.START_ARRAY:
            await self._handle_start_array_token(token)
        elif token.type == TokenType.END_ARRAY:
            await self._handle_end_array_token(token)
        elif token.type == TokenType.START_MODULE:
            await self._handle_start_module_token(token)
        elif token.type == TokenType.END_MODULE:
            await self._handle_end_module_token(token)
        elif token.type == TokenType.START_DEF:
            self._handle_start_definition_token(token)
        elif token.type == TokenType.START_MEMO:
            self._handle_start_memo_token(token)
        elif token.type == TokenType.END_DEF:
            self._handle_end_definition_token(token)
        elif token.type == TokenType.DOT_SYMBOL:
            await self._handle_dot_symbol_token(token)
        elif token.type == TokenType.WORD:
            await self._handle_word_token(token)
        elif token.type == TokenType.EOS:
            if self._is_compiling:
                location = self._previous_token.location if self._previous_token else None
                raise MissingSemicolonError(self.get_top_input_string(), location)
        else:
            raise UnknownTokenError(
                self.get_top_input_string(), token.string, self._string_location
            )

    async def _handle_string_token(self, token: Token) -> None:
        value = PositionedString(token.string, token.location)
        await self._handle_word(PushValueWord("<string>", value))

    async def _handle_dot_symbol_token(self, token: Token) -> None:
        value = PositionedString(token.string, token.location)
        await self._handle_word(PushValueWord("<dot-symbol>", value))

    async def _handle_start_module_token(self, token: Token) -> None:
        """Start/end module tokens are IMMEDIATE and also compiled."""
        word = StartModuleWord(token.string)
        if self._is_compiling and self._cur_definition:
            self._cur_definition.add_word(word)
        self.count_word(word)
        await word.execute(self)

    async def _handle_end_module_token(self, token: Token) -> None:
        word = EndModuleWord()
        if self._is_compiling and self._cur_definition:
            self._cur_definition.add_word(word)
        self.count_word(word)
        await word.execute(self)

    async def _handle_start_array_token(self, token: Token) -> None:
        await self._handle_word(PushValueWord("<start_array_token>", token))

    async def _handle_end_array_token(self, token: Token) -> None:
        await self._handle_word(EndArrayWord())

    def _handle_comment_token(self, token: Token) -> None:
        """Comments are ignored."""
        pass

    def _handle_start_definition_token(self, token: Token) -> None:
        if self._is_compiling:
            location = self._previous_token.location if self._previous_token else None
            raise MissingSemicolonError(self.get_top_input_string(), location)
        self._cur_definition = DefinitionWord(token.string)
        self._is_compiling = True
        self._is_memo_definition = False

    def _handle_start_memo_token(self, token: Token) -> None:
        if self._is_compiling:
            location = self._previous_token.location if self._previous_token else None
            raise MissingSemicolonError(self.get_top_input_string(), location)
        self._cur_definition = DefinitionWord(token.string)
        self._is_compiling = True
        self._is_memo_definition = True

    def _handle_end_definition_token(self, token: Token) -> None:
        if not self._is_compiling or self._cur_definition is None:
            raise ExtraSemicolonError(self.get_top_input_string(), token.location)

        if self._is_memo_definition:
            self.cur_module().add_memo_words(self._cur_definition)
        else:
            self.cur_module().add_word(self._cur_definition)
        self._is_compiling = False

    async def _handle_word_token(self, token: Token) -> None:
        word = self.find_word(token.string)
        await self._handle_word(word, token.location)

    async def _handle_word(
        self, word: Word, location: CodeLocation | None = None
    ) -> None:
        """Handle a word (either compile or execute)."""
        if self._is_compiling and self._cur_definition:
            word.set_location(location)
            self._cur_definition.add_word(word)
        else:
            self.count_word(word)
            await word.execute(self)


def dup_interpreter(interp: Interpreter) -> Interpreter:
    """Create a duplicate of an interpreter.

    Copies app module, module stack, and stack. Shares registered modules.
    """
    # Create new interpreter of same type
    constructor = type(interp)
    result_interp = constructor([], interp.get_timezone())

    # Copy app module with prefixes restored
    result_interp._app_module = interp._app_module.copy(result_interp)
    result_interp._module_stack = [result_interp._app_module]

    # Duplicate stack
    result_interp._stack = interp._stack.dup()

    # Share registered modules reference
    result_interp._registered_modules = interp._registered_modules

    # Copy error handler if present
    if interp._handle_error:
        result_interp._handle_error = interp._handle_error

    return result_interp


class StandardInterpreter(Interpreter):
    """Interpreter with standard library modules pre-loaded.

    Automatically imports Core, Math, Boolean, String, Array, Record, JSON, and DateTime modules.
    """

    def __init__(self, modules: list[Module] | None = None, timezone: str | ZoneInfo = "UTC"):
        # Don't pass modules to super - we'll import them after stdlib
        super().__init__([], timezone)

        # Import standard library modules FIRST (checked last during lookup)
        # This allows user modules to shadow stdlib words
        self._import_standard_library()

        # Import user modules AFTER stdlib (checked first during lookup)
        if modules:
            self.import_modules(modules)

    def _import_standard_library(self) -> None:
        """Import all standard library modules without prefixes."""
        from .modules import (
            ArrayModule,
            BooleanModule,
            CoreModule,
            DateTimeModule,
            JSONModule,
            MathModule,
            RecordModule,
            StringModule,
        )

        stdlib = [
            CoreModule(),
            ArrayModule(),
            RecordModule(),
            StringModule(),
            MathModule(),
            BooleanModule(),
            JSONModule(),
            DateTimeModule(),
        ]

        # Import unprefixed at the BOTTOM of module stack
        # This ensures they're checked LAST during find_word()
        for module in stdlib:
            self.import_module(module._module, "")
