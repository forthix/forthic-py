"""Word decorators for Forthic modules.

Provides @ForthicWord and @ForthicDirectWord decorators for creating module words with automatic
stack marshalling and documentation support.
"""

from __future__ import annotations

import re
import weakref
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..interpreter import Interpreter

# Metadata storage using WeakKeyDictionary
_word_metadata: weakref.WeakKeyDictionary[type, dict[str, WordMetadata]] = (
    weakref.WeakKeyDictionary()
)
_direct_word_metadata: weakref.WeakKeyDictionary[type, dict[str, DirectWordMetadata]] = (
    weakref.WeakKeyDictionary()
)
_module_metadata: weakref.WeakKeyDictionary[type, ModuleMetadata] = (
    weakref.WeakKeyDictionary()
)


@dataclass
class WordMetadata:
    """Metadata for a @ForthicWord decorated method."""

    stack_effect: str
    description: str
    word_name: str
    method_name: str
    input_count: int
    has_options: bool


@dataclass
class DirectWordMetadata:
    """Metadata for a @ForthicDirectWord decorated method."""

    stack_effect: str
    description: str
    word_name: str
    method_name: str


@dataclass
class ModuleMetadata:
    """Module-level documentation metadata."""

    description: str
    categories: list[dict[str, str]]  # [{"name": str, "words": str}]
    options_info: str | None
    examples: list[str]


def parse_stack_notation(stack_effect: str) -> tuple[int, bool]:
    """Parse Forthic stack notation to extract input count and optional WordOptions.

    Examples:
        "( a:any b:any -- sum:number )" → (2, False)
        "( -- value:any )" → (0, False)
        "( items:any[] -- first:any )" → (1, False)
        "( array:any[] [options:WordOptions] -- flat:any[] )" → (1, True)

    Returns:
        Tuple of (input_count, has_options)
    """
    trimmed = stack_effect.strip()
    if not (trimmed.startswith("(") and trimmed.endswith(")")):
        raise ValueError(f"Stack effect must be wrapped in parentheses: {stack_effect}")

    content = trimmed[1:-1].strip()
    parts = content.split("--")
    if len(parts) != 2:
        raise ValueError(f"Invalid stack notation: {stack_effect}")

    input_part = parts[0].strip()
    if input_part == "":
        return (0, False)

    # Check for optional [options:WordOptions] parameter
    has_options = bool(re.search(r"\[options:WordOptions\]", input_part))

    # Remove optional parameter from counting
    without_optional = re.sub(r"\[options:WordOptions\]", "", input_part).strip()

    # Split by whitespace, count non-empty tokens
    inputs = [s for s in without_optional.split() if s]

    return (len(inputs), has_options)


def parse_module_doc_string(doc_string: str) -> ModuleMetadata:
    """Parse markdown-formatted module documentation string.

    Expected format:
        Brief description

        ## Categories
        - Category Name: WORD1, WORD2, WORD3
        - Another Category: WORD4, WORD5

        ## Options
        Multi-line text describing the options system

        ## Examples
        example code line 1
        example code line 2
    """
    lines = [line.strip() for line in doc_string.split("\n") if line.strip()]

    result = ModuleMetadata(
        description="", categories=[], options_info=None, examples=[]
    )

    current_section: str = "description"
    options_lines: list[str] = []

    for line in lines:
        # Check for section headers
        if line.startswith("## Categories"):
            current_section = "categories"
            continue
        elif line.startswith("## Options"):
            current_section = "options"
            continue
        elif line.startswith("## Examples"):
            current_section = "examples"
            continue

        # Process content based on current section
        if current_section == "description":
            if result.description:
                result.description += " " + line
            else:
                result.description = line
        elif current_section == "categories":
            # Parse "- Category Name: WORD1, WORD2, WORD3"
            match = re.match(r"^-\s*([^:]+):\s*(.+)$", line)
            if match:
                result.categories.append({"name": match[1].strip(), "words": match[2].strip()})
        elif current_section == "options":
            options_lines.append(line)
        elif current_section == "examples":
            result.examples.append(line)

    # Join options lines into a single string
    if options_lines:
        result.options_info = "\n".join(options_lines)

    return result


