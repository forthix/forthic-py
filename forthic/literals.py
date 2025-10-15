"""Literal handlers for Forthic interpreters.

This module provides literal parsing functions that convert string tokens into typed values.
Includes support for booleans, integers, floats, dates, times, and datetimes.
"""

import re
from collections.abc import Callable
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

# Type alias for literal handlers
LiteralHandler = Callable[[str], bool | int | float | str | date | time | datetime | None]


def to_bool(s: str) -> bool | None:
    """Parse boolean literals: TRUE, FALSE."""
    if s == "TRUE":
        return True
    if s == "FALSE":
        return False
    return None


def to_float(s: str) -> float | None:
    """Parse float literals: 3.14, -2.5, 0.0.

    Must contain a decimal point.
    """
    if "." not in s:
        return None
    try:
        result = float(s)
        return result
    except ValueError:
        return None


def to_int(s: str) -> int | None:
    """Parse integer literals: 42, -10, 0.

    Must not contain a decimal point.
    """
    if "." in s:
        return None
    try:
        result = int(s, 10)
        # Verify it's actually an integer string (not "42abc")
        if str(result) != s:
            return None
        return result
    except ValueError:
        return None


def to_time(s: str) -> time | None:
    """Parse time literals: 9:00, 11:30 PM, 22:15 AM."""
    match = re.match(r"^(\d{1,2}):(\d{2})(?:\s*(AM|PM))?$", s)
    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))
    meridiem = match.group(3)

    # Adjust for AM/PM
    if meridiem == "PM" and hours < 12:
        hours += 12
    elif meridiem == "AM" and hours == 12:
        hours = 0
    elif meridiem == "AM" and hours > 12:
        # Handle invalid cases like "22:15 AM"
        hours -= 12

    if hours > 23 or minutes >= 60:
        return None

    return time(hour=hours, minute=minutes)


def to_literal_date(timezone: ZoneInfo) -> LiteralHandler:
    """Create a date literal handler with timezone support.

    Parses: 2020-06-05, YYYY-MM-DD (with wildcards).
    """

    def handler(s: str) -> date | None:
        match = re.match(r"^(\d{4}|YYYY)-(\d{2}|MM)-(\d{2}|DD)$", s)
        if not match:
            return None

        now = datetime.now(timezone)
        year = now.year if match.group(1) == "YYYY" else int(match.group(1))
        month = now.month if match.group(2) == "MM" else int(match.group(2))
        day = now.day if match.group(3) == "DD" else int(match.group(3))

        try:
            return date(year, month, day)
        except ValueError:
            return None

    return handler


def to_zoned_datetime(timezone: ZoneInfo) -> LiteralHandler:
    """Create a zoned datetime literal handler with timezone support.

    Parses: 2025-05-24T10:15:00Z, 2025-05-24T10:15:00-05:00, 2025-05-24T10:15:00.
    """

    def handler(s: str) -> datetime | None:
        if "T" not in s:
            return None

        try:
            # Handle explicit UTC (Z suffix)
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return dt

            # Handle explicit timezone offset (+05:00, -05:00)
            if re.search(r"[+-]\d{2}:\d{2}$", s):
                dt = datetime.fromisoformat(s)
                return dt

            # No timezone specified, use interpreter's timezone
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone)
            return dt
        except ValueError:
            return None

    return handler
