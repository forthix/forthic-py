"""Present-but-verify pass (Phase 5).

Port of forthic-rs tests/present_verify_test.rs, plus the py-specific
items this scrub flagged along the way (stray '}', dropped no-sibling
classics per the owner decision). py note: OR/AND's two-value form
returns the selecting OPERAND like ts (rs coerces to Bool — its
sanctioned divergence); that behavior is pinned in test_word_batch1.py.
"""

import math

import pytest

from forthic.errors import ModuleStackUnderflowError, UnknownVariableError
from forthic.interpreter import StandardInterpreter


async def run(code: str, timezone: str = "UTC"):
    interp = StandardInterpreter(timezone=timezone)
    await interp.run(code)
    return interp.stack_pop()


# ===== >DATETIME / TIMESTAMP>DATETIME: interpreter timezone =====


@pytest.mark.asyncio
async def test_timestamps_resolve_in_interpreter_timezone():
    # The ts test-pinned instant: 1593895532 is 2020-07-04 13:45 in LA
    # (20:45 UTC — a UTC-hardcoded runtime fails this)
    result = await run("1593895532 >DATETIME", timezone="America/Los_Angeles")
    assert (result.year, result.month, result.day, result.hour, result.minute) == (
        2020, 7, 4, 13, 45,
    )
    assert str(result.tzinfo) == "America/Los_Angeles"

    result = await run("1593895532 TIMESTAMP>DATETIME", timezone="America/Los_Angeles")
    assert result.hour == 13


@pytest.mark.asyncio
async def test_to_datetime_input_breadth():
    # Epoch 0 is a value, not a miss (ts #29)
    assert (await run("0 >DATETIME")).year == 1970
    # Floats are epoch seconds too
    assert (await run("0.5 >DATETIME")).year == 1970
    # A Date is midnight in the interpreter tz
    result = await run("'2024-01-15' >DATE >DATETIME", timezone="Asia/Tokyo")
    assert (result.year, result.month, result.day, result.hour) == (2024, 1, 15, 0)
    assert str(result.tzinfo) == "Asia/Tokyo"
    # An existing DateTime passes through KEEPING its own timezone
    tokyo_dt = await run("0 >DATETIME", timezone="Asia/Tokyo")
    interp = StandardInterpreter(timezone="UTC")
    interp.stack_push(tokyo_dt)
    await interp.run(">DATETIME")
    assert str(interp.stack_pop().tzinfo) == "Asia/Tokyo"
    assert await run("NULL >DATETIME") is None
    assert await run("'' >DATETIME") is None


@pytest.mark.asyncio
async def test_to_datetime_strings_are_wall_clocks_in_interpreter_tz():
    result = await run("'2024-01-15T14:30:00' >DATETIME", timezone="America/Los_Angeles")
    assert (result.year, result.month, result.day, result.hour, result.minute) == (
        2024, 1, 15, 14, 30,
    )
    assert str(result.tzinfo) == "America/Los_Angeles"
    # Short and date-only forms
    assert (await run("'2024-01-15T14:30' >DATETIME")).minute == 30
    assert (await run("'2024-01-15' >DATETIME")).hour == 0


@pytest.mark.asyncio
async def test_to_datetime_zoned_strings_are_instants():
    # Zone-carrying strings are the instants they denote, resolved into
    # the interpreter tz (consistent with >DATE's #35 rule). ts originally
    # nulled Z-strings and reinterpreted offset wall-clocks (Temporal
    # accidents); a fix aligning ts to this contract is in flight
    # (forthic-ts fix/datetime-zoned-strings-are-instants)
    result = await run("'2024-01-15T23:30:00Z' >DATETIME", timezone="Asia/Tokyo")
    assert (result.year, result.month, result.day, result.hour) == (
        2024, 1, 16, 8,
    ), "23:30Z is 08:30 next day in Tokyo"
    assert str(result.tzinfo) == "Asia/Tokyo"


@pytest.mark.asyncio
async def test_at_builds_wall_clock_in_interpreter_tz():
    result = await run("'2024-01-15' >DATE '14:30' >TIME AT", timezone="America/Los_Angeles")
    assert (result.year, result.month, result.day, result.hour, result.minute) == (
        2024, 1, 15, 14, 30,
    )
    assert str(result.tzinfo) == "America/Los_Angeles"
    # Round trip through the timestamp words agrees with itself
    interp = StandardInterpreter(timezone="America/Los_Angeles")
    await interp.run("'2024-01-15' >DATE '14:30' >TIME AT >TIMESTAMP TIMESTAMP>DATETIME")
    assert interp.stack_pop().hour == 14
    # Falsy operands
    assert await run("NULL '14:30' >TIME AT") is None
    assert await run("'2024-01-15' >DATE NULL AT") is None


