"""WordOptions - Type-safe options container for module words.

Overview:
WordOptions provides a structured way for Forthic words to accept optional
configuration parameters without requiring fixed parameter positions. This
enables flexible, extensible APIs similar to keyword arguments in other languages.

Usage in Forthic:
    [.option_name value ...] ~> WORD

The ~> operator takes an options array and a word, passing the options as
an additional parameter to words that support them.

Example in Forthic code:
    [1 2 3] '2 *' [.with_key TRUE] ~> MAP
    [10 20 30] [.comparator "-1 *"] ~> SORT
    [[[1 2]]] [.depth 1] ~> FLATTEN

Implementation in Module Words:
Words declare options support by adding an options parameter with type dict[str, Any]:

    @Word("( items:any[] forthic:string [options:WordOptions] -- result:any )")
    async def MAP(self, items: list, forthic: str, options: dict[str, Any]) -> list:
        with_key = options.get('with_key')
        push_error = options.get('push_error')
        # ... use options to modify behavior

The @Word decorator automatically:
1. Checks if the top stack item is a WordOptions instance
2. Converts it to a plain dict if present
3. Passes an empty {} if no options provided

Common Patterns:
- Boolean flags: options.get('with_key')
- Numeric values: options.get('depth')
- String values: options.get('comparator')
- Multiple options: All accessed from same options dict

Internal Representation:
Created from flat array: [.key1 val1 .key2 val2]
Stored as dict internally for efficient lookup

Note: Dot-symbols in Forthic have the leading '.' already stripped,
so keys come in as "key1", "key2", etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .interpreter import Interpreter


class WordOptions:
    """Options container for Forthic words."""

    def __init__(self, flat_array: list[Any]):
        if not isinstance(flat_array, list):
            raise TypeError("Options must be an array")

        if len(flat_array) % 2 != 0:
            raise ValueError(
                f"Options must be key-value pairs (even length). Got {len(flat_array)} elements"
            )

        self._options: dict[str, Any] = {}

        for i in range(0, len(flat_array), 2):
            key = flat_array[i]
            value = flat_array[i + 1]

            # Key should be a string (dot-symbol with . already stripped)
            if not isinstance(key, str):
                raise TypeError(f"Option key must be a string (dot-symbol). Got: {type(key)}")

            self._options[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get option value with optional default."""
        return self._options.get(key, default)

    def has(self, key: str) -> bool:
        """Check if option exists."""
        return key in self._options

    def to_dict(self) -> dict[str, Any]:
        """Get all options as plain dict."""
        return self._options.copy()

    def keys(self) -> list[str]:
        """Get all option keys."""
        return list(self._options.keys())

    def __str__(self) -> str:
        """For debugging/display."""
        pairs = " ".join(f".{k} {v!r}" for k, v in self._options.items())
        return f"<WordOptions: {pairs}>"

    def __repr__(self) -> str:
        return self.__str__()


def pop_options_if_present(interp: Interpreter) -> dict[str, Any]:
    """Helper for words to check if top of stack is WordOptions and pop it if present.

    Returns empty dict if not present.
    """
    if len(interp.get_stack()) == 0:
        return {}

    top = interp.stack_peek()
    if isinstance(top, WordOptions):
        opts = interp.stack_pop()
        return opts.to_dict()

    return {}
