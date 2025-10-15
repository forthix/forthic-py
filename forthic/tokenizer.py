"""Tokenizer for Forthic language."""

from dataclasses import dataclass
from enum import IntEnum

from .errors import InvalidWordNameError, UnterminatedStringError


class TokenType(IntEnum):
    """Types of tokens in Forthic."""

    STRING = 1
    COMMENT = 2
    START_ARRAY = 3
    END_ARRAY = 4
    START_MODULE = 5
    END_MODULE = 6
    START_DEF = 7
    END_DEF = 8
    START_MEMO = 9
    WORD = 10
    DOT_SYMBOL = 11
    EOS = 12  # End of string


@dataclass
class CodeLocation:
    """Location information for a token in source code."""

    source: str | None = None
    line: int = 1
    column: int = 1
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class Token:
    """A token produced by the tokenizer."""

    type: TokenType
    string: str
    location: CodeLocation


class PositionedString:
    """A string with location information."""

    def __init__(self, string: str, location: CodeLocation):
        self.string = string
        self.location = location

    def __str__(self) -> str:
        return self.string

    def __repr__(self) -> str:
        return f"PositionedString({self.string!r})"


@dataclass
class _StringDelta:
    """Internal: Tracks string content delta for streaming."""

    start: int
    end: int


class Tokenizer:
    """Tokenizer for Forthic source code.

    Converts Forthic source into a stream of tokens for the interpreter.
    """

    def __init__(
        self,
        string: str,
        reference_location: CodeLocation | None = None,
        streaming: bool = False,
    ):
        if reference_location is None:
            reference_location = CodeLocation()
        self.reference_location = reference_location
        self.line = reference_location.line
        self.column = reference_location.column
        self.input_string = self._unescape_string(string)
        self.input_pos = 0
        self.whitespace = [" ", "\t", "\n", "\r", "(", ")", ","]
        self.quote_chars = ['"', "'", "^"]

        # Token info
        self.token_start_pos = 0
        self.token_end_pos = 0
        self.token_line = 0
        self.token_column = 0
        self.token_string = ""
        self._string_delta: _StringDelta | None = None
        self._streaming = streaming

    def next_token(self) -> Token:
        """Get the next token from the input."""
        self._clear_token_string()
        return self._transition_from_START()

    # Helper functions

    def _unescape_string(self, string: str) -> str:
        """Unescape HTML entities in string."""
        result = string.replace("&lt;", "<")
        result = result.replace("&gt;", ">")
        return result

    def _clear_token_string(self) -> None:
        self.token_string = ""

    def _note_start_token(self) -> None:
        """Record the starting position of a token."""
        self.token_start_pos = self.input_pos + self.reference_location.start_pos
        self.token_line = self.line
        self.token_column = self.column

    def _is_whitespace(self, char: str) -> bool:
        return char in self.whitespace

    def _is_quote(self, char: str) -> bool:
        return char in self.quote_chars

    def _is_triple_quote(self, index: int, char: str) -> bool:
        if not self._is_quote(char):
            return False
        if index + 2 >= len(self.input_string):
            return False
        return (
            self.input_string[index + 1] == char and self.input_string[index + 2] == char
        )

    def _is_start_memo(self, index: int) -> bool:
        if index + 1 >= len(self.input_string):
            return False
        return (
            self.input_string[index] == "@" and self.input_string[index + 1] == ":"
        )

    def _advance_position(self, num_chars: int) -> int:
        """Advance (or retreat) position in input string."""
        i = 0
        if num_chars >= 0:
            for i in range(num_chars):
                if self.input_string[self.input_pos] == "\n":
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.input_pos += 1
        else:
            for i in range(-num_chars):
                self.input_pos -= 1
                if self.input_pos < 0 or self.column < 0:
                    raise ValueError("InvalidInputPositionError")
                if self.input_string[self.input_pos] == "\n":
                    self.line -= 1
                    self.column = 1
                else:
                    self.column -= 1
        return abs(num_chars)

    def _get_token_location(self) -> CodeLocation:
        """Get location information for current token."""
        return CodeLocation(
            source=self.reference_location.source,
            line=self.token_line,
            column=self.token_column,
            start_pos=self.token_start_pos,
            end_pos=self.token_start_pos + len(self.token_string),
        )

    def get_input_string(self) -> str:
        """Get the full input string."""
        return self.input_string

    def get_string_delta(self) -> str:
        """Get the string delta for streaming mode."""
        if self._string_delta is None:
            return ""
        return self.input_string[self._string_delta.start : self._string_delta.end]

    def get_token_location(self) -> CodeLocation:
        """Get the current token location."""
        return self._get_token_location()

    # State transition methods

    def _transition_from_START(self) -> Token:
        """Main tokenization loop."""
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._note_start_token()
            self._advance_position(1)

            if self._is_whitespace(char):
                continue
            elif char == "#":
                return self._transition_from_COMMENT()
            elif char == ":":
                return self._transition_from_START_DEFINITION()
            elif self._is_start_memo(self.input_pos - 1):
                self._advance_position(1)  # Skip over ":" in "@:"
                return self._transition_from_START_MEMO()
            elif char == ";":
                self.token_string = char
                return Token(TokenType.END_DEF, char, self._get_token_location())
            elif char == "[":
                self.token_string = char
                return Token(TokenType.START_ARRAY, char, self._get_token_location())
            elif char == "]":
                self.token_string = char
                return Token(TokenType.END_ARRAY, char, self._get_token_location())
            elif char == "{":
                return self._transition_from_GATHER_MODULE()
            elif char == "}":
                self.token_string = char
                return Token(TokenType.END_MODULE, char, self._get_token_location())
            elif self._is_triple_quote(self.input_pos - 1, char):
                self._advance_position(2)  # Skip 2nd and 3rd quote chars
                return self._transition_from_GATHER_TRIPLE_QUOTE_STRING(char)
            elif self._is_quote(char):
                return self._transition_from_GATHER_STRING(char)
            elif char == ".":
                self._advance_position(-1)  # Back up to beginning of dot symbol
                return self._transition_from_GATHER_DOT_SYMBOL()
            else:
                self._advance_position(-1)  # Back up to beginning of word
                return self._transition_from_GATHER_WORD()

        return Token(TokenType.EOS, "", self._get_token_location())

    def _transition_from_COMMENT(self) -> Token:
        """Gather a comment token."""
        self._note_start_token()
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self.token_string += char
            self._advance_position(1)
            if char == "\n":
                self._advance_position(-1)
                break
        return Token(TokenType.COMMENT, self.token_string, self._get_token_location())

    def _transition_from_START_DEFINITION(self) -> Token:
        """Handle start of definition (after ':')."""
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)

            if self._is_whitespace(char):
                continue
            elif self._is_quote(char):
                raise InvalidWordNameError(
                    self.input_string,
                    self._get_token_location(),
                    "Definition names can't have quotes in them",
                )
            else:
                self._advance_position(-1)
                return self._transition_from_GATHER_DEFINITION_NAME()

        raise InvalidWordNameError(
            self.input_string,
            self._get_token_location(),
            "Got EOS in START_DEFINITION",
        )

    def _transition_from_START_MEMO(self) -> Token:
        """Handle start of memo (after '@:')."""
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)

            if self._is_whitespace(char):
                continue
            elif self._is_quote(char):
                raise InvalidWordNameError(
                    self.input_string,
                    self._get_token_location(),
                    "Memo names can't have quotes in them",
                )
            else:
                self._advance_position(-1)
                return self._transition_from_GATHER_MEMO_NAME()

        raise InvalidWordNameError(
            self.input_string,
            self._get_token_location(),
            "Got EOS in START_MEMO",
        )

    def _gather_definition_name(self) -> None:
        """Gather the name of a definition or memo."""
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)
            if self._is_whitespace(char):
                break
            if self._is_quote(char):
                raise InvalidWordNameError(
                    self.input_string,
                    self._get_token_location(),
                    "Definition names can't have quotes in them",
                )
            if char in ["[", "]", "{", "}"]:
                raise InvalidWordNameError(
                    self.input_string,
                    self._get_token_location(),
                    f"Definition names can't have '{char}' in them",
                )
            self.token_string += char

    def _transition_from_GATHER_DEFINITION_NAME(self) -> Token:
        """Gather definition name token."""
        self._note_start_token()
        self._gather_definition_name()
        return Token(TokenType.START_DEF, self.token_string, self._get_token_location())

    def _transition_from_GATHER_MEMO_NAME(self) -> Token:
        """Gather memo name token."""
        self._note_start_token()
        self._gather_definition_name()
        return Token(TokenType.START_MEMO, self.token_string, self._get_token_location())

    def _transition_from_GATHER_MODULE(self) -> Token:
        """Gather module name."""
        self._note_start_token()
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)
            if self._is_whitespace(char):
                break
            elif char == "}":
                self._advance_position(-1)
                break
            else:
                self.token_string += char
        return Token(TokenType.START_MODULE, self.token_string, self._get_token_location())

    def _transition_from_GATHER_TRIPLE_QUOTE_STRING(self, delim: str) -> Token:
        """Gather triple-quoted string."""
        self._note_start_token()
        string_delimiter = delim
        self._string_delta = _StringDelta(start=self.input_pos, end=self.input_pos)

        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            if char == string_delimiter and self._is_triple_quote(self.input_pos, char):
                # Check for greedy mode (4+ quotes)
                if (
                    self.input_pos + 3 < len(self.input_string)
                    and self.input_string[self.input_pos + 3] == string_delimiter
                ):
                    # Greedy mode: include quote and continue
                    self._advance_position(1)
                    self.token_string += string_delimiter
                    self._string_delta.end = self.input_pos
                    continue

                # Normal: close at first triple quote
                self._advance_position(3)
                token = Token(TokenType.STRING, self.token_string, self._get_token_location())
                self._string_delta = None
                return token
            else:
                self._advance_position(1)
                self.token_string += char
                self._string_delta.end = self.input_pos

        if self._streaming:
            # In streaming mode, return None to indicate incomplete token
            return None  # type: ignore
        raise UnterminatedStringError("Unterminated string", self._get_token_location())

    def _transition_from_GATHER_STRING(self, delim: str) -> Token:
        """Gather single or double quoted string."""
        self._note_start_token()
        string_delimiter = delim
        self._string_delta = _StringDelta(start=self.input_pos, end=self.input_pos)

        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)
            if char == string_delimiter:
                token = Token(TokenType.STRING, self.token_string, self._get_token_location())
                self._string_delta = None
                return token
            else:
                self.token_string += char
                self._string_delta.end = self.input_pos

        if self._streaming:
            return None  # type: ignore
        raise UnterminatedStringError("Unterminated string", self._get_token_location())

    def _transition_from_GATHER_WORD(self) -> Token:
        """Gather a word token."""
        self._note_start_token()
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)
            if self._is_whitespace(char):
                break
            if char in [";", "[", "]", "{", "}", "#"]:
                self._advance_position(-1)
                break
            else:
                self.token_string += char
        return Token(TokenType.WORD, self.token_string, self._get_token_location())

    def _transition_from_GATHER_DOT_SYMBOL(self) -> Token:
        """Gather a dot symbol token."""
        self._note_start_token()
        full_token_string = ""
        while self.input_pos < len(self.input_string):
            char = self.input_string[self.input_pos]
            self._advance_position(1)
            if self._is_whitespace(char):
                break
            if char in [";", "[", "]", "{", "}", "#"]:
                self._advance_position(-1)
                break
            else:
                full_token_string += char
                self.token_string += char

        # If dot symbol has no characters after the dot, treat it as a word
        if len(full_token_string) < 2:  # "." + at least 1 char = 2 minimum
            return Token(TokenType.WORD, full_token_string, self._get_token_location())

        # For DOT_SYMBOL, return the string without the dot prefix
        symbol_without_dot = full_token_string[1:]
        return Token(TokenType.DOT_SYMBOL, symbol_without_dot, self._get_token_location())
