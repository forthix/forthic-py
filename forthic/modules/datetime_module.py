"""DateTime module for Forthic.

Date and time operations with timezone-aware datetime manipulation.

Categories:
- Current: TODAY, NOW
- Time adjustment: AM, PM
- Conversion to: >TIME, >DATE, >DATETIME, AT
- Conversion from: TIME>STR, DATE>STR, DATE>INT
- Timestamps: >TIMESTAMP, TIMESTAMP>DATETIME
- Date math: ADD-DAYS, SUBTRACT-DATES

Examples:
    TODAY
    NOW
    "14:30" >TIME
    "2024-01-15" >DATE
    TODAY "14:30" >TIME AT
    TODAY 7 ADD-DAYS
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from ..decorators import DirectWord, Word, DecoratedModule, register_module_doc

if TYPE_CHECKING:
    from ..interpreter import Interpreter


class DateTimeModule(DecoratedModule):
    """DateTime module for Forthic."""

    def __init__(self):
        super().__init__("datetime")
        register_module_doc(
            DateTimeModule,
            """
Date and time operations using Python's datetime with timezone support.

## Categories
- Current: TODAY, NOW
- Time adjustment: AM, PM
- Conversion to: >TIME, >DATE, >DATETIME, AT
- Conversion from: TIME>STR, DATE>STR, DATE>INT
- Timestamps: >TIMESTAMP, TIMESTAMP>DATETIME
- Date math: ADD-DAYS, SUBTRACT-DATES

