"""Utility functions for Forthic."""

import json
import math
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo


def is_truthy(value: Any) -> bool:
    """JS truthiness (the cross-runtime contract for >BOOL, IF, ANY?, ALL?, ...).

    Differs from Python's bool() in two ways that matter:
    - empty containers (lists, records) are TRUTHY
    - NaN is falsy

    None, False, 0, and "" are falsy; everything else is truthy.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value != 0 and not math.isnan(value)
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    return True


def values_equal(a: Any, b: Any) -> bool:
    """Cross-runtime value equality (feeds ==, !=, and membership words).

    JS ===-flavored where Python disagrees:
    - booleans only equal booleans (Python's True == 1 is a false friend)
    - int and float unify (one JS number type): 1 equals 1.0
    - datetimes match ts's ISO-string comparison: the same instant in two
      different timezones is NOT equal
    - arrays and records compare structurally (the sanctioned rs divergence
      from ts's reference identity)
    """
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b  # NaN != NaN falls out naturally
    if isinstance(a, datetime) or isinstance(b, datetime):
        # datetime is a date subclass; require both to be datetimes so a
        # date never equals a datetime
        if not (isinstance(a, datetime) and isinstance(b, datetime)):
            return False
        return a == b and str(a.tzinfo) == str(b.tzinfo)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(values_equal(v, b[k]) for k, v in a.items())
    if type(a) is not type(b):
        return False
    return bool(a == b)


def _same_stack_item(a: Any, b: Any) -> bool:
    """Element comparison for TRY's unchanged-stack check (ts uses ===):
    identity for objects, value equality for same-type primitives."""
    if a is b:
        return True
    return type(a) is type(b) and isinstance(a, (int, float, str)) and a == b


async def run_to_outcome(
    interp: Any, forthic: str, location: Any, snapshot: list[Any], module_depth: int
) -> dict[str, Any]:
    """Run forthic and capture the result as a TRY outcome record.

    Shared by TRY and MAP's outcomes option — the caller chooses the
    snapshot moment (TRY: before anything; MAP: BEFORE pushing the item, so
    a failed element consumes the item and cannot strand it).

    Success: {"ok": payload} where payload is the top of stack if the run
    changed the stack relative to the snapshot (a no-net-effect run yields
    ok: None). Failure: the stack is restored to the snapshot, modules left
    open by the failed code are unwound, and the outcome is
    {"error": {"message", "error_type"}}.
    """
    try:
        await interp.run(forthic, location)
    except Exception as e:
        interp.get_stack().set_raw_items(list(snapshot))
        while interp.module_stack_depth() > module_depth:
            interp.module_stack_pop()
        return {"error": {"message": str(e), "error_type": type(e).__name__}}

    after = interp.get_stack().get_raw_items()
    unchanged = len(after) == len(snapshot) and all(
        _same_stack_item(x, y) for x, y in zip(after, snapshot, strict=True)
    )
    payload = interp.stack_pop() if not unchanged and len(after) > 0 else None
    return {"ok": payload}


def _jsonable(value: Any) -> Any:
    """Convert a Forthic value to something json.dumps renders per the contract."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None  # JSON.stringify renders NaN/Infinity as null
        return int(value) if value.is_integer() else value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return value


def to_compact_json(value: Any) -> str:
    """Insertion-ordered compact JSON (records in >STR, interpolation, ...)."""
    return json.dumps(_jsonable(value), separators=(",", ":"), ensure_ascii=False)


def to_forthic_string(value: Any) -> str:
    """JS-flavored stringification (the >STR contract).

    None -> "", booleans lowercase, integral floats drop the ".0", arrays
    comma-join recursively with null elements empty (JS Array.toString),
    records render as insertion-ordered compact JSON, temporal values use
    their ISO forms.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, list):
        return ",".join(to_forthic_string(v) for v in value)
    if isinstance(value, dict):
        return to_compact_json(value)
    return str(value)


def to_zoned_datetime(date_string: str, timezone: str) -> datetime | None:
    """Parse a date string and create a timezone-aware datetime.

    Args:
        date_string: ISO format date string (e.g., "2025-06-07T13:00:00")
        timezone: IANA timezone name (e.g., "America/Los_Angeles")

    Returns:
        A timezone-aware datetime object, or None if parsing fails
    """
    try:
        # Parse the date string components
        year = int(date_string[0:4])
        month = int(date_string[5:7])
        day = int(date_string[8:10])
        hour = int(date_string[11:13])
        minute = int(date_string[14:16])
        second = int(date_string[17:19])

        # Create timezone-aware datetime
        tz = ZoneInfo(timezone)
        return datetime(year, month, day, hour, minute, second, tzinfo=tz)
    except (ValueError, IndexError, KeyError):
        return None