# ===== MEAN: polymorphic dispatch =====


@pytest.mark.asyncio
async def test_mean_numbers():
    assert await run("[ 2 4 6 ] MEAN") == 4
    assert await run("[ 1 2 ] MEAN") == 1.5
    # NULL elements are SKIPPED, not zero
    assert await run("[ 2 NULL 4 ] MEAN") == 3
    assert await run("[ NULL NULL ] MEAN") == 0


@pytest.mark.asyncio
async def test_mean_edges():
    assert await run("NULL MEAN") == 0, "falsy input is 0"
    assert await run("[ ] MEAN") == 0
    # Truthy non-array passes through as-is — including empty records,
    # which are truthy under the contract
    assert await run("'hello' MEAN") == "hello"
    assert await run("[ ] REC MEAN") == {}
    # Single-element array: that element AS-IS (before null filtering)
    assert await run("[ 'a' ] MEAN") == "a"
    assert await run("[ NULL ] MEAN") is None


@pytest.mark.asyncio
async def test_mean_strings_give_frequency_distribution():
    result = await run("[ 'a' 'a' 'b' 'c' ] MEAN")
    assert result == {"a": 0.5, "b": 0.25, "c": 0.25}


@pytest.mark.asyncio
async def test_mean_records_give_field_wise_mean():
    result = await run(
        "[ [ [ 'score' 10 ] [ 'grade' 'A' ] ] REC "
        "[ [ 'score' 20 ] [ 'grade' 'A' ] ] REC ] MEAN"
    )
    assert result == {"score": 15, "grade": {"A": 1.0}}
    assert list(result.keys()) == ["score", "grade"], "first-seen key order"


# ===== @ : read-only fetch, unknown variable errors =====


@pytest.mark.asyncio
async def test_fetch_unknown_variable_is_an_error():
    interp = StandardInterpreter()
    with pytest.raises(UnknownVariableError, match="ghost"):
        await interp.run(".ghost @")


@pytest.mark.asyncio
async def test_fetch_does_not_create_as_a_side_effect():
    # ts pins this explicitly: the failed @ must not mint the variable
    interp = StandardInterpreter()
    with pytest.raises(UnknownVariableError):
        await interp.run(".ghost @")
    assert interp.find_variable("ghost") is None


@pytest.mark.asyncio
async def test_declared_and_stored_variables_still_read():
    # Declared-but-unset reads as NULL (no error)
    assert await run("[ 'x' ] VARIABLES .x @") is None
    # Stored reads back; ! still get-or-creates
    assert await run("7 .y ! .y @") == 7


# ===== Stray } errors (py finding from Phase 2) =====


@pytest.mark.asyncio
async def test_stray_end_module_errors():
    # A stray } at the app-module level used to silently pop the app
    # module itself, corrupting the interpreter
    interp = StandardInterpreter()
    with pytest.raises(ModuleStackUnderflowError):
        await interp.run("}")
    # Balanced module blocks still work
    interp = StandardInterpreter()
    await interp.run("{my-mod } 40 2 +")
    assert interp.stack_pop() == 42


# ===== UNIQUE: structural equality =====


@pytest.mark.asyncio
async def test_unique_handles_unhashable_elements():
    # dict.fromkeys raised TypeError on records; structural policy matches
    # UNIQUE-BY / SORT-U
    result = await run("[ [ [ 'a' 1 ] ] REC [ [ 'a' 1 ] ] REC [ [ 'a' 2 ] ] REC ] UNIQUE")
    assert result == [{"a": 1}, {"a": 2}]


# ===== Dropped no-sibling classics (owner decision — matches rs) =====


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code",
    [
        "[ 'X' ] EXPORT",
        "PROFILE-START",
        "PROFILE-TIMESTAMP",
        "PROFILE-END",
        "PROFILE-DATA",
        "[ 1 2 ] SHUFFLE",
        "[ 1 2 ] ROTATE",
        "INFINITY",
        "0 1 UNIFORM-RANDOM",
        "'ab' '(a)' RE-MATCH 1 RE-MATCH-GROUP",
    ],
)
async def test_no_sibling_classics_are_gone(code):
    interp = StandardInterpreter()
    with pytest.raises(Exception):
        await interp.run(code)


@pytest.mark.asyncio
async def test_e_and_pi_stay_as_py_extensions():
    # Owner decision: keep, propose upstream to ts/rs
    assert abs(await run("PI") - math.pi) < 1e-12
    assert abs(await run("E") - math.e) < 1e-12
