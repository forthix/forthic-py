"""Batch 5 words: math & datetime round-out.

Port of forthic-rs tests/word_batch5_test.rs, plus RANGE (rs fixed RANGE
in its Batch 0; py never had it). py notes: strict parsing in >DATE (no
new Date() leniency beyond month-name forms); non-numeric PRODUCT
elements are null (no JS string coercion, no Python string repetition);
py ints are arbitrary-precision so huge PRODUCTs stay exact (host-native
numerics — rs saturates to Float there).
"""

import math

import pytest

from forthic.interpreter import StandardInterpreter


async def run(code: str, timezone: str = "UTC"):
    interp = StandardInterpreter(timezone=timezone)
    await interp.run(code)
    return interp.stack_pop()


# ===== RANGE =====


@pytest.mark.asyncio
async def test_range_ascending():
    assert await run("1 4 RANGE") == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_range_reversed_is_empty():
    assert await run("5 1 RANGE") == []


@pytest.mark.asyncio
async def test_range_allocation_guard():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="too large"):
        await interp.run("1 2000000000 RANGE")


# ===== PRODUCT (Batch 0 word; Batch 5 pins) =====


@pytest.mark.asyncio
async def test_product_strictness():
    assert await run("[ 2 0.5 ] PRODUCT") == 1
    assert await run("5 PRODUCT") is None
    # Non-numeric elements: null (no Python string repetition!)
    assert await run("[ 2 'x' ] PRODUCT") is None
    # py ints are arbitrary precision: huge products stay exact
    assert await run("[ 1000000000000000000 100 ] PRODUCT") == 10**20


# ===== SQRT =====


@pytest.mark.asyncio
async def test_sqrt():
    assert await run("16 SQRT") == 4
    assert await run("NULL SQRT") is None
    assert abs(await run("2 SQRT") - math.sqrt(2)) < 1e-9
    # Negative input is NaN (JS Math.sqrt), not an error
    assert math.isnan(await run("-1 SQRT"))


# ===== CLAMP =====


@pytest.mark.asyncio
async def test_clamp():
    assert await run("5 0 10 CLAMP") == 5
    assert await run("-5 0 10 CLAMP") == 0
    assert await run("15 0 10 CLAMP") == 10
    # Boundaries inclusive
    assert await run("0 0 10 CLAMP") == 0
    assert await run("10 0 10 CLAMP") == 10
    # ts formula is max(min, min(max, value)): when min > max, MIN WINS
    assert await run("5 10 0 CLAMP") == 10
    # Any NULL operand nulls the result
    assert await run("NULL 0 10 CLAMP") is None
    assert await run("5 NULL 10 CLAMP") is None


@pytest.mark.asyncio
async def test_clamp_propagates_nan_like_js():
    # JS Math.min/max propagate NaN; Python's min/max are order-dependent
    interp = StandardInterpreter()
    interp.stack_push(math.nan)
    await interp.run("0 10 CLAMP")
    assert math.isnan(interp.stack_pop())


# ===== MOD / ROUND (JS semantics) =====


@pytest.mark.asyncio
async def test_mod_takes_the_sign_of_the_dividend():
    # JS % is truncated modulo; Python's % is floored — pinned to JS
    assert await run("7 3 MOD") == 1
    assert await run("-7 3 MOD") == -1
    assert await run("7 -3 MOD") == 1
    assert await run("NULL 3 MOD") is None


@pytest.mark.asyncio
async def test_round_halves_go_toward_positive_infinity():
    # JS Math.round; Python's round() is banker's (2.5 -> 2)
    assert await run("0.5 ROUND") == 1
    assert await run("2.5 ROUND") == 3
    assert await run("-2.5 ROUND") == -2
    assert await run("-0.6 ROUND") == -1


# ===== FORMAT-FIXED =====


@pytest.mark.asyncio
async def test_format_fixed():
    assert await run("3.14159 2 FORMAT-FIXED") == "3.14"
    assert await run("5 2 FORMAT-FIXED") == "5.00", "pads with zeros"
    assert await run("3.7 0 FORMAT-FIXED") == "4", "digits 0 has no point"
    assert await run("NULL 2 FORMAT-FIXED") is None
    # NULL digits means 0 (JS ToInteger)
    assert await run("3.7 NULL FORMAT-FIXED") == "4"


