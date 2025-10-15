"""Tests for Forthic word options."""

import pytest

from forthic import WordOptions


class TestWordOptions:
    """Test WordOptions functionality."""

    def test_creates_from_flat_array(self) -> None:
        """Test creating WordOptions from flat array."""
        opts = WordOptions(["depth", 2, "with_key", True])
        assert opts.get("depth") == 2
        assert opts.get("with_key") is True

    def test_requires_array_input(self) -> None:
        """Test that WordOptions requires array input."""
        with pytest.raises(Exception) as exc_info:
            WordOptions("not an array")  # type: ignore

        assert "must be an array" in str(exc_info.value)

    def test_requires_even_number_of_elements(self) -> None:
        """Test that WordOptions requires even number of elements."""
        with pytest.raises(Exception) as exc_info:
            WordOptions(["depth", 2, "with_key"])

        assert "even length" in str(exc_info.value)

    def test_requires_string_keys(self) -> None:
        """Test that WordOptions requires string keys."""
        with pytest.raises(Exception) as exc_info:
            WordOptions([123, "value"])  # type: ignore

        assert "must be a string" in str(exc_info.value)

    def test_returns_default_for_missing_key(self) -> None:
        """Test returning default for missing key."""
        opts = WordOptions(["depth", 2])
        assert opts.get("missing") is None
        assert opts.get("missing", "default") == "default"

    def test_has_checks_key_existence(self) -> None:
        """Test has() checks key existence."""
        opts = WordOptions(["depth", 2])
        assert opts.has("depth") is True
        assert opts.has("missing") is False

    def test_to_dict_converts_to_plain_object(self) -> None:
        """Test to_dict() converts to plain object."""
        opts = WordOptions(["depth", 2, "with_key", True])
        assert opts.to_dict() == {"depth": 2, "with_key": True}

    def test_keys_returns_all_option_keys(self) -> None:
        """Test keys() returns all option keys."""
        opts = WordOptions(["depth", 2, "with_key", True])
        assert sorted(opts.keys()) == ["depth", "with_key"]

    def test_later_values_override_earlier_ones(self) -> None:
        """Test later values override earlier ones."""
        opts = WordOptions(["depth", 2, "depth", 3])
        assert opts.get("depth") == 3

    def test_handles_null_and_undefined_values(self) -> None:
        """Test handling null and undefined values."""
        opts = WordOptions(["key1", None, "key2", None])
        assert opts.get("key1") is None
        assert opts.get("key2") is None
        assert opts.has("key1") is True
        assert opts.has("key2") is True

    def test_handles_complex_values(self) -> None:
        """Test handling complex values."""
        complex_value = {"nested": {"data": [1, 2, 3]}}
        opts = WordOptions(["config", complex_value])
        assert opts.get("config") == complex_value

    def test_to_string_formats_nicely(self) -> None:
        """Test toString() formats nicely."""
        opts = WordOptions(["depth", 2, "with_key", True])
        string = str(opts)
        assert "WordOptions" in string
        assert ".depth" in string
        assert ".with_key" in string

    def test_empty_options_array(self) -> None:
        """Test empty options array."""
        opts = WordOptions([])
        assert opts.keys() == []
        assert opts.to_dict() == {}
        assert opts.has("anything") is False
