"""Tests for the DateTime module."""

import pytest
from datetime import date, time, datetime
from zoneinfo import ZoneInfo

from forthic.interpreter import StandardInterpreter


@pytest.fixture
async def interp():
    """Create a StandardInterpreter with Los Angeles timezone."""
    return StandardInterpreter([], "America/Los_Angeles")


# ========================================
# Current Time/Date
# ========================================


@pytest.mark.asyncio
async def test_TODAY_returns_current_date(interp):
    """TODAY returns current date."""
    await interp.run("TODAY")
    result = interp.stack_pop()
    tz = interp.get_timezone()
    today = datetime.now(tz).date()

    assert result.year == today.year
    assert result.month == today.month
    assert result.day == today.day


@pytest.mark.asyncio
async def test_NOW_returns_current_datetime(interp):
    """NOW returns current datetime."""
    await interp.run("NOW")
    result = interp.stack_pop()
    tz = interp.get_timezone()
    now = datetime.now(tz)

    assert result.year == now.year
    assert result.month == now.month
    assert result.day == now.day
    assert result.hour == now.hour
    assert result.minute == now.minute


# ========================================
# Time Adjustment (AM/PM)
# ========================================


@pytest.mark.asyncio
async def test_AM_converts_afternoon_to_morning(interp):
    """AM converts afternoon to morning."""
    await interp.run("14:30 AM")
    result = interp.stack_pop()
    assert result.hour == 2
    assert result.minute == 30


@pytest.mark.asyncio
async def test_AM_keeps_morning_times_unchanged(interp):
    """AM keeps morning times unchanged."""
    await interp.run("'09:15' >TIME AM")
    result = interp.stack_pop()
    assert result.hour == 9
    assert result.minute == 15


@pytest.mark.asyncio
async def test_PM_converts_morning_to_afternoon(interp):
    """PM converts morning to afternoon."""
    await interp.run("09:15 PM")
    result = interp.stack_pop()
    assert result.hour == 21
    assert result.minute == 15


@pytest.mark.asyncio
async def test_PM_keeps_afternoon_times_unchanged(interp):
    """PM keeps afternoon times unchanged."""
    await interp.run("14:30 PM")
    result = interp.stack_pop()
    assert result.hour == 14
    assert result.minute == 30


@pytest.mark.asyncio
async def test_AM_PM_with_noon_and_midnight(interp):
    """AM/PM with noon and midnight."""
    await interp.run("'12:00' >TIME AM")
    assert interp.stack_pop().hour == 0

    await interp.run("'00:00' >TIME PM")
    assert interp.stack_pop().hour == 12


# ========================================
# Conversion TO Time/Date/DateTime
# ========================================


@pytest.mark.asyncio
async def test_to_TIME_parses_HH_MM_format(interp):
    """>TIME parses HH:MM format."""
    await interp.run("'14:30' >TIME")
    result = interp.stack_pop()
    assert result.hour == 14
    assert result.minute == 30


@pytest.mark.asyncio
async def test_to_TIME_parses_HH_MM_AM_format(interp):
    """>TIME parses HH:MM AM format."""
    await interp.run("'10:52 PM' >TIME")
    result = interp.stack_pop()
    assert result.hour == 22
    assert result.minute == 52


@pytest.mark.asyncio
async def test_to_TIME_parses_HH_MM_PM_format(interp):
    """>TIME parses HH:MM PM format."""
    await interp.run("'02:15 PM' >TIME")
    result = interp.stack_pop()
    assert result.hour == 14
    assert result.minute == 15


@pytest.mark.asyncio
async def test_to_TIME_extracts_time_from_datetime(interp):
    """>TIME extracts time from datetime."""
    await interp.run("NOW >TIME")
    result = interp.stack_pop()
    assert isinstance(result.hour, int)
    assert isinstance(result.minute, int)


@pytest.mark.asyncio
async def test_to_DATE_parses_ISO_format(interp):
    """>DATE parses ISO format."""
    await interp.run("'2024-01-15' >DATE")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


@pytest.mark.asyncio
async def test_to_DATE_parses_flexible_format(interp):
    """>DATE parses flexible format."""
    await interp.run("'Oct 21, 2020' >DATE")
    result = interp.stack_pop()
    assert result.year == 2020
    assert result.month == 10
    assert result.day == 21