@pytest.mark.asyncio
async def test_format_fixed_rounds_half_away_from_zero():
    # JS toFixed semantics on exactly-representable ties; Python's f-string
    # would give "0" and "2" (ties-to-even)
    assert await run("0.5 0 FORMAT-FIXED") == "1"
    assert await run("2.5 0 FORMAT-FIXED") == "3"
    assert await run("-0.5 0 FORMAT-FIXED") == "-1"
    # 1.005 is 1.00499... in binary — "1.00" in every runtime
    assert await run("1.005 2 FORMAT-FIXED") == "1.00"


@pytest.mark.asyncio
async def test_format_fixed_errors():
    # The one math word where wrong inputs THROW (ts RangeError/TypeError)
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="between 0 and 100"):
        await interp.run("3.14 -1 FORMAT-FIXED")
    interp.reset()
    with pytest.raises(Exception, match="between 0 and 100"):
        await interp.run("3.14 101 FORMAT-FIXED")
    interp.reset()
    with pytest.raises(Exception, match="requires a number"):
        await interp.run("'x' 2 FORMAT-FIXED")


@pytest.mark.asyncio
async def test_classic_to_fixed_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="FIXED"):
        await interp.run("3.14 2 >FIXED")


# ===== AM / PM =====


@pytest.mark.asyncio
async def test_am_forces_morning():
    result = await run("'14:30' >TIME AM")
    assert (result.hour, result.minute) == (2, 30)
    result = await run("'12:00' >TIME AM")
    assert (result.hour, result.minute) == (0, 0), "noon -> midnight"
    result = await run("'09:15' >TIME AM")
    assert (result.hour, result.minute) == (9, 15), "already morning"


@pytest.mark.asyncio
async def test_pm_forces_afternoon():
    result = await run("'09:15' >TIME PM")
    assert (result.hour, result.minute) == (21, 15)
    result = await run("'00:00' >TIME PM")
    assert (result.hour, result.minute) == (12, 0), "midnight -> noon"
    result = await run("'14:30' >TIME PM")
    assert (result.hour, result.minute) == (14, 30), "already afternoon"


@pytest.mark.asyncio
async def test_am_pm_pass_non_times_through_unchanged():
    # ts returns the input itself, NOT null
    assert await run("NULL AM") is None
    assert await run("'not a time' PM") == "not a time"
    assert await run("42 AM") == 42


# ===== DAYS-BETWEEN (replaces classic SUBTRACT-DATES) =====


@pytest.mark.asyncio
async def test_days_between_is_date1_minus_date2():
    assert await run("'2026-01-10' >DATE '2026-01-01' >DATE DAYS-BETWEEN") == 9
    assert await run("'2024-01-15' >DATE '2024-01-25' >DATE DAYS-BETWEEN") == -10, (
        "sign convention identical to the dropped SUBTRACT-DATES"
    )
    assert await run("'2024-01-15' >DATE '2024-01-15' >DATE DAYS-BETWEEN") == 0
    assert await run("NULL '2024-01-15' >DATE DAYS-BETWEEN") is None


@pytest.mark.asyncio
async def test_classic_subtract_dates_is_gone():
    # Tombstone: the last scheduled classic drop
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="SUBTRACT-DATES"):
        await interp.run("'2024-01-15' >DATE '2024-01-25' >DATE SUBTRACT-DATES")


# ===== YEAR / MONTH / DAY-OF-WEEK =====


@pytest.mark.asyncio
async def test_date_components():
    assert await run("'2024-01-15' >DATE YEAR") == 2024
    assert await run("'2024-01-15' >DATE MONTH") == 1, "1-based (1=January)"
    assert await run("'2024-01-15' >DATE DAY-OF-WEEK") == 1, "2024-01-15 is a Monday; ISO 1=Mon"
    assert await run("'2024-01-21' >DATE DAY-OF-WEEK") == 7, "Sunday is 7, never 0"


