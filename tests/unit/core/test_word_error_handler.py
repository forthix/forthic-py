"""Tests for per-word error handler functionality."""

import pytest

from forthic.errors import IntentionalStopError
from forthic.interpreter import Interpreter
from forthic.module import ModuleWord


@pytest.mark.asyncio
async def test_add_and_execute_error_handler():
    """Error handler should be called when word throws error."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise ValueError("Test error")

    word = ModuleWord("TEST", failing_handler)

    handler_called = False

    async def error_handler(error, word, interp):
        nonlocal handler_called
        handler_called = True

    word.add_error_handler(error_handler)

    await word.execute(interp)
    assert handler_called is True


@pytest.mark.asyncio
async def test_suppress_error_if_handler_succeeds():
    """Error should be suppressed if handler succeeds."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise ValueError("Test error")

    word = ModuleWord("TEST", failing_handler)

    async def error_handler(error, word, interp):
        # Handler succeeds - error should be suppressed
        pass

    word.add_error_handler(error_handler)

    # Should not raise
    await word.execute(interp)


@pytest.mark.asyncio
async def test_try_handlers_in_order():
    """Handlers should be tried in order until one succeeds."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise ValueError("Test error")

    word = ModuleWord("TEST", failing_handler)

    calls = []

    async def handler1(error, word, interp):
        calls.append(1)
        raise ValueError("Handler 1 failed")

    async def handler2(error, word, interp):
        calls.append(2)
        # Handler 2 succeeds

    async def handler3(error, word, interp):
        calls.append(3)
        # Should not be called

    word.add_error_handler(handler1)
    word.add_error_handler(handler2)
    word.add_error_handler(handler3)

    await word.execute(interp)
    assert calls == [1, 2]  # Handler 3 not called


@pytest.mark.asyncio
async def test_rethrow_if_all_handlers_fail():
    """Original error should be re-thrown if all handlers fail."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise ValueError("Original error")

    word = ModuleWord("TEST", failing_handler)

    async def error_handler(error, word, interp):
        raise ValueError("Handler failed")

    word.add_error_handler(error_handler)

    with pytest.raises(ValueError, match="Original error"):
        await word.execute(interp)


@pytest.mark.asyncio
async def test_never_handle_intentional_stop():
    """IntentionalStopError should never be handled."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise IntentionalStopError()

    word = ModuleWord("TEST", failing_handler)

    handler_called = False

    async def error_handler(error, word, interp):
        nonlocal handler_called
        handler_called = True

    word.add_error_handler(error_handler)

    with pytest.raises(IntentionalStopError):
        await word.execute(interp)

    assert handler_called is False


@pytest.mark.asyncio
async def test_handler_receives_error_word_interp():
    """Handler should receive error, word, and interpreter."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise ValueError("Test error")

    word = ModuleWord("TEST", failing_handler)

    received_error = None
    received_word = None
    received_interp = None

    async def error_handler(error, word, interp):
        nonlocal received_error, received_word, received_interp
        received_error = error
        received_word = word
        received_interp = interp

    word.add_error_handler(error_handler)

    await word.execute(interp)

    assert isinstance(received_error, ValueError)
    assert received_error.args[0] == "Test error"
    assert received_word.name == "TEST"
    assert received_interp is interp


def test_remove_handler():
    """Should be able to remove a specific handler."""
    word = ModuleWord("TEST", lambda i: None)

    async def handler(error, word, interp):
        pass

    word.add_error_handler(handler)
    assert len(word.get_error_handlers()) == 1

    word.remove_error_handler(handler)
    assert len(word.get_error_handlers()) == 0


def test_clear_handlers():
    """Should be able to clear all handlers."""
    word = ModuleWord("TEST", lambda i: None)

    async def handler1(error, word, interp):
        pass

    async def handler2(error, word, interp):
        pass

    word.add_error_handler(handler1)
    word.add_error_handler(handler2)
    assert len(word.get_error_handlers()) == 2

    word.clear_error_handlers()
    assert len(word.get_error_handlers()) == 0


def test_get_handlers_returns_copy():
    """get_error_handlers should return a copy, not original list."""
    word = ModuleWord("TEST", lambda i: None)

    async def handler(error, word, interp):
        pass

    word.add_error_handler(handler)

    handlers = word.get_error_handlers()
    handlers.clear()

    # Original should still have handler
    assert len(word.get_error_handlers()) == 1


@pytest.mark.asyncio
async def test_multiple_errors_multiple_handlers():
    """Test complex scenario with multiple failures and handlers."""
    interp = Interpreter()

    async def failing_handler(interp):
        raise RuntimeError("Main error")

    word = ModuleWord("TEST", failing_handler)

    attempts = []

    async def handler1(error, word, interp):
        attempts.append("handler1")
        raise ValueError("Handler 1 cannot handle RuntimeError")

    async def handler2(error, word, interp):
        attempts.append("handler2")
        # Handler 2 can handle it
        interp.stack_push("Recovered")

    word.add_error_handler(handler1)
    word.add_error_handler(handler2)

    await word.execute(interp)

    assert attempts == ["handler1", "handler2"]
    assert interp.stack_pop() == "Recovered"


@pytest.mark.asyncio
async def test_error_handler_can_manipulate_stack():
    """Error handlers can manipulate the stack for recovery."""
    interp = Interpreter()
    interp.stack_push("initial")

    async def failing_handler(interp):
        interp.stack_push("partial")
        raise ValueError("Computation failed")

    word = ModuleWord("TEST", failing_handler)

    async def recovery_handler(error, word, interp):
        # Clean up partial state
        interp.stack_pop()  # Remove "partial"
        # Push default value
        interp.stack_push("default")

    word.add_error_handler(recovery_handler)

    await word.execute(interp)

    # Stack should have: ["initial", "default"]
    assert interp.stack_pop() == "default"
    assert interp.stack_pop() == "initial"


@pytest.mark.asyncio
async def test_no_error_handlers_work_normally():
    """Words without error handlers should work normally."""
    interp = Interpreter()

    async def normal_handler(interp):
        interp.stack_push(42)

    word = ModuleWord("TEST", normal_handler)

    # No error handlers
    assert len(word.get_error_handlers()) == 0

    await word.execute(interp)
    assert interp.stack_pop() == 42


@pytest.mark.asyncio
async def test_error_handler_sees_correct_error_type():
    """Error handler should receive the original error type."""
    interp = Interpreter()

    class CustomError(Exception):
        pass

    async def failing_handler(interp):
        raise CustomError("Custom error message")

    word = ModuleWord("TEST", failing_handler)

    received_error = None

    async def error_handler(error, word, interp):
        nonlocal received_error
        received_error = error

    word.add_error_handler(error_handler)

    await word.execute(interp)

    assert isinstance(received_error, CustomError)
    assert str(received_error) == "Custom error message"


@pytest.mark.asyncio
async def test_remove_nonexistent_handler_does_not_error():
    """Removing a handler that doesn't exist should not raise."""
    word = ModuleWord("TEST", lambda i: None)

    async def handler(error, word, interp):
        pass

    # Should not raise
    word.remove_error_handler(handler)
    assert len(word.get_error_handlers()) == 0