def ForthicWord(
    stack_effect: str, description: str = "", custom_word_name: str | None = None
) -> Callable:
    """Decorator that auto-registers word and handles stack marshalling.

    Args:
        stack_effect: Forthic stack notation (e.g., "( a:any b:any -- sum:number )")
        description: Human-readable description for docs
        custom_word_name: Optional custom word name (defaults to method name)

    Example:
        @ForthicWord("( a:number b:number -- sum:number )", "Adds two numbers")
        async def ADD(self, a: int, b: int) -> int:
            return a + b

        @ForthicWord("( rec:any field:any -- value:any )", "Get value from record", "REC@")
        async def REC_at(self, rec: Any, field: Any) -> Any:
            # Word name will be "REC@" instead of "REC_at"
            return rec.get(field)
    """

    def decorator(method: Callable) -> Callable:
        input_count, has_options = parse_stack_notation(stack_effect)
        word_name = custom_word_name or method.__name__

        # Store metadata at decoration time by attaching to the method
        metadata = WordMetadata(
            stack_effect=stack_effect,
            description=description,
            word_name=word_name,
            method_name=method.__name__,
            input_count=input_count,
            has_options=has_options,
        )

        # Replace method with wrapper that handles stack marshalling
        @wraps(method)
        async def wrapper(self: Any, interp: Interpreter) -> None:
            from ..word_options import WordOptions

            inputs: list[Any] = []

            # Check for optional WordOptions FIRST (before popping regular args)
            options: dict[str, Any] | None = None
            if has_options and len(interp.get_stack()) > 0:
                top = interp.stack_peek()
                if isinstance(top, WordOptions):
                    opts = interp.stack_pop()
                    options = opts.to_dict()

            # Pop required inputs in reverse order (stack is LIFO)
            for _ in range(input_count):
                inputs.insert(0, interp.stack_pop())

            # Add options as last parameter if method expects it
            if has_options:
                inputs.append(options or {})

            # Call original method with popped inputs (+ options if present)
            result = await method(self, *inputs)

            # Push result if not None
            if result is not None:
                interp.stack_push(result)

        # Attach metadata to wrapper for later retrieval
        wrapper._forthic_word_metadata = metadata  # type: ignore

        return wrapper

    return decorator


def ForthicDirectWord(
    stack_effect: str, description: str = "", custom_word_name: str | None = None
) -> Callable:
    """Decorator that auto-registers word but does NOT handle stack marshalling.

    Use this for words that need direct interpreter access to manually manipulate the stack.
    Word name defaults to method name, but can be overridden.

    Args:
        stack_effect: Forthic stack notation (e.g., "( item:any forthic:string n:number -- )")
        description: Human-readable description for docs
        custom_word_name: Optional custom word name (defaults to method name)

    Example:
        @ForthicDirectWord("( item:any forthic:str num:int -- )", "Repeat execution num_times", "<REPEAT")
        async def l_REPEAT(self, interp: Interpreter) -> None:
            num = interp.stack_pop()
            forthic = interp.stack_pop()
            # ... manual stack manipulation
    """

    def decorator(method: Callable) -> Callable:
        word_name = custom_word_name or method.__name__

        # Store metadata at decoration time by attaching to the method
        metadata = DirectWordMetadata(
            stack_effect=stack_effect,
            description=description,
            word_name=word_name,
            method_name=method.__name__,
        )

        # Wrap to ensure metadata storage
        @wraps(method)
        async def wrapper(self: Any, interp: Interpreter) -> None:
            return await method(self, interp)

        # Attach metadata to wrapper for later retrieval
        wrapper._forthic_direct_word_metadata = metadata  # type: ignore

        return wrapper

    return decorator


