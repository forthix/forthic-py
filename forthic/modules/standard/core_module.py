"""Core module - Essential interpreter operations.

Provides stack manipulation, variables, control flow, and module system operations.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...errors import IntentionalStopError, InvalidVariableNameError
from ...module import Variable
from ...utils import run_to_outcome
from ...word_options import WordOptions


class CoreModule(DecoratedModule):
    """Essential interpreter operations for stack manipulation, variables, and control flow."""

    def __init__(self) -> None:
        super().__init__("core")
        register_module_doc(
            CoreModule,
            """
Essential interpreter operations for stack manipulation, variables, control flow, and module system.

## Categories
- Stack: POP, DUP, SWAP
- Variables: VARIABLES, !, @, !@
- Module: EXPORT, USE_MODULES
- Execution: INTERPRET
- Control: IDENTITY, NOP, DEFAULT, *DEFAULT, NULL, ARRAY?
- Options: ~> (converts array to WordOptions)
- Profiling: PROFILE-START, PROFILE-TIMESTAMP, PROFILE-END, PROFILE-DATA
- String: INTERPOLATE, PRINT
- Debug: PEEK!, STACK!

## Options
INTERPOLATE and PRINT support options via the ~> operator using syntax: [.option_name value ...] ~> WORD
- separator: String to use when joining array values (default: ", ")
- null_text: Text to display for null/None values (default: "null")
- json: Use JSON formatting for all values (default: false)

