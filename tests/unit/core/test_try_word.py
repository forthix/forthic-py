"""TRY tests — error handling as data.

Port of forthic-rs tests/try_word_test.rs (mirrored with ts). Rust Result
is the model: Forthic's default propagation is `?`; TRY holds the error as
a value. Law: `'CODE' TRY UNWRAP` ≡ `CODE`. TRY is transactional for the
stack; MAP's outcomes option owns per-element error tolerance (TRY inside
MAP would restore the pushed item and strand it).

py spelling notes: since the Batch 0 rename, py's stack pop is DROP,
matching the rs tests.
"""

import pytest

from forthic.interpreter import StandardInterpreter


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


async def run_all(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.get_stack().get_items()


def error_info_of(outcome):
    assert isinstance(outcome, dict), f"expected outcome record, got {outcome!r}"
    return outcome.get("error")


# ===== TRY basics + the law =====


@pytest.mark.asyncio
async def test_try_wraps_success():
    outcome = await run("5 '2 *' TRY")
    assert outcome == {"ok": 10}


@pytest.mark.asyncio
async def test_law_try_unwrap_equals_code_on_success():
    assert await run("5 '2 *' TRY UNWRAP") == 10


@pytest.mark.asyncio
async def test_law_unwrap_reraises_with_message_and_type():
    interp = StandardInterpreter()
    with pytest.raises(Exception) as exc_info:
        await interp.run("'NO-SUCH-WORD' TRY UNWRAP")
    message = str(exc_info.value)
    assert "NO-SUCH-WORD" in message
    assert "UnknownWordError" in message, f"type preserved: {message}"


@pytest.mark.asyncio
async def test_try_wraps_failure_with_message_and_error_type():
    outcome = await run("'NO-SUCH-WORD' TRY")
    info = error_info_of(outcome)
    assert "NO-SUCH-WORD" in info["message"]
    assert info["error_type"] == "UnknownWordError"


# ===== Transactionality =====


@pytest.mark.asyncio
async def test_try_is_transactional_for_the_stack_on_failure():
    # The failing code consumes 2 and would have kept going; afterwards the
    # stack must be exactly [1, 2, outcome]
    stack = await run_all("1 2 'DROP DROP NO-SUCH-WORD' TRY")
    assert len(stack) == 3
    assert stack[0] == 1
    assert stack[1] == 2
    assert error_info_of(stack[2]) is not None


@pytest.mark.asyncio
async def test_try_does_not_roll_back_side_effects():
    # catch_unwind semantics: the variable write before the failure persists
    assert await run("'42 .written ! NO-SUCH-WORD' TRY DROP .written @") == 42


@pytest.mark.asyncio
async def test_try_unwinds_modules_left_open_by_failed_code():
    interp = StandardInterpreter()
    await interp.run("'{my-mod NO-SUCH-WORD' TRY")
    outcome = interp.stack_pop()
    assert error_info_of(outcome) is not None
    # The module the failed code left open was unwound: we're back at the
    # app module (depth 1) and the interpreter stays usable
    assert interp.module_stack_depth() == 1
    await interp.run("40 2 +")
    assert interp.stack_pop() == 42


@pytest.mark.asyncio
async def test_try_success_consumes_inputs_legitimately():
    stack = await run_all("1 2 '+' TRY")
    assert stack == [{"ok": 3}]


@pytest.mark.asyncio
async def test_try_net_zero_code_succeeds_with_ok_null():
    outcome = await run("'1 DROP' TRY")
    assert outcome == {"ok": None}


# ===== OK? / ERROR? / UNWRAP-OR =====


@pytest.mark.asyncio
async def test_ok_and_error_discriminate():
    assert await run("'1' TRY OK?") is True
    assert await run("'1' TRY ERROR?") is False
    assert await run("'NO-SUCH-WORD' TRY OK?") is False
    assert await run("'NO-SUCH-WORD' TRY ERROR?") is True


@pytest.mark.asyncio
async def test_unwrap_or_fallbacks():
    assert await run("'5' TRY 0 UNWRAP-OR") == 5
    assert await run("'NO-SUCH-WORD' TRY 0 UNWRAP-OR") == 0


@pytest.mark.asyncio
async def test_unwrap_or_ok_null_beats_default():
    # Failure is not nullness
    assert await run("'NULL' TRY 99 UNWRAP-OR") is None


@pytest.mark.asyncio
async def test_unwrap_is_structural():
    # Hand-built ok records participate (records are records)
    assert await run("[ [ 'ok' 7 ] ] REC UNWRAP") == 7


@pytest.mark.asyncio
async def test_unwrap_rejects_non_outcomes():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="outcome record"):
        await interp.run("[ [ 'other' 1 ] ] REC UNWRAP")


# ===== MAP outcomes (option A) =====


@pytest.mark.asyncio
async def test_map_outcomes_wraps_successes():
    result = await run("[ 1 2 ] '2 *' [ .outcomes TRUE ] ~> MAP")
    assert result == [{"ok": 2}, {"ok": 4}]


@pytest.mark.asyncio
async def test_map_outcomes_failures_strand_nothing():
    stack = await run_all("[ 1 2 ] 'NO-SUCH-WORD' [ .outcomes TRUE ] ~> MAP")
    # MAP owns its pushes: exactly one result container, nothing stranded
    assert len(stack) == 1
    items = stack[0]
    assert len(items) == 2
    for item in items:
        assert error_info_of(item)["error_type"] == "UnknownWordError"


@pytest.mark.asyncio
async def test_map_outcomes_mixes_success_and_failure():
    # Items that are themselves Forthic strings: mapping with bare 'TRY'
    # works (the item IS TRY's code argument, so TRY consumes it), and the
    # garbage item yields an error outcome without aborting the map
    stack = await run_all("[ '5' 'NO-SUCH-WORD' ] 'TRY' MAP")
    assert len(stack) == 1
    items = stack[0]
    assert items[0] == {"ok": 5}
    assert error_info_of(items[1]) is not None


@pytest.mark.asyncio
async def test_map_outcomes_with_depth():
    result = await run("[ [ 1 2 ] 5 ] '2 *' [ .depth 1 .outcomes TRUE ] ~> MAP")
    assert result[0] == [{"ok": 2}, {"ok": 4}]
    # Scalar leaf at depth is also wrapped
    assert result[1] == {"ok": 10}


@pytest.mark.asyncio
async def test_try_inside_map_restores_items_the_documented_reason_for_outcomes():
    # TRY is transactional: its snapshot includes the item MAP pushed, so a
    # failing element is faithfully restored... beneath the outcome record.
    # Correct TRY behavior, wrong tool for mapping — use outcomes mode.
    stack = await run_all("[ 1 2 ] \"'NO-SUCH-WORD' TRY\" MAP")
    assert len(stack) == 3, "restored items + result array"
    assert stack[0] == 1
    assert stack[1] == 2
    assert error_info_of(stack[2][0]) is not None
