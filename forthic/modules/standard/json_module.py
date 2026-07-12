"""JSON module - JSON serialization and deserialization.

Provides operations for converting between Forthic data structures and JSON.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...utils import to_compact_json


class JSONModule(DecoratedModule):
    """JSON serialization, parsing, and formatting operations."""

    def __init__(self) -> None:
        super().__init__("json")
        register_module_doc(
            JSONModule,
            """
JSON serialization, parsing, and formatting operations.

## Categories
- Conversion: >JSON, JSON>
- Formatting: JSON-PRETTIFY

## Examples
{name: "Alice", age: 30} >JSON
'{"name":"Alice"}' JSON>
'{"a":1}' JSON-PRETTIFY
            """,
        )

    @WordDecorator("( object:any -- json:string )", "Convert object to JSON string", ">JSON")
    async def to_JSON(self, obj: Any) -> str:
        # Compact like JSON.stringify (no spaces), insertion-ordered keys,
        # temporal values as their ISO forms
        return to_compact_json(obj)

    @ForthicDirectWord("( json:string -- object:any )", "Parse JSON string to object", "JSON>")
    async def from_JSON(self, interp: Interpreter) -> None:
        json_str = interp.stack_pop()
        if not json_str or json_str.strip() == "":
            interp.stack_push(None)
            return
        result = json.loads(json_str)
        interp.stack_push(result)

    @WordDecorator("( json:string -- pretty:string )", "Format JSON with 2-space indentation", "JSON-PRETTIFY")
    async def JSON_PRETTIFY(self, json_str: str) -> str:
        if not json_str or json_str.strip() == "":
            return ""
        obj = json.loads(json_str)
        return json.dumps(obj, indent=2)
