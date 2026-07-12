"""Core module - Essential interpreter operations.

Provides stack manipulation, variables, control flow, and module system operations.
"""

from __future__ import annotations

import json
import math
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...interpreter import Interpreter

from ...decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from ...decorators import ForthicWord as WordDecorator
from ...errors import IntentionalStopError, InvalidVariableNameError, UnknownVariableError
from ...module import Variable
from ...utils import is_truthy, run_to_outcome, to_compact_json, to_forthic_string
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
- Stack: DROP, DUP, SWAP
- Variables: VARIABLES, !, @, !@
- Module: USE-MODULES
- Execution: RUN
- Control: NOP, IF, IF-RUN, WHEN, DEFAULT, DEFAULT-RUN, NULL
- Predicates: ARRAY?, NULL?, EMPTY?, STRING?, NUMBER?, RECORD?
- Options: ~> (converts array to WordOptions)
- String: INTERPOLATE, PRINT
- Debug: PEEK!, STACK!

## Options
INTERPOLATE and PRINT fill ${name} holes (template-literal style; ${.name} also works) from
variables, read-only. Options via the ~> operator: [.option_name value ...] ~> WORD
- separator: String to use when joining array values (default: ", ")
- null_text: Text to display for null/missing values (default: "")
- json: Use JSON formatting for all values (default: false)

