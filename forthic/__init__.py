"""Forthic - A stack-based, concatenative programming language."""

from .decorators import (
    DecoratedModule,
    DirectWord,
    register_module_doc,
)
from .decorators import (
    Word as WordDecorator,
)
from .errors import (
    CodeLocationData,
    ExtraSemicolonError,
    ForthicError,
    IntentionalStopError,
    InvalidInputPositionError,
    InvalidVariableNameError,
    InvalidWordNameError,
    MissingSemicolonError,
    ModuleError,
    StackUnderflowError,
    TooManyAttemptsError,
    UnknownModuleError,
    UnknownTokenError,
    UnknownWordError,
    UnterminatedStringError,
    WordExecutionError,
)
from .interpreter import Interpreter, StandardInterpreter, dup_interpreter
from .literals import LiteralHandler, to_bool, to_float, to_int
from .module import (
    DefinitionWord,
    ExecuteWord,
    Module,
    ModuleMemoBangAtWord,
    ModuleMemoBangWord,
    ModuleMemoWord,
    PushValueWord,
    Stack,
    Variable,
    Word,
    WordHandler,
)
from .tokenizer import (
    CodeLocation,
    PositionedString,
    Token,
    Tokenizer,
    TokenType,
)
from .word_options import WordOptions, pop_options_if_present

__version__ = "0.1.0"

__all__ = [
    # Core
    "Interpreter",
    "StandardInterpreter",
    "dup_interpreter",
    # Decorators
    "WordDecorator",
    "DirectWord",
    "DecoratedModule",
    "register_module_doc",
    # Module system
    "Module",
    "Word",
    "PushValueWord",
    "DefinitionWord",
    "ExecuteWord",
    "ModuleMemoWord",
    "ModuleMemoBangWord",
    "ModuleMemoBangAtWord",
    "Variable",
    "Stack",
    "WordHandler",
    # Tokenizer
    "Tokenizer",
    "Token",
    "TokenType",
    "CodeLocation",
    "PositionedString",
    # Literals
    "LiteralHandler",
    "to_bool",
    "to_int",
    "to_float",
    # Errors
    "ForthicError",
    "UnknownWordError",
    "WordExecutionError",
    "MissingSemicolonError",
    "ExtraSemicolonError",
    "StackUnderflowError",
    "InvalidVariableNameError",
    "UnknownModuleError",
    "InvalidInputPositionError",
    "InvalidWordNameError",
    "UnterminatedStringError",
    "UnknownTokenError",
    "ModuleError",
    "TooManyAttemptsError",
    "IntentionalStopError",
    "CodeLocationData",
    # Word Options
    "WordOptions",
    "pop_options_if_present",
]
