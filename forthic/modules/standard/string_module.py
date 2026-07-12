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
- Slice: SUBSTR, SPLICE
- Predicates: STARTS-WITH?, ENDS-WITH?, RE-MATCH?
- Trim: TRIM-PREFIX, TRIM-SUFFIX
- Shell-flavored: LINES, UNLINES, GREP, GREP-V, SED, CUT
- Transform: LOWERCASE, UPPERCASE, STRIP, ASCII
- Split/Join: SPLIT, JOIN, CONCAT
- Pattern: REPLACE, RE-REPLACE, RE-MATCH, RE-MATCH-ALL, RE-MATCH?
- Constants: /N, /R, /T

## Note
Regex patterns (RE-*, GREP, SED) are compiled and run as-is. A pathological
pattern can backtrack catastrophically (ReDoS) and block execution, so patterns
must come from a trusted source, not untrusted input.

## Examples
["hello" " " "world"] CONCAT
"hello world" STR-LENGTH
"hello world" " " SPLIT
["hello" "world"] " " JOIN
"Hello" LOWERCASE
"test@example.com" "(@.+)" RE-MATCH
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

    @staticmethod
    def _compile_regex(pattern: str, flags: int = 0) -> re.Pattern:
        """Compile a regex with a clean error (ts throws a raw SyntaxError)."""
        try:
            return re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex {pattern!r}: {e}") from e

    @staticmethod
    def _normalize_js_replacement(replace: str) -> str:
        """Normalize JS replacement syntax to Python's re.sub template:
        $$ -> literal $, $& -> whole match, $n -> group n (safe even when
        followed by a word character)."""
        LITERAL_DOLLAR = "\x00LITERAL_DOLLAR\x00"
        result = replace.replace("\\", "\\\\")
        result = result.replace("$$", LITERAL_DOLLAR)
        result = result.replace("$&", "\\g<0>")
        result = re.sub(r"\$(\d+)", r"\\g<\1>", result)
        return result.replace(LITERAL_DOLLAR, "$")

    @WordDecorator(
        "( str:string start:number end:number -- substring:string )",
        "Substring of str from start (inclusive) to end (exclusive), by character (code point) index. Indices clamp like String.slice (negatives count from the end; crossed range is empty).",
        "SUBSTR",
    )
    async def SUBSTR(self, string: Any, start: int, end: int) -> str:
        if string is None:
            return ""
        if not isinstance(string, str):
            raise ValueError("SUBSTR requires a string. For arrays/records, use SLICE.")
        return string[self._clamp_index(start, len(string)):self._clamp_index(end, len(string))]

    @staticmethod
    def _clamp_index(index: int, length: int) -> int:
        """JS String.slice index normalization: negatives from the end, clamped to [0, length]."""
        if index < 0:
            return max(0, length + index)
        return min(index, length)

    @WordDecorator(
        "( str:string start:number end:number newval:string -- result:string )",
        "Replace the substring [start, end) of str with newval and return the result (a splice). Char (code point) indices.",
        "SPLICE",
    )
    async def SPLICE(self, string: Any, start: int, end: int, newval: Any) -> str:
        if string is None:
            string = ""
        if not isinstance(string, str):
            raise ValueError("SPLICE requires a string.")
        ins = "" if newval is None else to_forthic_string(newval)
        length = len(string)
        return string[: self._clamp_index(start, length)] + ins + string[self._clamp_index(end, length):]

    @WordDecorator(
        "( str:string prefix:string -- bool:boolean )",
        "Returns true if str begins with prefix.",
        "STARTS-WITH?",
    )
    async def STARTS_WITH_q(self, string: Any, prefix: Any) -> bool:
        if not isinstance(string, str) or not isinstance(prefix, str):
            return False
        return string.startswith(prefix)

    @WordDecorator(
        "( str:string suffix:string -- bool:boolean )",
        "Returns true if str ends with suffix.",
        "ENDS-WITH?",
    )
    async def ENDS_WITH_q(self, string: Any, suffix: Any) -> bool:
        if not isinstance(string, str) or not isinstance(suffix, str):
            return False
        return string.endswith(suffix)

    @WordDecorator(
        "( str:string prefix:string -- result:string )",
        "Strip prefix from start of str if present (at most one occurrence; otherwise unchanged).",
        "TRIM-PREFIX",
    )
    async def TRIM_PREFIX(self, string: Any, prefix: Any) -> Any:
        if not isinstance(string, str):
            return string
        if not isinstance(prefix, str) or len(prefix) == 0:
            return string
        return string[len(prefix):] if string.startswith(prefix) else string

    @WordDecorator(
        "( str:string suffix:string -- result:string )",
        "Strip suffix from end of str if present (at most one occurrence; otherwise unchanged).",
        "TRIM-SUFFIX",
    )
    async def TRIM_SUFFIX(self, string: Any, suffix: Any) -> Any:
        if not isinstance(string, str):
            return string
        if not isinstance(suffix, str) or len(suffix) == 0:
            return string
        return string[: len(string) - len(suffix)] if string.endswith(suffix) else string

    @WordDecorator(
        "( str:string pattern:string -- bool:boolean )",
        "Returns true if str matches the regex pattern. Predicate-only — does not return the match. (jq's `test`.)",
        "RE-MATCH?",
    )
    async def RE_MATCH_q(self, string: Any, pattern: Any) -> bool:
        if not isinstance(string, str) or not isinstance(pattern, str):
            return False
        return self._compile_regex(pattern).search(string) is not None

    @WordDecorator(
        "( string:string pattern:string replace:string -- result:string )",
        "Replace all regex matches of pattern with replace (JS $n/$&/$$ backrefs supported). For literal replacement use REPLACE.",
        "RE-REPLACE",
    )
    async def RE_REPLACE(self, string: Any, pattern: Any, replace: Any) -> Any:
        if string is None:
            return None
        if pattern is None:
            return string
        template = self._normalize_js_replacement("" if replace is None else str(replace))
        return self._compile_regex(pattern).sub(template, string)

    @WordDecorator(
        "( str:string -- lines:string[] )",
        "Split string on newline. Equivalent to /N SPLIT.",
        "LINES",
    )
    async def LINES(self, string: Any) -> list:
        if not isinstance(string, str):
            return []
        return string.split("\n")

    @WordDecorator(
        "( lines:string[] -- str:string )",
        "Join an array of lines with newlines (null elements render empty; non-strings stringify). Equivalent to /N JOIN.",
        "UNLINES",
    )
    async def UNLINES(self, lines: Any) -> str:
        if not isinstance(lines, list):
            return ""
        return "\n".join(to_forthic_string(v) for v in lines)

    @WordDecorator(
        "( strings:string[] pattern:string -- matches:string[] )",
        "Keep only strings matching the regex pattern (bash grep). Non-string elements are dropped.",
        "GREP",
    )
    async def GREP(self, strings: Any, pattern: Any) -> list:
        if not isinstance(strings, list):
            return []
        if not isinstance(pattern, str):
            return []
        regex = self._compile_regex(pattern)
        return [v for v in strings if isinstance(v, str) and regex.search(v)]

    @WordDecorator(
        "( strings:string[] pattern:string -- non_matches:string[] )",
        "Keep only elements NOT matching the regex pattern (bash grep -v). Deliberate asymmetry: keeps non-strings.",
        "GREP-V",
    )
    async def GREP_V(self, strings: Any, pattern: Any) -> Any:
        if not isinstance(strings, list):
            return []
        if not isinstance(pattern, str):
            return strings
        regex = self._compile_regex(pattern)
        return [v for v in strings if not isinstance(v, str) or not regex.search(v)]

    @WordDecorator(
        "( strings:string[] pattern:string repl:string -- strings:string[] )",
        "Apply RE-REPLACE to each string in the array (bash sed s/pattern/repl/g). Non-strings pass through.",
        "SED",
    )
    async def SED(self, strings: Any, pattern: Any, repl: Any) -> Any:
        if not isinstance(strings, list):
            return []
        if not isinstance(pattern, str):
            return strings
        regex = self._compile_regex(pattern)
        template = self._normalize_js_replacement("" if repl is None else str(repl))
        return [regex.sub(template, v) if isinstance(v, str) else v for v in strings]

    @WordDecorator(
        "( strings:string[] sep:string field:number -- field_values:any[] )",
        "Split each string on the LITERAL sep and pick the field-th column (bash cut). '' splits into chars; out-of-range yields null.",
        "CUT",
    )
    async def CUT(self, strings: Any, sep: Any, field: Any) -> list:
        if not isinstance(strings, list):
            return []
        if not isinstance(sep, str):
            return []
        try:
            idx = int(field) if not isinstance(field, bool) else None
        except (TypeError, ValueError):
            idx = None
        if idx is None or (isinstance(field, float) and not field.is_integer()):
            return []

        def cut_one(value: Any) -> Any:
            if not isinstance(value, str):
                return None
            parts = list(value) if sep == "" else value.split(sep)
            return parts[idx] if 0 <= idx < len(parts) else None

        return [cut_one(v) for v in strings]

    # ==================
    # Conversion
    # ==================

    @WordDecorator(
        "( item:any -- string:string )",
        "Convert item to string. Null renders as ''; records render as JSON; arrays comma-join their stringified elements.",
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
        "Replace all literal occurrences of text with replace. For regex matching use RE-REPLACE.",
    )
    async def REPLACE(self, string: Any, text: Any, replace: Any) -> Any:
        # Fully literal on both sides (no regex, no backref surprises).
        # For regex matching use RE-REPLACE.
        if string is None:
            return string
        if text is None or text == "":
            return string
        return string.replace(text, "" if replace is None else replace)

    @WordDecorator("( string:string pattern:string -- match:any )", "Match string against regex pattern", "RE-MATCH")
    async def RE_MATCH(self, string: Any, pattern: str) -> Any:
        # Returns [full, group1, ...] with None for non-participating
        # groups; False on no-match/null input (ts parity — rs pushes NULL
        # there, a documented divergence; both falsy)
        re_pattern = self._compile_regex(pattern)
        result: Any = False
        if isinstance(string, str):
            match = re_pattern.search(string)
            if match:
                result = [match.group(0), *match.groups()]
        return result

    @WordDecorator("( string:string pattern:string -- matches:any[] )", "Find all regex matches in string", "RE-MATCH-ALL")
    async def RE_MATCH_ALL(self, string: Any, pattern: str) -> list:
        # Capture group 1 per match when the pattern has one, otherwise the
        # full match (the old code errored on group-less patterns)
        re_pattern = self._compile_regex(pattern)
        matches: list = []
        if isinstance(string, str):
            for m in re_pattern.finditer(string):
                matches.append(m.group(1) if re_pattern.groups >= 1 else m.group(0))
        return matches

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
