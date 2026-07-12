"""String module - String manipulation operations.

Provides string transformation, searching, and formatting functions.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, unquote

if TYPE_CHECKING:
    pass

from ...decorators import DecoratedModule, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...utils import to_forthic_string


class StringModule(DecoratedModule):
    """String manipulation and processing operations with regex and URL encoding support."""

    def __init__(self) -> None:
        super().__init__("string")
        register_module_doc(
            StringModule,
            """
String manipulation and processing operations with regex and URL encoding support.

## Categories
- Conversion: >STR, STR-LENGTH, URL-ENCODE, URL-DECODE
- Transform: LOWERCASE, UPPERCASE, STRIP, ASCII
- Split/Join: SPLIT, JOIN, CONCAT
- Pattern: REPLACE, RE_MATCH, RE_MATCH_ALL, RE_MATCH_GROUP
- Constants: /N, /R, /T

## Examples
"hello" "world" CONCAT
["a" "b" "c"] CONCAT
"hello world" " " SPLIT
["hello" "world"] " " JOIN
"Hello" LOWERCASE
"test@example.com" "(@.+)" RE-MATCH 1 RE-MATCH-GROUP
            """,
        )

    # ==================
    # Concatenation
    # ==================

    @WordDecorator(
        "( strings:string[] -- result:string )",
        "Concatenate an array of strings into one string. For two strings: write [s1 s2] CONCAT. For arrays of arrays, use FLATTEN.",
        "CONCAT",
    )
    async def CONCAT(self, strings: Any) -> str:
        if not isinstance(strings, list):
            raise ValueError("CONCAT requires an array of strings. Wrap two strings as [s1 s2] CONCAT.")
        return "".join("" if s is None else str(s) for s in strings)

    @WordDecorator(
        "( str:string -- length:number )",
        "Length of a string in characters (0 if null).",
        "STR-LENGTH",
    )
    async def STR_LENGTH(self, string: Any) -> int:
        if string is None:
            return 0
        if not isinstance(string, str):
            raise ValueError("STR-LENGTH requires a string. For arrays/records, use LENGTH.")
        return len(string)

    # ==================
    # Conversion
    # ==================

    @WordDecorator(
        "( item:any -- string:string )",
        "Convert item to string (JS semantics: null -> '', arrays comma-join, records -> compact JSON)",
        ">STR",
    )
    async def to_STR(self, item: Any) -> str:
        return to_forthic_string(item)

    # ==================
    # Split/Join
    # ==================

    @WordDecorator("( string:string sep:string -- items:any[] )", "Split string by separator")
    async def SPLIT(self, string: str, sep: str) -> list[str]:
        if not string:
            string = ""
        return string.split(sep)

    @WordDecorator("( strings:string[] sep:string -- result:string )", "Join strings with separator")
    async def JOIN(self, strings: list, sep: str) -> str:
        if not strings:
            strings = []
        return sep.join(str(s) for s in strings)

    # ==================
    # Constants
    # ==================

    @WordDecorator("( -- char:string )", "Newline character", "/N")
    async def slash_N(self) -> str:
        return "\n"

    @WordDecorator("( -- char:string )", "Carriage return character", "/R")
    async def slash_R(self) -> str:
        return "\r"

    @WordDecorator("( -- char:string )", "Tab character", "/T")
    async def slash_T(self) -> str:
        return "\t"

    # ==================
    # Transform
    # ==================

    @WordDecorator("( string:string -- result:string )", "Convert string to lowercase")
    async def LOWERCASE(self, string: str) -> str:
        result = ""
        if string:
            result = string.lower()
        return result

    @WordDecorator("( string:string -- result:string )", "Convert string to uppercase")
    async def UPPERCASE(self, string: str) -> str:
        result = ""
        if string:
            result = string.upper()
        return result

    @WordDecorator("( string:string -- result:string )", "Keep only ASCII characters (< 256)")
    async def ASCII(self, string: str) -> str:
        if not string:
            string = ""

        result = ""
        for ch in string:
            if ord(ch) < 256:
                result += ch
        return result

    @WordDecorator("( string:string -- result:string )", "Trim whitespace from string")
    async def STRIP(self, string: str) -> str:
        result = string
        if result:
            result = result.strip()
        return result

    # ==================
    # Pattern/Replace
    # ==================

    @WordDecorator(
        "( string:string text:string replace:string -- result:string )",
        "Replace all occurrences of text with replace",
    )
    async def REPLACE(self, string: str, text: str, replace: str) -> str:
        result = string
        if string:
            pattern = re.compile(re.escape(text))
            result = pattern.sub(replace, string)
        return result

    @WordDecorator("( string:string pattern:string -- match:any )", "Match string against regex pattern", "RE-MATCH")
    async def RE_MATCH(self, string: str, pattern: str) -> Any:
        re_pattern = re.compile(pattern)
        result: Any = False
        if string is not None:
            match = re_pattern.search(string)
            if match:
                result = list(match.groups())
                result.insert(0, match.group(0))  # Add full match at index 0
        return result

    @WordDecorator("( string:string pattern:string -- matches:any[] )", "Find all regex matches in string", "RE-MATCH-ALL")
    async def RE_MATCH_ALL(self, string: str, pattern: str) -> list:
        re_pattern = re.compile(pattern)
        matches: list = []
        if string is not None:
            matches = [m.group(1) for m in re_pattern.finditer(string)]
        return matches

    @WordDecorator("( match:any num:number -- result:any )", "Get capture group from regex match", "RE-MATCH-GROUP")
    async def RE_MATCH_GROUP(self, match: Any, num: int) -> Any:
        result = None
        if match:
            result = match[num]
        return result

    # ==================
    # URL Encoding
    # ==================

    @WordDecorator("( str:string -- encoded:string )", "URL encode string", "URL-ENCODE")
    async def URL_ENCODE(self, string: str) -> str:
        result = ""
        if string:
            result = quote(string)
        return result

    @WordDecorator("( urlencoded:string -- decoded:string )", "URL decode string", "URL-DECODE")
    async def URL_DECODE(self, urlencoded: str) -> str:
        result = ""
        if urlencoded:
            result = unquote(urlencoded)
        return result