@pytest.mark.asyncio
async def test_date_components_need_a_date():
    # Strings do NOT coerce
    assert await run("'2024-01-15' YEAR") is None
    assert await run("NULL MONTH") is None
    assert await run("42 DAY-OF-WEEK") is None


@pytest.mark.asyncio
async def test_date_components_work_on_datetimes():
    assert await run("0 >DATETIME YEAR") == 1970
    assert await run("0 >DATETIME MONTH") == 1
    assert await run("0 >DATETIME DAY-OF-WEEK") == 4, "epoch was a Thursday"


# ===== >DATE after ts #35 =====


@pytest.mark.asyncio
async def test_to_date_takes_written_date_for_no_zone_and_offset_strings():
    import datetime as dt

    assert await run("'2024-01-15' >DATE") == dt.date(2024, 1, 15)
    assert await run("'2024-01-15T23:30:00' >DATE") == dt.date(2024, 1, 15)
    # Explicit numeric offset: date AS WRITTEN, offset ignored
    assert await run("'2024-01-15T23:30:00+09:00' >DATE") == dt.date(2024, 1, 15)
    # Whitespace trims
    assert await run("'  2024-01-15  ' >DATE") == dt.date(2024, 1, 15)


@pytest.mark.asyncio
async def test_to_date_resolves_z_instants_in_interpreter_timezone():
    import datetime as dt

    # The #35 rule: a trailing-Z instant is a moment in time; its calendar
    # date depends on the INTERPRETER timezone (never the host's)
    assert await run("'2024-01-15T23:30:00Z' >DATE", timezone="Asia/Tokyo") == dt.date(2024, 1, 16)
    assert await run("'2024-01-15T23:30:00Z' >DATE", timezone="America/Los_Angeles") == dt.date(
        2024, 1, 15
    )


@pytest.mark.asyncio
async def test_to_date_month_name_forms_and_strictness():
    import datetime as dt

    assert await run("'Oct 21, 2020' >DATE") == dt.date(2020, 10, 21)
    assert await run("'October 21, 2020' >DATE") == dt.date(2020, 10, 21)
    # Beyond that, no new Date() leniency — sanctioned strict divergence
    assert await run("'20240115' >DATE") is None
    assert await run("'garbage' >DATE") is None
    assert await run("0 >DATE") is None, "ts falsy asymmetry kept"


# ===== USE-MODULES =====


def make_greet_module():
    from forthic.module import Module, PushValueWord

    module = Module("greet")
    word = PushValueWord("GREETING", "hello")
    module.add_word(word)
    module.add_exportable(["GREETING"])
    return module


@pytest.mark.asyncio
async def test_use_modules_unprefixed():
    interp = StandardInterpreter()
    interp.register_module(make_greet_module())
    await interp.run("[ 'greet' ] USE-MODULES GREETING")
    assert interp.stack_pop() == "hello"


@pytest.mark.asyncio
async def test_use_modules_prefixed_option():
    interp = StandardInterpreter()
    interp.register_module(make_greet_module())
    await interp.run("[ 'greet' ] [ .prefixed TRUE ] ~> USE-MODULES greet.GREETING")
    assert interp.stack_pop() == "hello"
    # ...and the bare name was NOT imported
    with pytest.raises(Exception, match="GREETING"):
        await interp.run("GREETING")


@pytest.mark.asyncio
async def test_use_modules_pair_prefix_beats_option():
    interp = StandardInterpreter()
    interp.register_module(make_greet_module())
    await interp.run("[ [ 'greet' 'g' ] ] [ .prefixed TRUE ] ~> USE-MODULES g.GREETING")
    assert interp.stack_pop() == "hello"
    with pytest.raises(Exception):
        await interp.run("greet.GREETING")


@pytest.mark.asyncio
async def test_use_modules_errors():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="no-such-module"):
        await interp.run("[ 'no-such-module' ] USE-MODULES")
    interp.reset()
    with pytest.raises(Exception, match="requires an array"):
        await interp.run("'greet' USE-MODULES")
    # NULL names is a silent no-op
    interp.reset()
    await interp.run("NULL USE-MODULES")
    assert len(interp.get_stack()) == 0