@pytest.mark.asyncio
async def test_to_DATE_extracts_date_from_datetime(interp):
    """>DATE extracts date from datetime."""
    await interp.run("NOW >DATE")
    result = interp.stack_pop()
    tz = interp.get_timezone()
    today = datetime.now(tz).date()
    assert result.year == today.year
    assert result.month == today.month
    assert result.day == today.day


@pytest.mark.asyncio
async def test_to_DATETIME_parses_ISO_datetime_string(interp):
    """>DATETIME parses ISO datetime string."""
    await interp.run("'2024-01-15T14:30:00' >DATETIME")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 14
    assert result.minute == 30


@pytest.mark.asyncio
async def test_to_DATETIME_converts_Unix_timestamp(interp):
    """>DATETIME converts Unix timestamp."""
    # 1593895532 seconds = July 4, 2020, 13:45:32 PDT
    await interp.run("1593895532 >DATETIME")
    result = interp.stack_pop()
    assert result.year == 2020
    assert result.month == 7
    assert result.day == 4


@pytest.mark.asyncio
async def test_AT_combines_date_and_time(interp):
    """AT combines date and time."""
    await interp.run("'2024-01-15' >DATE '14:30' >TIME AT")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 14
    assert result.minute == 30


# ========================================
# Conversion FROM Time/Date
# ========================================


@pytest.mark.asyncio
async def test_TIME_to_STR_formats_time_as_HH_MM(interp):
    """TIME>STR formats time as HH:MM."""
    await interp.run("'14:30' >TIME TIME>STR")
    assert interp.stack_pop() == "14:30"


@pytest.mark.asyncio
async def test_DATE_to_STR_formats_date_as_YYYY_MM_DD(interp):
    """DATE>STR formats date as YYYY-MM-DD."""
    await interp.run("'2024-01-15' >DATE DATE>STR")
    assert interp.stack_pop() == "2024-01-15"


@pytest.mark.asyncio
async def test_DATE_to_STR_with_literal_date(interp):
    """DATE>STR with literal date."""
    await interp.run("2021-01-01 DATE>STR")
    assert interp.stack_pop() == "2021-01-01"


@pytest.mark.asyncio
async def test_DATE_to_INT_converts_date_to_integer(interp):
    """DATE>INT converts date to integer."""
    await interp.run("'2024-01-15' >DATE DATE>INT")
    assert interp.stack_pop() == 20240115


@pytest.mark.asyncio
async def test_DATE_to_INT_with_single_digit_month_and_day(interp):
    """DATE>INT with single-digit month and day."""
    await interp.run("'2024-03-05' >DATE DATE>INT")
    assert interp.stack_pop() == 20240305


# ========================================
# Timestamp Operations
# ========================================


@pytest.mark.asyncio
async def test_to_TIMESTAMP_converts_datetime_to_Unix_timestamp(interp):
    """>TIMESTAMP converts datetime to Unix timestamp."""
    await interp.run("'2020-07-01T15:20:00' >DATETIME >TIMESTAMP")
    result = interp.stack_pop()
    # Should be close to 1593642000 (may vary slightly due to timezone)
    assert abs(result - 1593642000) < 100


@pytest.mark.asyncio
async def test_TIMESTAMP_to_DATETIME_converts_Unix_timestamp_to_datetime(interp):
    """TIMESTAMP>DATETIME converts Unix timestamp to datetime."""
    await interp.run("1593895532 TIMESTAMP>DATETIME")
    result = interp.stack_pop()
    assert result.year == 2020
    assert result.month == 7
    assert result.day == 4
    assert result.hour == 13
    assert result.minute == 45


@pytest.mark.asyncio
async def test_round_trip_datetime_timestamp_datetime(interp):
    """Round-trip: datetime -> timestamp -> datetime."""
    await interp.run("'2024-01-15T14:30:00' >DATETIME >TIMESTAMP TIMESTAMP>DATETIME")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15
    assert result.hour == 14
    assert result.minute == 30


# ========================================
# Date Math
# ========================================


@pytest.mark.asyncio
async def test_ADD_DAYS_adds_positive_days(interp):
    """ADD-DAYS adds positive days."""
    await interp.run("'2024-01-15' >DATE 10 ADD-DAYS")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 25