## Examples
5 .count ! "Count: ${count}" PRINT
[1 2 3] PRINT                           # Direct printing: 1, 2, 3
[1 2 3] [.separator " | "] ~> PRINT    # With options: 1 | 2 | 3
"Hello ${name}" INTERPOLATE .greeting !
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
    async def DROP(self, a: Any) -> None:
        # Declares no output: the wrapper pushes nothing.
        # (Classic POP dropped — DROP is the canonical name. The old array
        # skip-first-n meaning of DROP is now SKIP.)
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

    @ForthicDirectWord(
        "( variable:any -- value:any )",
        "Gets variable value. READ-ONLY: an unknown variable name is an error and creates nothing — only ! and !@ get-or-create.",
        "@",
    )
    async def at(self, interp: Interpreter) -> None:
        variable = interp.stack_pop()
        if isinstance(variable, str):
            var_obj = interp.find_variable(variable)
            if var_obj is None:
                raise UnknownVariableError(
                    interp.get_top_input_string(), variable, interp.get_string_location()
                )
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

    @ForthicDirectWord(
        "( forthic:string -- )",
        "Run a Forthic string in the current context. Whatever the forthic produces is left on the stack.",
        "RUN",
    )
    async def RUN(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        string_location = interp.get_string_location()
        if forthic:
            await interp.run(forthic, string_location)

    # ==================
    # Module Operations
    # ==================

    @ForthicDirectWord(
        "( names:string[] [options:WordOptions] -- )",
        "Imports modules by name. Entries are 'name' or ['name' 'prefix']; [.prefixed TRUE] "
        "self-prefixes plain names (an explicit pair prefix always wins). Unknown names error.",
        "USE-MODULES",
    )
    async def USE_MODULES(self, interp: Interpreter) -> None:
        options_dict = {}
        if len(interp.get_stack()) > 0:
            top = interp.stack_peek()
            if isinstance(top, WordOptions):
                opts = interp.stack_pop()
                options_dict = opts.to_dict()

        names = interp.stack_pop()
        if names is None:
            return
        if not isinstance(names, list):
            raise ValueError("USE-MODULES requires an array of module names.")
        interp.use_modules(names, prefixed=bool(options_dict.get("prefixed")))

    # ==================
    # Control Flow
    # ==================

    @WordDecorator("( -- )", "Does nothing (no operation)")
    async def NOP(self) -> None:
        pass

    @ForthicDirectWord("( -- null:None )", "Pushes None onto stack")
    async def NULL(self, interp: Interpreter) -> None:
        interp.stack_push(None)

    @WordDecorator("( value:any -- boolean:bool )", "Returns true if value is an array", "ARRAY?")
    async def ARRAY_q(self, value: Any) -> bool:
        return isinstance(value, list)

    @WordDecorator("( value:any -- boolean:bool )", "Returns true if value is null", "NULL?")
    async def NULL_q(self, value: Any) -> bool:
        return value is None

    @WordDecorator(
        "( value:any -- boolean:bool )",
        "Returns true if value is null, an empty string, or a container (array/record) with no entries",
        "EMPTY?",
    )
    async def EMPTY_q(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, list, dict)):
            return len(value) == 0
        return False

    @WordDecorator("( value:any -- boolean:bool )", "Returns true if value is a string", "STRING?")
    async def STRING_q(self, value: Any) -> bool:
        return isinstance(value, str)

    @WordDecorator(
        "( value:any -- boolean:bool )",
        "Returns true if value is a number (Infinity is a number; NaN is not; booleans are not)",
        "NUMBER?",
    )
    async def NUMBER_q(self, value: Any) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, float):
            return not math.isnan(value)
        return isinstance(value, int)

    @WordDecorator(
        "( value:any -- boolean:bool )",
        "Returns true if value is a plain record (not an array, not null)",
        "RECORD?",
    )
    async def RECORD_q(self, value: Any) -> bool:
        return isinstance(value, dict)

    @WordDecorator(
        "( bool:boolean then_value:any else_value:any -- chosen:any )",
        "Pure value selection: push then_value if bool is truthy, else push else_value. "
        "For lazy code execution use IF-RUN; for one-sided side effects use WHEN.",
    )
    async def IF(self, bool_val: Any, then_value: Any, else_value: Any) -> Any:
        return then_value if is_truthy(bool_val) else else_value

    @ForthicDirectWord(
        "( bool:boolean then_forthic:string else_forthic:string -- )",
        "Conditional code execution: if bool is truthy run then_forthic, otherwise run else_forthic. "
        "Branches are Forthic strings; a null/empty branch is a no-op.",
        "IF-RUN",
    )
    async def IF_RUN(self, interp: Interpreter) -> None:
        else_forthic = interp.stack_pop()
        then_forthic = interp.stack_pop()
        bool_val = interp.stack_pop()
        branch = then_forthic if is_truthy(bool_val) else else_forthic
        if branch:
            string_location = interp.get_string_location()
            await interp.run(branch, string_location)

    @ForthicDirectWord(
        "( bool:boolean forthic:string -- )",
        "If bool is truthy run forthic, otherwise do nothing. The forthic argument is always treated as code (executed in current context).",
        "WHEN",
    )
    async def WHEN(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        bool_val = interp.stack_pop()
        if is_truthy(bool_val) and forthic:
            string_location = interp.get_string_location()
            await interp.run(forthic, string_location)

    @WordDecorator(
        "( value:any default_value:any -- result:any )",
        "Returns value or default if value is None/empty string",
    )
    async def DEFAULT(self, value: Any, default_value: Any) -> Any:
        if value is None or value == "":
            return default_value
        return value

    @ForthicDirectWord(
        "( value:any forthic:string -- result:any )",
        "Lazy default: returns value if non-empty, otherwise runs forthic and uses its result. The forthic is only evaluated when needed.",
        "DEFAULT-RUN",
    )
    async def DEFAULT_RUN(self, interp: Interpreter) -> None:
        forthic = interp.stack_pop()
        value = interp.stack_pop()
        if value is None or value == "":
            string_location = interp.get_string_location()
            await interp.run(forthic, string_location)
            # The forthic's result is already on the stack
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
    # String Operations
    # ==================

    @WordDecorator(
        "( string:string [options:WordOptions] -- result:string )",
        "Fill ${name} holes from variables (${.name} also works; read-only — a miss renders as "
        "null_text and creates nothing). Holes are variable names, never expressions. "
        "Escape a literal with \\${. Null template stays null.",
    )
    async def INTERPOLATE(self, string: Any, options: dict[str, Any]) -> Any:
        if string is None:
            return None
        separator = options.get("separator", ", ")
        null_text = options.get("null_text", "")
        use_json = options.get("json", False)

        return self._interpolate_string(str(string), separator, null_text, use_json)

    @WordDecorator(
        "( value:any [options:WordOptions] -- )",
        "Print value to stdout. Strings interpolate ${name} holes first; other values format "
        "with the same options. Escape a literal with \\${.",
    )
    async def PRINT(self, value: Any, options: dict[str, Any]) -> None:
        separator = options.get("separator", ", ")
        null_text = options.get("null_text", "")
        use_json = options.get("json", False)

        if isinstance(value, str):
            # String: interpolate variables
            result = self._interpolate_string(value, separator, null_text, use_json)
        else:
            # Non-string: format directly
            result = self._value_to_string(value, separator, null_text, use_json)

        print(result)

    # The ONE interpolation grammar (settled 2026-07-11, mirrored in
    # forthic-ts / forthic-rs): ${name} holes, variable NAMES only — never
    # expressions — so rendering a template can never execute Forthic
    # (injection-safe by construction; the same reasoning that made JQ
    # paths data instead of interpolated source). Computation belongs on
    # the stack.
    def _interpolate_string(
        self, string: str, separator: str, null_text: str, use_json: bool
    ) -> str:
        if not string:
            string = ""

        # \${ escapes a literal ${: swap for a NUL-fenced placeholder so
        # the hole regex can't see it, restore after
        ESCAPED_HOLE = "\x00ESCAPED_HOLE\x00"
        escaped = string.replace("\\${", ESCAPED_HOLE)

        def fill_hole(match: re.Match) -> str:
            assert self._module.interp is not None
            name = self._hole_name(match.group(1))
            # READ-ONLY lookup: templates render state, never mutate it — a
            # miss renders as null_text and creates nothing (no @-style
            # get-or-create)
            variable = self._module.interp.find_variable(name)
            value = variable.get_value() if variable is not None else None
            return self._value_to_string(value, separator, null_text, use_json)

        interpolated = re.sub(r"\$\{([^{}]*)\}", fill_hole, escaped)

        return interpolated.replace(ESCAPED_HOLE, "${")

    def _hole_name(self, body: str) -> str:
        """Validate a hole body into a variable name. ${1 + 2} is a hard
        error, not a template feature. __ names are reserved, same as ! / @."""
        assert self._module.interp is not None
        trimmed = str(body).strip()
        name = trimmed[1:] if trimmed.startswith(".") else trimmed
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name):
            raise ValueError(
                f"Invalid interpolation hole '${{{body}}}': holes are variable names "
                "(${name} or ${.name}), not expressions. Escape a literal with \\${"
            )
        if name.startswith("__"):
            raise InvalidVariableNameError(
                self._module.interp.get_top_input_string(),
                name,
                self._module.interp.get_string_location(),
            )
        return name

    def _value_to_string(
        self, value: Any, separator: str, null_text: str, use_json: bool
    ) -> str:
        """Convert value to string with formatting options."""
        if value is None:
            return null_text
        if use_json:
            return to_compact_json(value)
        if isinstance(value, list):
            # Elements render recursively, so null elements also use null_text
            return separator.join(
                self._value_to_string(v, separator, null_text, use_json) for v in value
            )
        if isinstance(value, dict):
            return to_compact_json(value)
        return to_forthic_string(value)
