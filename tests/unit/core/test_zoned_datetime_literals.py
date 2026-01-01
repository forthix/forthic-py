"""Tests for zoned datetime literal parsing."""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from forthic.literals import to_zoned_datetime


class TestZonedDatetimeLiterals:
    """Test zoned datetime literal parsing with IANA timezone bracket notation."""

    def test_parse_utc_with_z(self):
        """Parse UTC datetime with Z suffix."""
        handler = to_zoned_datetime(ZoneInfo("America/New_York"))
        dt = handler("2025-05-24T10:15:00Z")

        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 10
        assert dt.minute == 15

    def test_parse_iana_bracket_notation(self):
        """Parse IANA timezone with bracket notation."""
        handler = to_zoned_datetime(ZoneInfo("America/New_York"))
        dt = handler("2025-05-20T08:00:00[America/Los_Angeles]")

        assert dt is not None
        assert dt.tzinfo == ZoneInfo("America/Los_Angeles")
        assert dt.hour == 8
        assert dt.minute == 0

    def test_parse_offset_and_iana_bracket(self):
        """Parse datetime with offset and IANA timezone in brackets."""
        handler = to_zoned_datetime(ZoneInfo("America/New_York"))
        dt = handler("2025-05-20T08:00:00-07:00[America/Los_Angeles]")

        assert dt is not None
        # Should be converted to Los Angeles timezone
        assert dt.tzinfo == ZoneInfo("America/Los_Angeles")
        assert dt.hour == 8

    def test_parse_offset_only(self):
        """Parse datetime with offset only (no IANA timezone)."""
        handler = to_zoned_datetime(ZoneInfo("America/New_York"))
        dt = handler("2025-05-24T10:15:00-05:00")

        assert dt is not None
        assert dt.tzinfo is not None  # Has timezone info
        assert dt.hour == 10

    def test_parse_no_timezone_uses_default(self):
        """Parse datetime without timezone uses default timezone."""
        handler = to_zoned_datetime(ZoneInfo("America/Los_Angeles"))
        dt = handler("2025-05-24T10:15:00")

        assert dt is not None
        assert dt.tzinfo == ZoneInfo("America/Los_Angeles")
        assert dt.hour == 10

    def test_different_iana_timezones(self):
        """Test various IANA timezone identifiers."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        # Europe/London
        dt1 = handler("2025-05-20T14:30:00[Europe/London]")
        assert dt1 is not None
        assert dt1.tzinfo == ZoneInfo("Europe/London")

        # Asia/Tokyo
        dt2 = handler("2025-05-20T09:00:00[Asia/Tokyo]")
        assert dt2 is not None
        assert dt2.tzinfo == ZoneInfo("Asia/Tokyo")

        # Australia/Sydney
        dt3 = handler("2025-05-20T18:00:00[Australia/Sydney]")
        assert dt3 is not None
        assert dt3.tzinfo == ZoneInfo("Australia/Sydney")

    def test_invalid_timezone_returns_none(self):
        """Invalid IANA timezone should return None."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))
        dt = handler("2025-05-20T08:00:00[Invalid/Timezone]")

        assert dt is None

    def test_no_t_returns_none(self):
        """Strings without 'T' should return None."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        assert handler("2025-05-20") is None
        assert handler("regular-word") is None
        assert handler("08:00:00") is None

    def test_malformed_datetime_returns_none(self):
        """Malformed datetime strings should return None."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        assert handler("2025-13-45T10:15:00") is None  # Invalid month/day
        assert handler("not-a-datetime[America/Los_Angeles]") is None
        assert handler("2025-05-20T25:00:00") is None  # Invalid hour

    def test_bracket_without_datetime_returns_none(self):
        """Brackets without datetime should return None."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        assert handler("[America/Los_Angeles]") is None
        assert handler("word[bracket]") is None

    def test_unclosed_bracket_returns_none(self):
        """Unclosed bracket should return None."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        assert handler("2025-05-20T08:00:00[America/Los_Angeles") is None

    def test_with_seconds(self):
        """Parse datetime with seconds."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))
        dt = handler("2025-05-20T08:30:45[America/Los_Angeles]")

        assert dt is not None
        assert dt.hour == 8
        assert dt.minute == 30
        assert dt.second == 45

    def test_with_microseconds(self):
        """Parse datetime with microseconds."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))
        dt = handler("2025-05-20T08:30:45.123456[America/Los_Angeles]")

        assert dt is not None
        assert dt.hour == 8
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.microsecond == 123456

    def test_utc_z_with_bracket_iana(self):
        """Parse UTC (Z) datetime with IANA timezone in brackets."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))
        dt = handler("2025-05-20T08:00:00Z[UTC]")

        assert dt is not None
        assert dt.tzinfo == ZoneInfo("UTC")

    def test_conversion_preserves_instant(self):
        """Converting to different timezone preserves the instant in time."""
        handler = to_zoned_datetime(ZoneInfo("UTC"))

        # 8 AM in Los Angeles = 4 PM UTC (during daylight saving)
        # Note: Actual offset depends on the date and DST rules
        dt = handler("2025-05-20T08:00:00[America/Los_Angeles]")

        assert dt is not None
        # Convert to UTC to verify it's the same instant
        dt_utc = dt.astimezone(timezone.utc)
        # 8 AM PDT (UTC-7) = 3 PM UTC
        assert dt_utc.hour == 15  # 8 + 7 = 15 (3 PM)


class TestTokenizerIntegration:
    """Test that tokenizer properly handles bracket notation."""

    @pytest.mark.asyncio
    async def test_tokenizer_includes_brackets_for_datetime(self):
        """Tokenizer should include brackets when token contains 'T'."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()
        await interp.run("2025-05-20T08:00:00[America/Los_Angeles]")

        # Should push a datetime object
        result = interp.stack_pop()
        assert isinstance(result, datetime)
        assert result.tzinfo == ZoneInfo("America/Los_Angeles")
        assert result.hour == 8

    @pytest.mark.asyncio
    async def test_tokenizer_array_brackets_still_work(self):
        """Arrays with brackets should still work normally."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()
        await interp.run("[1 2 3]")

        # Should push an array
        result = interp.stack_pop()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_datetime_in_array(self):
        """Zoned datetime in array should parse correctly."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()
        await interp.run("[2025-05-20T08:00:00[America/Los_Angeles] 42]")

        # Should push an array with datetime and number
        result = interp.stack_pop()
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], datetime)
        assert result[0].tzinfo == ZoneInfo("America/Los_Angeles")
        assert result[1] == 42

    @pytest.mark.asyncio
    async def test_multiple_zoned_datetimes(self):
        """Multiple zoned datetimes should all parse correctly."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()
        await interp.run(
            "2025-05-20T08:00:00[America/Los_Angeles] "
            "2025-05-20T14:00:00[Europe/London]"
        )

        # Should push two datetimes
        dt2 = interp.stack_pop()
        dt1 = interp.stack_pop()

        assert isinstance(dt1, datetime)
        assert dt1.tzinfo == ZoneInfo("America/Los_Angeles")

        assert isinstance(dt2, datetime)
        assert dt2.tzinfo == ZoneInfo("Europe/London")

    @pytest.mark.asyncio
    async def test_zoned_datetime_as_value(self):
        """Zoned datetimes should be pushed as datetime objects."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()
        # Push datetime
        await interp.run("2025-05-20T08:30:45[America/Los_Angeles]")

        # Should push a datetime object that can be manipulated
        result = interp.stack_pop()
        assert isinstance(result, datetime)
        assert result.tzinfo == ZoneInfo("America/Los_Angeles")
        assert result.hour == 8
        assert result.minute == 30
        assert result.second == 45