@pytest.mark.asyncio
async def test_ADD_DAYS_adds_negative_days(interp):
    """ADD-DAYS adds negative days."""
    await interp.run("'2024-01-15' >DATE -5 ADD-DAYS")
    result = interp.stack_pop()
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 10


@pytest.mark.asyncio
async def test_ADD_DAYS_crosses_month_boundary(interp):
    """ADD-DAYS crosses month boundary."""
    await interp.run("'2020-10-21' >DATE 12 ADD-DAYS")
    result = interp.stack_pop()
    assert result.year == 2020
    assert result.month == 11
    assert result.day == 2


@pytest.mark.asyncio
async def test_ADD_DAYS_with_literal_date(interp):
    """ADD-DAYS with literal date."""
    await interp.run("2020-10-21 12 ADD-DAYS")
    result = interp.stack_pop()
    assert result.year == 2020
    assert result.month == 11
    assert result.day == 2


@pytest.mark.asyncio
async def test_SUBTRACT_DATES_calculates_positive_difference(interp):
    """SUBTRACT-DATES calculates positive difference."""
    # date1 - date2 = 2024-01-15 - 2024-01-25 = -10
    await interp.run("'2024-01-15' >DATE '2024-01-25' >DATE SUBTRACT-DATES")
    assert interp.stack_pop() == -10


@pytest.mark.asyncio
async def test_SUBTRACT_DATES_calculates_negative_difference(interp):
    """SUBTRACT-DATES calculates negative difference."""
    await interp.run("'2020-10-21' >DATE '2020-11-02' >DATE SUBTRACT-DATES")
    assert interp.stack_pop() == -12


@pytest.mark.asyncio
async def test_SUBTRACT_DATES_with_literal_dates(interp):
    """SUBTRACT-DATES with literal dates."""
    await interp.run("2020-10-21 2020-11-02 SUBTRACT-DATES")
    assert interp.stack_pop() == -12


@pytest.mark.asyncio
async def test_SUBTRACT_DATES_with_same_date(interp):
    """SUBTRACT-DATES with same date."""
    await interp.run("'2024-01-15' >DATE '2024-01-15' >DATE SUBTRACT-DATES")
    assert interp.stack_pop() == 0


# ========================================
# Edge Cases
# ========================================


@pytest.mark.asyncio
async def test_to_TIME_with_null_returns_null(interp):
    """>TIME with null returns null."""
    await interp.run("NULL >TIME")
    assert interp.stack_pop() is None


@pytest.mark.asyncio
async def test_to_DATE_with_null_returns_null(interp):
    """>DATE with null returns null."""
    await interp.run("NULL >DATE")
    assert interp.stack_pop() is None


@pytest.mark.asyncio
async def test_AM_with_null_returns_null(interp):
    """AM with null returns null."""
    await interp.run("NULL AM")
    assert interp.stack_pop() is None


@pytest.mark.asyncio
async def test_PM_with_null_returns_null(interp):
    """PM with null returns null."""
    await interp.run("NULL PM")
    assert interp.stack_pop() is None


@pytest.mark.asyncio
async def test_ADD_DAYS_with_null_date_returns_null(interp):
    """ADD-DAYS with null date returns null."""
    await interp.run("NULL 5 ADD-DAYS")
    assert interp.stack_pop() is None


@pytest.mark.asyncio
async def test_SUBTRACT_DATES_with_null_dates_returns_null(interp):
    """SUBTRACT-DATES with null dates returns null."""
    await interp.run("NULL '2024-01-15' >DATE SUBTRACT-DATES")
    assert interp.stack_pop() is None


# ========================================
# Integration Tests
# ========================================


@pytest.mark.asyncio
async def test_complex_datetime_workflow(interp):
    """Complex datetime workflow."""
    await interp.run("""
        '2024-01-15' >DATE
        '14:30' >TIME
        AT
        >TIMESTAMP
        TIMESTAMP>DATETIME
        >DATE
        DATE>STR
    """)
    assert interp.stack_pop() == "2024-01-15"


@pytest.mark.asyncio
async def test_date_arithmetic_chain(interp):
    """Date arithmetic chain."""
    await interp.run("""
        TODAY
        7 ADD-DAYS
        14 ADD-DAYS
        TODAY
        SUBTRACT-DATES
    """)
    assert interp.stack_pop() == 21
