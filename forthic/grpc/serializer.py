"""
Phase 2: Serialization/Deserialization for all basic Forthic types
Handles: int, float, string, bool, None, list, dict
Phase 4: Added DataFrame support (serialized as records)
Phase 8: Added temporal types (datetime, date)
"""
import re
from typing import Any
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from forthic.grpc import forthic_runtime_pb2

# Optional pandas import for DataFrame support
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def serialize_value(value: Any) -> forthic_runtime_pb2.StackValue:
    """Convert Python value to protobuf StackValue"""
    print(f"[SERIALIZE] type={type(value).__name__} value={repr(value)[:100]}", flush=True)
    stack_value = forthic_runtime_pb2.StackValue()

    # Handle None
    if value is None:
        stack_value.null_value.CopyFrom(forthic_runtime_pb2.NullValue())
        return stack_value

    # Handle datetime (must check before date, as datetime is subclass of date)
    if isinstance(value, datetime):
        # If timezone-aware with a named timezone (not just UTC offset), serialize as ZonedDateTimeValue
        if value.tzinfo is not None and hasattr(value.tzinfo, 'key'):
            # This is a ZoneInfo timezone - preserve it as ZonedDateTime
            zoned_value = forthic_runtime_pb2.ZonedDateTimeValue()
            # Format: "2025-01-15T10:30:00-05:00[America/New_York]"
            iso_str = value.isoformat()
            tz_name = value.tzinfo.key
            zoned_value.iso8601 = f"{iso_str}[{tz_name}]"
            zoned_value.timezone = tz_name
            stack_value.zoned_datetime_value.CopyFrom(zoned_value)
        elif value.tzinfo is not None:
            # Timezone-aware but not ZoneInfo (e.g., UTC offset) - serialize as Instant
            utc_dt = value.astimezone(timezone.utc)
            instant_value = forthic_runtime_pb2.InstantValue()
            instant_value.iso8601 = utc_dt.isoformat()
            stack_value.instant_value.CopyFrom(instant_value)
        else:
            # Naive datetime - treat as instant in UTC
            # Add UTC timezone before serializing
            utc_dt = value.replace(tzinfo=timezone.utc)
            instant_value = forthic_runtime_pb2.InstantValue()
            instant_value.iso8601 = utc_dt.isoformat()
            stack_value.instant_value.CopyFrom(instant_value)
        return stack_value

    # Handle date
    if isinstance(value, date):
        plain_date_value = forthic_runtime_pb2.PlainDateValue()
        plain_date_value.iso8601_date = value.isoformat()
        stack_value.plain_date_value.CopyFrom(plain_date_value)
        return stack_value

    # Handle bool (must check before int, as bool is subclass of int in Python)
    if isinstance(value, bool):
        stack_value.bool_value = value
        return stack_value

    # Handle int
    if isinstance(value, int):
        stack_value.int_value = value
        return stack_value

    # Handle float
    if isinstance(value, float):
        stack_value.float_value = value
        return stack_value

    # Handle string
    if isinstance(value, str):
        stack_value.string_value = value
        return stack_value

    # Handle list/array
    if isinstance(value, list):
        array_value = forthic_runtime_pb2.ArrayValue()
        for item in value:
            array_value.items.append(serialize_value(item))
        stack_value.array_value.CopyFrom(array_value)
        return stack_value

    # Handle dict/record
    if isinstance(value, dict):
        record_value = forthic_runtime_pb2.RecordValue()
        for key, val in value.items():
            if not isinstance(key, str):
                raise ValueError(f"Record keys must be strings, got {type(key).__name__}")
            record_value.fields[key].CopyFrom(serialize_value(val))
        stack_value.record_value.CopyFrom(record_value)
        return stack_value

    # Handle pandas DataFrame (Phase 4)
    # Serialize as array of records for cross-language compatibility
    if HAS_PANDAS and isinstance(value, pd.DataFrame):
        records = value.to_dict("records")
        return serialize_value(records)  # Recursively serialize as array

    raise ValueError(f"Unsupported value type: {type(value).__name__}")


