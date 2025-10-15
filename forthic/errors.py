"""Error classes for Forthic interpreter."""

from dataclasses import dataclass


@dataclass
class CodeLocationData:
    """Information about a location in Forthic source code."""

    source: str | None = None  # Source of the code (module name, file path)
    line: int = 1
    column: int = 1
    start_pos: int = 0
    end_pos: int | None = None


class ForthicError(Exception):
    """Base class for all Forthic errors."""

    def __init__(
        self,
        forthic: str,
        note: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(note)
        self.forthic = forthic
        self.note = note
        self.location = location
        self.__cause__ = cause

    def get_forthic(self) -> str:
        return self.forthic

    def get_note(self) -> str:
        return self.note


class UnknownWordError(ForthicError):
    """Raised when an unknown word is encountered."""

    def __init__(
        self,
        forthic: str,
        word: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Unknown word: {word}"
        super().__init__(forthic, note, location, cause)
        self.word = word

    def get_word(self) -> str:
        return self.word


class WordExecutionError(ForthicError):
    """Raised when a word execution fails."""

    def __init__(
        self,
        message: str,
        error: Exception,
        call_location: CodeLocationData | None = None,
        definition_location: CodeLocationData | None = None,
    ):
        super().__init__("", message, call_location)
        self.inner_error = error
        self.definition_location = definition_location

    def get_error(self) -> Exception:
        return self.inner_error

    def get_definition_location(self) -> CodeLocationData | None:
        return self.definition_location


class MissingSemicolonError(ForthicError):
    """Raised when a definition is missing a semicolon."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(forthic, "Missing semicolon", location, cause)


class ExtraSemicolonError(ForthicError):
    """Raised when an extra semicolon is found."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(forthic, "Extra semicolon", location, cause)


class StackUnderflowError(ForthicError):
    """Raised when popping from an empty stack."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(forthic, "Stack underflow", location, cause)


class InvalidVariableNameError(ForthicError):
    """Raised when an invalid variable name is used."""

    def __init__(
        self,
        forthic: str,
        varname: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Invalid variable name: {varname}"
        super().__init__(forthic, note, location, cause)
        self.varname = varname

    def get_varname(self) -> str:
        return self.varname


class UnknownModuleError(ForthicError):
    """Raised when an unknown module is referenced."""

    def __init__(
        self,
        forthic: str,
        module_name: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Unknown module: {module_name}"
        super().__init__(forthic, note, location, cause)
        self.module_name = module_name

    def get_module_name(self) -> str:
        return self.module_name


class InvalidInputPositionError(ForthicError):
    """Raised when an invalid input position is encountered."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(forthic, "Invalid input position", location, cause)


class InvalidWordNameError(ForthicError):
    """Raised when an invalid word name is used."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        note: str | None = None,
        cause: Exception | None = None,
    ):
        error_note = note or "Invalid word name"
        super().__init__(forthic, error_note, location, cause)


class UnterminatedStringError(ForthicError):
    """Raised when a string is not terminated."""

    def __init__(
        self,
        forthic: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(forthic, "Unterminated string", location, cause)


class UnknownTokenError(ForthicError):
    """Raised when an unknown token type is encountered."""

    def __init__(
        self,
        forthic: str,
        token: str,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Unknown type of token: {token}"
        super().__init__(forthic, note, location, cause)
        self.token = token

    def get_token(self) -> str:
        return self.token


class ModuleError(ForthicError):
    """Raised when a module error occurs."""

    def __init__(
        self,
        forthic: str,
        module_name: str,
        error: Exception,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Error in module {module_name}: {error}"
        super().__init__(forthic, note, location, cause)
        self.module_name = module_name
        self.error = error

    def get_module_name(self) -> str:
        return self.module_name

    def get_error(self) -> Exception:
        return self.error


class TooManyAttemptsError(ForthicError):
    """Raised when too many recovery attempts are made."""

    def __init__(
        self,
        forthic: str,
        num_attempts: int,
        max_attempts: int,
        location: CodeLocationData | None = None,
        cause: Exception | None = None,
    ):
        note = f"Too many recovery attempts: {num_attempts} of {max_attempts}"
        super().__init__(forthic, note, location, cause)
        self.num_attempts = num_attempts
        self.max_attempts = max_attempts

    def get_num_attempts(self) -> int:
        return self.num_attempts

    def get_max_attempts(self) -> int:
        return self.max_attempts


class IntentionalStopError(Exception):
    """Raised to intentionally stop execution."""

    pass


def get_error_description(forthic: str, forthic_error: ForthicError) -> str:
    """Get a formatted error description with code location highlighting.

    Args:
        forthic: The Forthic source code
        forthic_error: The ForthicError to format

    Returns:
        A formatted error message with code location and highlighting
    """
    # If don't have any extra info, just return the note
    if not forthic or forthic == "" or forthic_error.location is None:
        return forthic_error.get_note()

    # Otherwise, return the note and indicate where the error occurred
    location = forthic_error.location

    # For WordExecutionError, show both definition and call locations
    if isinstance(forthic_error, WordExecutionError):
        def_loc = forthic_error.get_definition_location()
        if def_loc:
            # Show definition location with highlighting
            def_line_num = def_loc.line
            def_lines = forthic.split("\n")[: def_line_num]
            def_error_line = " " * (def_loc.column - 1) + "^" * (
                (def_loc.end_pos or def_loc.start_pos + 1) - def_loc.start_pos
            )

            def_location_info = f"at line {def_line_num}"
            if def_loc.source:
                def_location_info += f" in {def_loc.source}"

            # Show call location with highlighting
            call_line_num = location.line
            call_lines = forthic.split("\n")[: call_line_num]
            call_error_line = " " * (location.column - 1) + "^" * (
                (location.end_pos or location.start_pos + 1) - location.start_pos
            )

            call_location_info = f"line {call_line_num}"
            if location.source:
                call_location_info += f" in {location.source}"

            def_code = "\n".join(def_lines)
            call_code = "\n".join(call_lines)

            return (
                f"{forthic_error.get_note()} {def_location_info}:\n"
                f"```\n{def_code}\n{def_error_line}\n```\n"
                f"Called from {call_location_info}:\n"
                f"```\n{call_code}\n{call_error_line}\n```"
            )

    # Standard error format for other errors
    line_num = location.line
    lines = forthic.split("\n")[: line_num]
    error_line = " " * (location.column - 1) + "^" * (
        (location.end_pos or location.start_pos + 1) - location.start_pos
    )

    location_info = f"at line {line_num}"
    if location.source:
        location_info += f" in {location.source}"

    code = "\n".join(lines)
    error_message = (
        f"{forthic_error.get_note()} {location_info}:\n"
        f"```\n{code}\n{error_line}\n```"
    )
    return error_message
