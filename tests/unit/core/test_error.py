"""Tests for Forthic error handling."""

import pytest

from forthic import (
    ExtraSemicolonError,
    ForthicError,
    MissingSemicolonError,
    StackUnderflowError,
    StandardInterpreter,
    UnknownWordError,
    WordExecutionError,
)
from forthic.errors import get_error_description


class TestErrorHandling:
    """Test error handling and error messages."""

    @pytest.mark.asyncio
    async def test_unknown_word_error(self) -> None:
        """Test unknown word error."""
        interp = StandardInterpreter()
        forthic = "1 2 3 GARBAGE +"

        with pytest.raises(UnknownWordError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_stack_underflow_error(self) -> None:
        """Test stack underflow error."""
        interp = StandardInterpreter()
        forthic = "1 + 3 2 *"

        with pytest.raises(StackUnderflowError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_word_execution_error(self) -> None:
        """Test word execution error."""
        interp = StandardInterpreter()
        forthic = """: ADD   +;
  1 ADD 2 *"""

        with pytest.raises(WordExecutionError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_missing_semicolon_error(self) -> None:
        """Test missing semicolon error."""
        interp = StandardInterpreter()
        forthic = """: ADD   +
  : MUL   *;"""

        with pytest.raises(MissingSemicolonError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_extra_semicolon_error(self) -> None:
        """Test extra semicolon error."""
        interp = StandardInterpreter()
        forthic = """: ADD   +;
[1 2 3];"""

        with pytest.raises(ExtraSemicolonError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_errors_in_map(self) -> None:
        """Test errors in MAP operation."""
        interp = StandardInterpreter()
        forthic = """: ADD   +;
  [1 2 3] "ADD" MAP"""

        with pytest.raises(ForthicError):
            await interp.run(forthic)

    @pytest.mark.asyncio
    async def test_word_execution_error_tracks_locations(self) -> None:
        """Test WordExecutionError tracks both call and definition locations."""
        interp = StandardInterpreter()
        forthic = """: ADD   +;
  1 ADD 2 *"""

        with pytest.raises(WordExecutionError) as exc_info:
            await interp.run(forthic)

        error = exc_info.value

        # Call location should be where ADD was called (line 2)
        assert error.location is not None
        assert error.location.line == 2

        # Definition location should be where + was in the definition (line 1)
        def_loc = error.get_definition_location()
        assert def_loc is not None
        assert def_loc.line == 1

        # Both should have no source (not in a module)
        assert error.location.source is None
        assert def_loc.source is None

    @pytest.mark.asyncio
    async def test_word_execution_error_dual_location_formatting(self) -> None:
        """Test WordExecutionError shows dual-location error formatting."""
        interp = StandardInterpreter()
        forthic = """: ADD   +;
  1 ADD 2 *"""

        with pytest.raises(WordExecutionError) as exc_info:
            await interp.run(forthic)

        error = exc_info.value
        description = get_error_description(forthic, error)

        # Should contain both "at line" (definition) and "Called from" (call site)
        assert "at line 1" in description
        assert "Called from line 2" in description

        # Should contain caret highlighting (^^^)
        assert "^" in description
