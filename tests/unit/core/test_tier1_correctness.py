"""Tier 1 correctness regression tests.

Port of forthic-rs tests/tier1_correctness_test.rs — pins the correctness
fixes from the ts scrub (#26, #29, #31) as executable contract specs:
crash-proof error formatter, temporal/record equality, ANY over an empty
set, IntentionalStop identity, and NOW/TODAY in the interpreter timezone.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from forthic.errors import (
    CodeLocation,
    IntentionalStopError,
    UnknownWordError,
    get_error_description,
)
from forthic.interpreter import StandardInterpreter


async def run(code: str, timezone: str = "UTC"):
    interp = StandardInterpreter(timezone=timezone)
    await interp.run(code)
    return interp.stack_pop()


# ===== 1. Error formatter must never crash (ts #26 crash-proof formatter) =====


def test_formatter_survives_degenerate_location():
    # end_pos < start_pos is constructible; formatting used to render zero
    # carets via a negative string repeat
    degenerate = CodeLocation(source=None, line=1, column=5, start_pos=10, end_pos=3)
    err = UnknownWordError("SOME CODE", "CODE", degenerate)
    formatted = get_error_description("SOME CODE", err)
    assert "^" in formatted, f"still renders a caret: {formatted}"


def test_formatter_survives_location_past_end_of_source():
    past_end = CodeLocation(source=None, line=99, column=50, start_pos=1000, end_pos=1001)
    err = UnknownWordError("short", "X", past_end)
    get_error_description("short", err)  # must not raise


def test_formatter_survives_negative_column():
    weird = CodeLocation(source=None, line=1, column=0, start_pos=0, end_pos=None)
    err = UnknownWordError("X", "X", weird)
    get_error_description("X", err)  # must not raise


# ===== 2. Temporal + record equality (ts #29) =====


@pytest.mark.asyncio
async def test_today_equals_today():
    assert await run("TODAY TODAY ==") is True


@pytest.mark.asyncio
async def test_equal_dates_are_equal():
    assert await run("2020-06-05 2020-06-05 ==") is True
    assert await run("2020-06-05 2020-06-06 ==") is False
    assert await run("2020-06-05 2020-06-06 !=") is True


@pytest.mark.asyncio
async def test_equal_times_are_equal():
    assert await run("9:30 9:30 ==") is True
    assert await run("9:30 9:31 ==") is False


@pytest.mark.asyncio
async def test_datetime_equality_requires_same_timezone():
    # ts compares Temporal values by ISO string (includes the tz annotation):
    # the same instant in different timezones is NOT equal
    instant_utc = datetime(2020, 6, 5, 17, 15, 0, tzinfo=ZoneInfo("UTC"))
    same_instant_la = instant_utc.astimezone(ZoneInfo("America/Los_Angeles"))

    interp = StandardInterpreter()
    interp.stack_push(instant_utc)
    interp.stack_push(same_instant_la)
    await interp.run("==")
    assert interp.stack_pop() is False

    interp.stack_push(instant_utc)
    interp.stack_push(instant_utc)
    await interp.run("==")
    assert interp.stack_pop() is True


@pytest.mark.asyncio
async def test_temporal_membership_works():
    # values_equal also feeds the membership words
    assert await run("[ TODAY ] TODAY CONTAINS?") is True


@pytest.mark.asyncio
async def test_record_equality_is_structural():
    assert await run("[ [ 'a' 1 ] ] REC [ [ 'a' 1 ] ] REC ==") is True
    assert await run("[ [ 'a' 1 ] ] REC [ [ 'a' 2 ] ] REC ==") is False


@pytest.mark.asyncio
async def test_booleans_only_equal_booleans():
    # JS ===: 1 is not true; Python's True == 1 must not leak through
    assert await run("TRUE 1 ==") is False
    assert await run("FALSE 0 ==") is False
    assert await run("TRUE TRUE ==") is True


@pytest.mark.asyncio
async def test_int_and_float_unify():
    # One JS number type: 1 equals 1.0
    assert await run("1 1.0 ==") is True


# ===== 3. ANY with empty second array (ts #31) =====


@pytest.mark.asyncio
async def test_any_with_empty_second_array_is_false():
    # Nothing can match against an empty set (the old code returned true)
    assert await run("[ 1 2 ] [ ] ANY") is False
    assert await run("[ ] [ ] ANY") is False
    assert await run("[ 1 2 ] [ 2 ] ANY") is True
    # ALL over an empty items2 stays vacuously true (matches ts)
    assert await run("[ 1 2 ] [ ] ALL") is True


# ===== 4. IntentionalStop keeps its identity and message (ts #26) =====


@pytest.mark.asyncio
async def test_intentional_stop_passes_through_definitions_unwrapped():
    interp = StandardInterpreter()
    await interp.run(": WRAPPED 42 PEEK! ;")
    with pytest.raises(IntentionalStopError) as exc_info:
        await interp.run("WRAPPED")
    # Not wrapped in WordExecutionError; message preserved
    assert str(exc_info.value) == "PEEK!"


# ===== 5. NOW and TODAY use the interpreter timezone (ts #29) =====


@pytest.mark.asyncio
async def test_now_uses_interpreter_timezone():
    interp = StandardInterpreter(timezone="America/New_York")
    await interp.run("NOW")
    now = interp.stack_pop()
    assert isinstance(now, datetime)
    assert str(now.tzinfo) == "America/New_York"


@pytest.mark.asyncio
@pytest.mark.parametrize("tz", ["Pacific/Kiritimati", "Pacific/Midway", "UTC"])
async def test_now_and_today_agree_on_the_date(tz):
    # NOW and TODAY must agree on what day it is in any single timezone
    # (allowing for a midnight tick between the two calls)
    interp = StandardInterpreter(timezone=tz)
    await interp.run("TODAY NOW")
    now = interp.stack_pop()
    today = interp.stack_pop()
    day_delta = (now.date() - today).days
    assert 0 <= day_delta <= 1, f"NOW ({now.date()}) and TODAY ({today}) disagree in {tz}"


# ===== 6. reset() clears per-run parsing state =====


@pytest.mark.asyncio
async def test_reset_after_failed_run_restores_interpreter():
    interp = StandardInterpreter()
    with pytest.raises(Exception):
        await interp.run("1 2 NO-SUCH-WORD")
    interp.reset()
    assert len(interp.get_stack()) == 0
    await interp.run("40 2 +")
    assert interp.stack_pop() == 42
