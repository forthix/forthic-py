"""Round-trip and shape tests for the JSON-RPC plain-dict serializer."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from forthic.jsonrpc.serializer import deserialize_value, serialize_value


@pytest.mark.parametrize(
    "value,expected_key",
    [
        (None, "null_value"),
        (True, "bool_value"),
        (False, "bool_value"),
        (42, "int_value"),
        (3.14, "float_value"),
        ("hello", "string_value"),
        ([1, 2, 3], "array_value"),
        ({"a": 1}, "record_value"),
        (date(2025, 1, 15), "plain_date_value"),
    ],
)
def test_tagged_union_shape(value, expected_key):
    sv = serialize_value(value)
    assert isinstance(sv, dict)
    assert expected_key in sv


@pytest.mark.parametrize(
    "value",
    [None, True, False, 0, -7, 42, 3.14, "", "hello", []],
)
def test_round_trip_primitives(value):
    assert deserialize_value(serialize_value(value)) == value


def test_round_trip_array():
    value = [1, "two", True, None, {"x": [1, 2]}]
    assert deserialize_value(serialize_value(value)) == value


def test_round_trip_record():
    value = {"name": "Alice", "age": 30, "tags": ["a", "b"]}
    assert deserialize_value(serialize_value(value)) == value


def test_zoned_datetime_round_trip():
    value = datetime(2025, 1, 15, 10, 30, tzinfo=ZoneInfo("America/New_York"))
    sv = serialize_value(value)
    assert "zoned_datetime_value" in sv
    parsed = deserialize_value(sv)
    assert parsed == value
    assert getattr(parsed.tzinfo, "key", None) == "America/New_York"


def test_naive_datetime_serializes_as_instant_utc():
    naive = datetime(2025, 1, 15, 10, 30)
    sv = serialize_value(naive)
    assert "instant_value" in sv
    parsed = deserialize_value(sv)
    assert parsed == naive.replace(tzinfo=timezone.utc)


def test_json_compatibility():
    # Whole envelope must be JSON-encodable / decodable without losing shape.
    value = {"items": [1, 2.5, "x", None, True, [1, 2]], "stamp": date(2025, 1, 15)}
    sv = serialize_value(value)
    encoded = json.dumps(sv)
    decoded = json.loads(encoded)
    assert deserialize_value(decoded) == value


def test_null_value_uses_empty_object_marker():
    assert serialize_value(None) == {"null_value": {}}


def test_record_rejects_non_string_keys():
    with pytest.raises(ValueError, match="Record keys must be strings"):
        serialize_value({1: "bad"})