## Examples
TODAY
NOW
"14:30" >TIME
"2024-01-15" >DATE
TODAY "14:30" >TIME AT
TODAY 7 ADD-DAYS
""",
        )

    @DirectWord("( -- date )", "Get current date", "TODAY")
    async def TODAY(self, interp: Interpreter) -> None:
        """Get current date in interpreter's timezone."""
        tz = interp.get_timezone()
        today = datetime.now(tz).date()
        interp.stack_push(today)

    @DirectWord("( -- datetime )", "Get current datetime", "NOW")
    async def NOW(self, interp: Interpreter) -> None:
        """Get current datetime in interpreter's timezone."""
        tz = interp.get_timezone()
        now = datetime.now(tz)
        interp.stack_push(now)

    @DirectWord("( time -- time )", "Convert time to AM (subtract 12 from hour if >= 12)")
    async def AM(self, interp: Interpreter) -> None:
        """Convert time to AM."""
        t = interp.stack_pop()

        if t is None:
            interp.stack_push(None)
            return
        if not isinstance(t, time):
            interp.stack_push(t)
            return
        if t.hour >= 12:
            interp.stack_push(t.replace(hour=t.hour - 12))
        else:
            interp.stack_push(t)

    @DirectWord("( time -- time )", "Convert time to PM (add 12 to hour if < 12)")
    async def PM(self, interp: Interpreter) -> None:
        """Convert time to PM."""
        t = interp.stack_pop()

        if t is None:
            interp.stack_push(None)
            return
        if not isinstance(t, time):
            interp.stack_push(t)
            return
        if t.hour < 12:
            interp.stack_push(t.replace(hour=t.hour + 12))
        else:
            interp.stack_push(t)

    @DirectWord("( item -- time )", "Convert string or datetime to time", ">TIME")
    async def to_TIME(self, interp: Interpreter) -> None:
        """Convert item to time object."""
        item = interp.stack_pop()

        if item is None:
            interp.stack_push(None)
            return

        # If already a time, return it
        if isinstance(item, time):
            interp.stack_push(item)
            return

        # If it's a datetime, extract the time
        if isinstance(item, datetime):
            interp.stack_push(item.time())
            return

        # Otherwise, parse as string
        str_val = str(item).strip()

        # Handle "HH:MM AM/PM" format
        ampm_match = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", str_val, re.IGNORECASE)
        if ampm_match:
            hour = int(ampm_match.group(1))
            minute = int(ampm_match.group(2))
            meridiem = ampm_match.group(3).upper()

            if meridiem == "PM" and hour < 12:
                hour += 12
            elif meridiem == "AM" and hour == 12:
                hour = 0

            interp.stack_push(time(hour=hour, minute=minute))
            return

        # Try standard time parsing (HH:MM or HH:MM:SS)
        try:
            # Try HH:MM:SS format
            if ":" in str_val:
                parts = str_val.split(":")
                if len(parts) == 2:
                    interp.stack_push(time(hour=int(parts[0]), minute=int(parts[1])))
                    return
                elif len(parts) == 3:
                    interp.stack_push(time(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2])))
                    return
        except (ValueError, IndexError):
            pass

        interp.stack_push(None)

    @DirectWord("( item -- date )", "Convert string or datetime to date", ">DATE")
    async def to_DATE(self, interp: Interpreter) -> None:
        """Convert item to date object."""
        item = interp.stack_pop()

        if item is None:
            interp.stack_push(None)
            return

        # If already a date, return it
        if isinstance(item, date) and not isinstance(item, datetime):
            interp.stack_push(item)
            return

        # If it's a datetime, extract the date
        if isinstance(item, datetime):
            interp.stack_push(item.date())
            return

        # Otherwise, parse as string
        str_val = str(item).strip()

        # Try standard ISO format (YYYY-MM-DD)
        try:
            interp.stack_push(date.fromisoformat(str_val))
            return
        except (ValueError, TypeError):
            pass

        # Try parsing as a more flexible format using dateutil if available
        try:
            from dateutil import parser
            parsed = parser.parse(str_val)
            interp.stack_push(parsed.date())
            return
        except (ImportError, ValueError, TypeError):
            pass

        interp.stack_push(None)

    @DirectWord("( str_or_timestamp -- datetime )", "Convert string or timestamp to datetime", ">DATETIME")
    async def to_DATETIME(self, interp: Interpreter) -> None:
        """Convert item to datetime object."""
        item = interp.stack_pop()
        tz = interp.get_timezone()

        if item is None:
            interp.stack_push(None)
            return

        # If already a datetime, ensure it has timezone info
        if isinstance(item, datetime):
            if item.tzinfo is None:
                # Assume it's in the interpreter's timezone
                interp.stack_push(item.replace(tzinfo=tz))
            else:
                interp.stack_push(item)
            return

        # If it's a number, treat as Unix timestamp (seconds)
        if isinstance(item, (int, float)):
            dt = datetime.fromtimestamp(item, tz=tz)
            interp.stack_push(dt)
            return

        # Otherwise, parse as string
        str_val = str(item).strip()

        try:
            # Try parsing as ISO datetime string
            dt = datetime.fromisoformat(str_val)
            # If no timezone info, assume interpreter's timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            interp.stack_push(dt)
        except (ValueError, TypeError):
            interp.stack_push(None)

    @DirectWord("( date time -- datetime )", "Combine date and time into datetime", "AT")
    async def AT(self, interp: Interpreter) -> None:
        """Combine date and time into datetime."""
        t = interp.stack_pop()
        d = interp.stack_pop()
        tz = interp.get_timezone()

        if d is None or t is None:
            interp.stack_push(None)
            return

        # Create datetime from date and time components
        dt = datetime(
            year=d.year,
            month=d.month,
            day=d.day,
            hour=getattr(t, "hour", 0),
            minute=getattr(t, "minute", 0),
            second=getattr(t, "second", 0),
            microsecond=getattr(t, "microsecond", 0),
            tzinfo=tz,
        )

        interp.stack_push(dt)

    @Word("( time -- str )", "Convert time to HH:MM string", "TIME>STR")
    async def TIME_to_STR(self, t: Any) -> str:
        """Convert time to string."""
        if t is None or not isinstance(t, time):
            return ""

        return f"{t.hour:02d}:{t.minute:02d}"

    @Word("( date -- str )", "Convert date to YYYY-MM-DD string", "DATE>STR")
    async def DATE_to_STR(self, d: Any) -> str:
        """Convert date to string."""
        if d is None:
            return ""

        # Handle datetime objects
        if isinstance(d, datetime):
            d = d.date()

        if not isinstance(d, date):
            return ""

        return d.isoformat()

    @Word("( date -- int )", "Convert date to integer (YYYYMMDD)", "DATE>INT")
    async def DATE_to_INT(self, d: Any) -> Any:
        """Convert date to integer."""
        if d is None:
            return None

        # Handle datetime objects
        if isinstance(d, datetime):
            d = d.date()

        if not isinstance(d, date):
            return None

        return d.year * 10000 + d.month * 100 + d.day

    @DirectWord("( datetime -- timestamp )", "Convert datetime to Unix timestamp (seconds)", ">TIMESTAMP")
    async def to_TIMESTAMP(self, interp: Interpreter) -> None:
        """Convert datetime to Unix timestamp."""
        dt = interp.stack_pop()

        if dt is None:
            interp.stack_push(None)
            return

        if not isinstance(dt, datetime):
            interp.stack_push(None)
            return

        # If datetime is naive, assume interpreter's timezone
        if dt.tzinfo is None:
            tz = interp.get_timezone()
            dt = dt.replace(tzinfo=tz)

        # Convert to Unix timestamp (seconds)
        timestamp = int(dt.timestamp())
        interp.stack_push(timestamp)

    @DirectWord("( timestamp -- datetime )", "Convert Unix timestamp (seconds) to datetime", "TIMESTAMP>DATETIME")
    async def TIMESTAMP_to_DATETIME(self, interp: Interpreter) -> None:
        """Convert Unix timestamp to datetime."""
        timestamp = interp.stack_pop()
        tz = interp.get_timezone()

        if timestamp is None or not isinstance(timestamp, (int, float)):
            interp.stack_push(None)
            return

        # Convert from Unix timestamp (seconds)
        dt = datetime.fromtimestamp(timestamp, tz=tz)
        interp.stack_push(dt)

    @DirectWord("( date num_days -- date )", "Add days to a date", "ADD-DAYS")
    async def ADD_DAYS(self, interp: Interpreter) -> None:
        """Add days to a date."""
        num_days = interp.stack_pop()
        d = interp.stack_pop()

        if d is None or num_days is None:
            interp.stack_push(None)
            return

        # Handle datetime objects
        if isinstance(d, datetime):
            result = d + timedelta(days=num_days)
            interp.stack_push(result.date())
            return

        if not isinstance(d, date):
            interp.stack_push(None)
            return

        interp.stack_push(d + timedelta(days=num_days))

    @DirectWord("( date1 date2 -- num_days )", "Get difference in days between dates (date1 - date2)", "SUBTRACT-DATES")
    async def SUBTRACT_DATES(self, interp: Interpreter) -> None:
        """Calculate difference in days between two dates."""
        date2 = interp.stack_pop()
        date1 = interp.stack_pop()

        if date1 is None or date2 is None:
            interp.stack_push(None)
            return

        # Handle datetime objects
        if isinstance(date1, datetime):
            date1 = date1.date()
        if isinstance(date2, datetime):
            date2 = date2.date()

        if not isinstance(date1, date) or not isinstance(date2, date):
            interp.stack_push(None)
            return

        # Get the difference: date1 - date2
        delta = date1 - date2
        interp.stack_push(delta.days)