## Examples
5 .count ! "Count: .count" PRINT
"Items: .items" [.separator " | "] ~> PRINT
[1 2 3] PRINT                           # Direct printing: 1, 2, 3
[1 2 3] [.separator " | "] ~> PRINT    # With options: 1 | 2 | 3
{"name" "Alice"} [.json TRUE] ~> PRINT  # JSON format: {"name":"Alice"}
"Hello .name" INTERPOLATE .greeting !
[1 2 3] DUP SWAP
            """,
        )

    @staticmethod
    def _get_or_create_variable(interp: Interpreter, name: str) -> Variable:
        """Get existing variable or create new one. Validates variable name."""
        # Validate variable name - no __ prefix allowed
        if name.startswith("__"):
            raise InvalidVariableNameError(
                interp.get_top_input_string(), name, interp.get_string_location()
            )

        cur_module = interp.cur_module()

        # Check if variable already exists
        variable = cur_module.variables.get(name)

        # Create it if it doesn't exist
        if not variable:
            cur_module.add_variable(name)
            variable = cur_module.variables[name]

        return variable

    # ==================
    # Stack Operations
    # ==================

    @WordDecorator("( a:any -- )", "Removes top item from stack")
    async def POP(self, a: Any) -> None:
        # No return = push nothing
        pass

    @ForthicDirectWord("( a:any -- a:any a:any )", "Duplicates top stack item")
    async def DUP(self, interp: Interpreter) -> None:
        a = interp.stack_pop()
        interp.stack_push(a)
        interp.stack_push(a)

    @ForthicDirectWord("( a:any b:any -- b:any a:any )", "Swaps top two stack items")
    async def SWAP(self, interp: Interpreter) -> None:
        b = interp.stack_pop()
        a = interp.stack_pop()
        interp.stack_push(b)
        interp.stack_push(a)

    # ==================
    # Debug Operations
    # ==================

    @ForthicDirectWord("( -- )", "Prints top of stack and stops execution", "PEEK!")
    async def PEEK_bang(self, interp: Interpreter) -> None:
        stack = interp.get_stack().get_items()
        if len(stack) > 0:
            print(stack[-1])
        else:
            print("<STACK EMPTY>")
        raise IntentionalStopError("PEEK!")

    @ForthicDirectWord("( -- )", "Prints entire stack (reversed) and stops execution", "STACK!")
    async def STACK_bang(self, interp: Interpreter) -> None:
        stack = list(reversed(interp.get_stack().get_items()))
        print(json.dumps(stack, indent=2, default=str))
        raise IntentionalStopError("STACK!")

    # ==================
    # Variables
    # ==================

    @WordDecorator("( varnames:list -- )", "Creates variables in current module")
    async def VARIABLES(self, varnames: list[str]) -> None:
        assert self._module.interp is not None
        module = self._module.interp.cur_module()
        for v in varnames:
            if v.startswith("__"):
                raise InvalidVariableNameError(
                    self._module.interp.get_top_input_string(),
                    v,
                    self._module.interp.get_string_location(),
                )
            module.add_variable(v)

    @WordDecorator("( value:any variable:any -- )", "Sets variable value (auto-creates if string name)", "!")
    async def bang(self, value: Any, variable: Any) -> None:
        assert self._module.interp is not None
        if isinstance(variable, str):
            var_obj = CoreModule._get_or_create_variable(self._module.interp, variable)
        else:
            var_obj = variable
        var_obj.set_value(value)

    @ForthicDirectWord("( variable:any -- value:any )", "Gets variable value (auto-creates if string name)", "@")
    async def at(self, interp: Interpreter) -> None:
        variable = interp.stack_pop()
        if isinstance(variable, str):
            var_obj = CoreModule._get_or_create_variable(interp, variable)
        else:
            var_obj = variable
        interp.stack_push(var_obj.get_value())

    @ForthicDirectWord("( value:any variable:any -- value:any )", "Sets variable and returns value", "!@")
    async def bang_at(self, interp: Interpreter) -> None:
        variable = interp.stack_pop()
        value = interp.stack_pop()
        if isinstance(variable, str):
            var_obj = CoreModule._get_or_create_variable(interp, variable)
        else:
            var_obj = variable
        var_obj.set_value(value)
        interp.stack_push(var_obj.get_value())

    # ==================
    # Execution
    # ==================

    @ForthicDirectWord("( string:str -- )", "Interprets Forthic string in current context")
    async def INTERPRET(self, interp: Interpreter) -> None:
        string = interp.stack_pop()
        string_location = interp.get_string_location()
        if string:
            await interp.run(string, string_location)

    # ==================
    # Module Operations
    # ==================

    @ForthicDirectWord("( names:list -- )", "Exports words from current module")
    async def EXPORT(self, interp: Interpreter) -> None:
        names = interp.stack_pop()
        interp.cur_module().add_exportable(names)

    @ForthicDirectWord("( names:list -- )", "Imports modules by name")
    async def USE_MODULES(self, interp: Interpreter) -> None:
        names = interp.stack_pop()
        if names:
            interp.use_modules(names)

    # ==================
    # Control Flow
    # ==================

    @WordDecorator("( -- )", "Does nothing (identity operation)")
    async def IDENTITY(self) -> None:
        pass

    @WordDecorator("( -- )", "Does nothing (no operation)")
    async def NOP(self) -> None:
        pass

    @ForthicDirectWord("( -- null:None )", "Pushes None onto stack")
    async def NULL(self, interp: Interpreter) -> None:
        interp.stack_push(None)

    @WordDecorator("( value:any -- boolean:bool )", "Returns true if value is an array", "ARRAY?")
    async def ARRAY_q(self, value: Any) -> bool:
        return isinstance(value, list)

    @WordDecorator(
        "( value:any default_value:any -- result:any )",
        "Returns value or default if value is None/empty string",
    )
    async def DEFAULT(self, value: Any, default_value: Any) -> Any:
        if value is None or value == "":
            return default_value
        return value

    @ForthicDirectWord(
        "( value:any default_forthic:str -- result:any )",
        "Returns value or executes Forthic if value is None/empty string",
        "*DEFAULT",
    )
    async def star_DEFAULT(self, interp: Interpreter) -> None:
        default_forthic = interp.stack_pop()
        value = interp.stack_pop()

        if value is None or value == "":
            string_location = interp.get_string_location()
            await interp.run(default_forthic, string_location)
            # Result is already on stack from run()
        else:
            interp.stack_push(value)

    # ==================
    # TRY: error handling as data (Rust Result semantics)
    #
    # Forthic's default error behavior is already Rust's `?` — errors
    # auto-propagate up run(). TRY is the other half of the Result model:
    # holding an error as a value. Law: 'CODE' TRY UNWRAP ≡ CODE.
    # Mirrored in forthic-ts / forthic-rs.
    # ==================

    @ForthicDirectWord(
        "( forthic:string -- outcome:record )",
        'Run forthic, capturing the outcome as data: {"ok": value} on success (value = top of stack '
        "if the run changed the stack; null for no-net-effect code), "
        '{"error": {message, error_type}} on failure. On failure the stack is restored to its state '
        "before TRY (transactional for the stack; side effects like variable writes persist), and "
        "modules left open by the failed code are unwound. For error-tolerant mapping use MAP's "
        "outcomes option ([.outcomes TRUE] ~> MAP): TRY inside MAP would transactionally restore "
        "the item MAP pushed, stranding it beneath the outcome.",
        "TRY",
    )
    async def TRY(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        string_location = interp.get_string_location()
        snapshot = list(interp.get_stack().get_raw_items())
        module_depth = interp.module_stack_depth()
        outcome = await run_to_outcome(interp, forthic, string_location, snapshot, module_depth)
        interp.stack_push(outcome)

    @WordDecorator(
        "( outcome:record -- boolean:boolean )",
        "True if outcome is an ok record (structural: has an 'ok' key)",
        "OK?",
    )
    async def OK_q(self, outcome: Any) -> bool:
        return isinstance(outcome, dict) and "ok" in outcome

    @WordDecorator(
        "( outcome:record -- boolean:boolean )",
        "True if outcome is an error record (structural: has an 'error' key)",
        "ERROR?",
    )
    async def ERROR_q(self, outcome: Any) -> bool:
        return isinstance(outcome, dict) and "error" in outcome

    # UNWRAP/UNWRAP-OR are direct words: an ok payload can legitimately be
    # NULL, and the @ForthicWord decorator skips pushing None returns
    @ForthicDirectWord(
        "( outcome:record -- value:any )",
        "Extract the ok value from a TRY outcome; re-raises for an error outcome (preserving "
        "message and error_type). 'CODE' TRY UNWRAP ≡ CODE.",
        "UNWRAP",
    )
    async def UNWRAP(self, interp: Interpreter) -> None:
        outcome = interp.stack_pop()
        if isinstance(outcome, dict):
            if "ok" in outcome:
                interp.stack_push(outcome["ok"])
                return
            if "error" in outcome:
                info = outcome["error"] if isinstance(outcome["error"], dict) else {}
                message = info.get("message") or "UNWRAP of error outcome"
                error_type = info.get("error_type")
                type_suffix = f" ({error_type})" if error_type else ""
                raise RuntimeError(f"{message}{type_suffix}")
        raise RuntimeError("UNWRAP requires a TRY outcome record with an 'ok' or 'error' key")

    @ForthicDirectWord(
        "( outcome:record default:any -- value:any )",
        "Extract the ok value from a TRY outcome, or default if it is an error outcome",
        "UNWRAP-OR",
    )
    async def UNWRAP_OR(self, interp: Interpreter) -> None:
        default_value = interp.stack_pop()
        outcome = interp.stack_pop()
        if isinstance(outcome, dict):
            if "ok" in outcome:
                interp.stack_push(outcome["ok"])
                return
            if "error" in outcome:
                interp.stack_push(default_value)
                return
        raise RuntimeError("UNWRAP-OR requires a TRY outcome record with an 'ok' or 'error' key")

    # ==================
    # WordOptions
    # ==================

    @WordDecorator(
        "( array:list -- options:WordOptions )",
        "Convert options array to WordOptions. Format: [.key1 val1 .key2 val2]",
        "~>",
    )
    async def tilde_gt(self, array: list) -> WordOptions:
        return WordOptions(array)

    # ==================
    # Profiling
    # ==================

    @ForthicDirectWord("( -- )", "Starts profiling word execution", "PROFILE-START")
    async def PROFILE_START(self, interp: Interpreter) -> None:
        interp.start_profiling()

    @ForthicDirectWord("( -- )", "Stops profiling word execution", "PROFILE-END")
    async def PROFILE_END(self, interp: Interpreter) -> None:
        interp.stop_profiling()

    @ForthicDirectWord("( label:str -- )", "Records profiling timestamp with label", "PROFILE-TIMESTAMP")
    async def PROFILE_TIMESTAMP(self, interp: Interpreter) -> None:
        label = interp.stack_pop()
        interp.add_timestamp(label)

    @ForthicDirectWord(
        "( -- profile_data:dict )", "Returns profiling data (word counts and timestamps)", "PROFILE-DATA"
    )
    async def PROFILE_DATA(self, interp: Interpreter) -> None:
        histogram = interp.word_histogram()
        timestamps = interp.profile_timestamps()

        result: dict[str, list] = {"word_counts": [], "timestamps": []}

        for val in histogram:
            rec = {"word": val["word"], "count": val["count"]}
            result["word_counts"].append(rec)

        prev_time = 0.0
        for t in timestamps:
            rec = {"label": t["label"], "time_ms": t["time_ms"], "delta": t["time_ms"] - prev_time}
            prev_time = t["time_ms"]
            result["timestamps"].append(rec)

        interp.stack_push(result)

    # ==================
    # String Operations
    # ==================

    @WordDecorator(
        "( string:str [options:WordOptions] -- result:str )",
        "Interpolate variables (.name) and return result string. Use \\. to escape literal dots.",
    )
    async def INTERPOLATE(self, string: str, options: dict[str, Any]) -> str:
        separator = options.get("separator", ", ")
        null_text = options.get("null_text", "null")
        use_json = options.get("json", False)

        return self._interpolate_string(string, separator, null_text, use_json)

    @WordDecorator(
        "( value:any [options:WordOptions] -- )",
        "Print value to stdout. Strings interpolate variables (.name). Use \\. to escape literal dots.",
    )
    async def PRINT(self, value: Any, options: dict[str, Any]) -> None:
        separator = options.get("separator", ", ")
        null_text = options.get("null_text", "null")
        use_json = options.get("json", False)

        if isinstance(value, str):
            # String: interpolate variables
            result = self._interpolate_string(value, separator, null_text, use_json)
        else:
            # Non-string: format directly
            result = self._value_to_string(value, separator, null_text, use_json)

        print(result)

    def _interpolate_string(
        self, string: str, separator: str, null_text: str, use_json: bool
    ) -> str:
        r"""Interpolate variables in string. Handles escaped dots (\.)."""
        if not string:
            string = ""

        # First, handle escape sequences by replacing \. with a temporary placeholder
        escaped = string.replace("\\.", "\x00ESCAPED_DOT\x00")

        # Replace whitespace-preceded or start-of-string .variable patterns
        def replace_var(match: re.Match) -> str:
            assert self._module.interp is not None
            var_name = match.group(1)
            variable = CoreModule._get_or_create_variable(self._module.interp, var_name)
            value = variable.get_value()
            return self._value_to_string(value, separator, null_text, use_json)

        interpolated = re.sub(
            r"(?:^|(?<=\s))\.([a-zA-Z_][a-zA-Z0-9_-]*)", replace_var, escaped
        )

        # Restore escaped dots
        return interpolated.replace("\x00ESCAPED_DOT\x00", ".")

    def _value_to_string(
        self, value: Any, separator: str, null_text: str, use_json: bool
    ) -> str:
        """Convert value to string with formatting options."""
        if value is None:
            return null_text
        if use_json:
            return json.dumps(value, default=str)
        if isinstance(value, list):
            return separator.join(str(v) for v in value)
        if isinstance(value, dict):
            return json.dumps(value, default=str)
        return str(value)