def deserialize_value(stack_value: forthic_runtime_pb2.StackValue) -> Any:
    """Convert protobuf StackValue to Python value"""
    which = stack_value.WhichOneof("value")
    print(f"[DESERIALIZE] which = {which}", flush=True)

    if which == "int_value":
        return stack_value.int_value
    elif which == "string_value":
        return stack_value.string_value
    elif which == "bool_value":
        return stack_value.bool_value
    elif which == "float_value":
        return stack_value.float_value
    elif which == "null_value":
        return None
    elif which == "instant_value":
        # Parse ISO 8601 datetime string
        # May include IANA timezone in brackets (e.g., "2025-01-15T10:30:00-05:00[America/New_York]")
        iso_str = stack_value.instant_value.iso8601
        print(f"[INSTANT] iso8601='{iso_str}'", flush=True)

        # Check if the string contains IANA timezone identifier in brackets
        iana_match = re.match(r'^(.+?)\[([^\]]+)\]$', iso_str)

        if iana_match:
            # Extract the datetime part and IANA timezone
            dt_part = iana_match.group(1)
            iana_tz = iana_match.group(2)
            print(f"[INSTANT] Has IANA tz - dt_part='{dt_part}' tz='{iana_tz}'", flush=True)

            # Parse the datetime part (without IANA timezone)
            dt = datetime.fromisoformat(dt_part)

            # Convert to the IANA timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(iana_tz))
            else:
                dt = dt.astimezone(ZoneInfo(iana_tz))

            print(f"[INSTANT] Result: {dt}", flush=True)
            return dt
        else:
            # Standard ISO 8601 parsing
            result = datetime.fromisoformat(iso_str)
            print(f"[INSTANT] Standard parse: {result}", flush=True)
            return result
    elif which == "plain_date_value":
        # Parse ISO 8601 date string
        iso_str = stack_value.plain_date_value.iso8601_date
        return date.fromisoformat(iso_str)
    elif which == "zoned_datetime_value":
        # Parse ISO 8601 datetime string with timezone
        # Format: "2025-01-15T10:30:00-05:00[America/New_York]"
        iso_str = stack_value.zoned_datetime_value.iso8601
        tz_field = stack_value.zoned_datetime_value.timezone
        print(f"[ZONED_DT] iso8601='{iso_str}' timezone='{tz_field}'", flush=True)

        # Check if the string contains IANA timezone identifier in brackets
        iana_match = re.match(r'^(.+?)\[([^\]]+)\]$', iso_str)

        if iana_match:
            # Extract the datetime part and IANA timezone
            dt_part = iana_match.group(1)
            iana_tz = iana_match.group(2)
            print(f"[ZONED_DT] Matched! dt_part='{dt_part}' iana_tz='{iana_tz}'", flush=True)

            # Parse the datetime part (without IANA timezone)
            try:
                dt = datetime.fromisoformat(dt_part)
                print(f"[ZONED_DT] Parsed: {dt}", flush=True)
            except Exception as e:
                print(f"[ZONED_DT] ERROR parsing dt_part: {e}", flush=True)
                raise

            # Convert to the IANA timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(iana_tz))
            else:
                dt = dt.astimezone(ZoneInfo(iana_tz))

            print(f"[ZONED_DT] Final: {dt}", flush=True)
            return dt
        else:
            # No IANA timezone - use standard parsing
            print(f"[ZONED_DT] No IANA match, trying standard parse", flush=True)
            try:
                result = datetime.fromisoformat(iso_str)
                print(f"[ZONED_DT] Standard parse succeeded: {result}", flush=True)
                return result
            except Exception as e:
                print(f"[ZONED_DT] ERROR in standard parse: {e}", flush=True)
                raise
    elif which == "array_value":
        return [deserialize_value(item) for item in stack_value.array_value.items]
    elif which == "record_value":
        return {key: deserialize_value(val) for key, val in stack_value.record_value.fields.items()}
    else:
        raise ValueError(f"Unknown stack value type: {which}")
