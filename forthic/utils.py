"""Utility functions for Forthic."""

from datetime import datetime
from zoneinfo import ZoneInfo


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
