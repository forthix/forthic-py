"""Tests for Forthic utility functions."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo


class TestUtils:
    """Test utility functions."""

    def test_to_zoned_datetime(self) -> None:
        """Test to_zoned_datetime function."""
        from forthic.utils import to_zoned_datetime

        date = to_zoned_datetime("2025-06-07T13:00:00", "America/Los_Angeles")

        assert date is not None
        assert date.year == 2025
        assert date.month == 6
        assert date.day == 7
        assert date.hour == 13
        assert date.minute == 0
        assert date.second == 0
