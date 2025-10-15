"""Tests for literal handlers."""


from forthic import to_bool, to_float, to_int


class TestBoolLiterals:
    """Test boolean literal parsing."""

    def test_true(self) -> None:
        assert to_bool("TRUE") is True

    def test_false(self) -> None:
        assert to_bool("FALSE") is False

    def test_non_bool(self) -> None:
        assert to_bool("true") is None
        assert to_bool("false") is None
        assert to_bool("True") is None
        assert to_bool("1") is None


class TestIntLiterals:
    """Test integer literal parsing."""

    def test_positive_int(self) -> None:
        assert to_int("42") == 42

    def test_negative_int(self) -> None:
        assert to_int("-10") == -10

    def test_zero(self) -> None:
        assert to_int("0") == 0

    def test_not_int_with_decimal(self) -> None:
        assert to_int("3.14") is None

    def test_not_int_invalid(self) -> None:
        assert to_int("abc") is None
        assert to_int("12abc") is None


class TestFloatLiterals:
    """Test float literal parsing."""

    def test_positive_float(self) -> None:
        assert to_float("3.14") == 3.14

    def test_negative_float(self) -> None:
        assert to_float("-2.5") == -2.5

    def test_zero_float(self) -> None:
        assert to_float("0.0") == 0.0

    def test_not_float_no_decimal(self) -> None:
        assert to_float("42") is None

    def test_not_float_invalid(self) -> None:
        assert to_float("abc") is None
