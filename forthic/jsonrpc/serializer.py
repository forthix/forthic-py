"""JSON-RPC StackValue serialization.

Plain-dict serializer matching the wire format of the TypeScript JSON-RPC
server (which itself reuses the protobuf StackValue tagged-union shape):

    {"int_value": 42}
    {"string_value": "hi"}
    {"bool_value": true}
    {"float_value": 1.5}
    {"null_value": {}}
    {"array_value": {"items": [<StackValue>, ...]}}
    {"record_value": {"fields": {<key>: <StackValue>, ...}}}
    {"instant_value": {"iso8601": "..."}}
    {"plain_date_value": {"iso8601_date": "..."}}
    {"plain_time_value": {"iso8601_time": "..."}}
    {"zoned_datetime_value": {"iso8601": "...", "timezone": "..."}}

Operates on plain dicts (no protobuf dependency); the tagged-union shape
is kept for wire compatibility with the other Forthic runtimes.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


def serialize_value(value: Any) -> dict[str, Any]:
    """Convert a Python value to a JSON-RPC StackValue dict."""
    if value is None:
        return {"null_value": {}}

    if isinstance(value, datetime):
        if value.tzinfo is not None and hasattr(value.tzinfo, "key"):
            iso_str = value.isoformat()
            tz_name = value.tzinfo.key
            return {
                "zoned_datetime_value": {
                    "iso8601": f"{iso_str}[{tz_name}]",
                    "timezone": tz_name,
                }
            }
        if value.tzinfo is not None:
            utc_dt = value.astimezone(timezone.utc)
            return {"instant_value": {"iso8601": utc_dt.isoformat()}}
        utc_dt = value.replace(tzinfo=timezone.utc)
        return {"instant_value": {"iso8601": utc_dt.isoformat()}}

    if isinstance(value, date):
        return {"plain_date_value": {"iso8601_date": value.isoformat()}}

    if isinstance(value, time):
        return {"plain_time_value": {"iso8601_time": value.isoformat()}}

    if isinstance(value, bool):
        return {"bool_value": value}

    if isinstance(value, int):
        return {"int_value": value}

    if isinstance(value, float):
        return {"float_value": value}

    if isinstance(value, str):
        return {"string_value": value}

    if isinstance(value, list):
        return {"array_value": {"items": [serialize_value(v) for v in value]}}

    if isinstance(value, dict):
        for key in value.keys():
            if not isinstance(key, str):
                raise ValueError(
                    f"Record keys must be strings, got {type(key).__name__}"
                )
        return {
            "record_value": {
                "fields": {k: serialize_value(v) for k, v in value.items()}
            }
        }

    if _HAS_PANDAS and isinstance(value, pd.DataFrame):
        return serialize_value(value.to_dict("records"))

    raise ValueError(f"Unsupported value type: {type(value).__name__}")


_IANA_BRACKET = re.compile(r"^(.+?)\[([^\]]+)\]$")


def deserialize_value(stack_value: dict[str, Any]) -> Any:
    """Convert a JSON-RPC StackValue dict to a Python value."""
    if "int_value" in stack_value:
        return stack_value["int_value"]
    if "string_value" in stack_value:
        return stack_value["string_value"]
    if "bool_value" in stack_value:
        return stack_value["bool_value"]
    if "float_value" in stack_value:
        return stack_value["float_value"]
    if "null_value" in stack_value:
        return None
    if "array_value" in stack_value:
        items = stack_value["array_value"].get("items", [])
        return [deserialize_value(item) for item in items]
    if "record_value" in stack_value:
        fields = stack_value["record_value"].get("fields", {})
        return {k: deserialize_value(v) for k, v in fields.items()}
    if "instant_value" in stack_value:
        return _parse_zoned_iso(stack_value["instant_value"]["iso8601"])
    if "plain_date_value" in stack_value:
        return date.fromisoformat(stack_value["plain_date_value"]["iso8601_date"])
    if "plain_time_value" in stack_value:
        return time.fromisoformat(stack_value["plain_time_value"]["iso8601_time"])
    if "zoned_datetime_value" in stack_value:
        return _parse_zoned_iso(stack_value["zoned_datetime_value"]["iso8601"])

    raise ValueError(f"Unknown stack value type: {stack_value!r}")


def _parse_zoned_iso(iso_str: str) -> datetime:
    """Parse an ISO-8601 string that may carry an IANA tz in brackets."""
    iana_match = _IANA_BRACKET.match(iso_str)
    if iana_match:
        dt_part = iana_match.group(1)
        iana_tz = iana_match.group(2)
        dt = datetime.fromisoformat(dt_part)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(iana_tz))
        else:
            dt = dt.astimezone(ZoneInfo(iana_tz))
        return dt
    return datetime.fromisoformat(iso_str)