def register_module_doc(constructor: type, doc_string: str) -> None:
    """Register module documentation.

    Call this as a class-level initialization:
        class ArrayModule(DecoratedModule):
            def __init__(self):
                super().__init__("array")
                register_module_doc(ArrayModule, '''
                  Array and collection operations
                  ## Categories
                  - Access: NTH, LAST, SLICE
                ''')
    """
    parsed = parse_module_doc_string(doc_string)
    _module_metadata[constructor] = parsed


class DecoratedModule:
    """Base class for modules using @ForthicWord decorator.

    Automatically registers all @ForthicWord decorated methods when interpreter is set.
    """

    def __init__(self, name: str):
        from ..module import Module

        # Initialize as a Module
        self._module = Module(name)

        # Pre-populate metadata for this class
        self._populate_metadata()

        # Override the module's set_interp to trigger word registration
        original_set_interp = self._module.set_interp

        def set_interp_with_registration(interp: Interpreter) -> None:
            original_set_interp(interp)
            self._register_decorated_words()

        self._module.set_interp = set_interp_with_registration  # type: ignore

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped Module."""
        return getattr(self._module, name)

    def set_interp(self, interp: Interpreter) -> None:
        """Set interpreter and register decorated words."""
        self._module.set_interp(interp)
        self._register_decorated_words()

    def _populate_metadata(self) -> None:
        """Populate metadata by inspecting decorated methods."""
        cls = type(self)

        # Initialize metadata dictionaries for this class
        if cls not in _word_metadata:
            _word_metadata[cls] = {}
        if cls not in _direct_word_metadata:
            _direct_word_metadata[cls] = {}

        # Scan for decorated methods and extract their metadata
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self, attr_name)

            # Check if this is a @ForthicWord decorated method
            if callable(attr) and hasattr(attr, "_forthic_word_metadata"):
                metadata = attr._forthic_word_metadata
                _word_metadata[cls][metadata.method_name] = metadata

            # Check if this is a @ForthicDirectWord decorated method
            elif callable(attr) and hasattr(attr, "_forthic_direct_word_metadata"):
                metadata = attr._forthic_direct_word_metadata
                _direct_word_metadata[cls][metadata.method_name] = metadata

    def _register_decorated_words(self) -> None:
        """Register all decorated words with the module."""
        # Register @ForthicWord decorated methods
        cls = type(self)
        if cls in _word_metadata:
            for method_name, metadata in _word_metadata[cls].items():
                # Get the wrapped method (already modified by decorator)
                method = getattr(self, method_name)
                # Register as exportable word
                self._module.add_module_word(metadata.word_name, method)

        # Register @ForthicDirectWord decorated methods
        if cls in _direct_word_metadata:
            for method_name, metadata in _direct_word_metadata[cls].items():
                # Get the method
                method = getattr(self, method_name)
                # Register as exportable word
                self._module.add_module_word(metadata.word_name, method)

    def get_word_docs(self) -> list[dict[str, str]]:
        """Get documentation for all words in this module.

        Returns:
            List of {name, stackEffect, description} dicts
        """
        docs: list[dict[str, str]] = []

        cls = type(self)

        # Get @ForthicWord decorated methods
        if cls in _word_metadata:
            for metadata in _word_metadata[cls].values():
                docs.append(
                    {
                        "name": metadata.word_name,
                        "stackEffect": metadata.stack_effect,
                        "description": metadata.description,
                    }
                )

        # Get @ForthicDirectWord decorated methods
        if cls in _direct_word_metadata:
            for metadata in _direct_word_metadata[cls].values():
                docs.append(
                    {
                        "name": metadata.word_name,
                        "stackEffect": metadata.stack_effect,
                        "description": metadata.description,
                    }
                )

        return docs

    def get_module_metadata(self) -> dict[str, Any] | None:
        """Get module-level documentation.

        Returns:
            Dict with name, description, categories, options, and examples
        """
        cls = type(self)
        parsed = _module_metadata.get(cls)
        if not parsed:
            return None

        return {
            "name": self._module.get_name(),
            "description": parsed.description,
            "categories": parsed.categories,
            "optionsInfo": parsed.options_info,
            "examples": parsed.examples,
        }
