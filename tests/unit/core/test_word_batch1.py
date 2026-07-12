"""Batch 1 words: control flow, predicates, membership, debug.

Port of forthic-rs tests/word_batch1_test.rs (post-scrub ts contracts).

py adaptations: the EMPTY? record case builds an empty record directly
(rs used DELETE, which lands in Batch 3 here); NaN/Infinity are pushed as
Python floats.
"""

import math

import pytest

from forthic.errors import IntentionalStopError
from forthic.interpreter import StandardInterpreter


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


# ===== RUN =====


@pytest.mark.asyncio
async def test_run_executes_in_current_context():
    assert await run("'40 2 +' RUN") == 42
    # Shares interpreter scope
    assert await run("7 .x ! '.x @' RUN") == 7


@pytest.mark.asyncio
async def test_run_null_and_empty_are_noops():
    interp = StandardInterpreter()
    await interp.run("1 NULL RUN '' RUN")
    assert interp.get_stack().get_items() == [1]


@pytest.mark.asyncio
async def test_classic_interpret_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="INTERPRET"):
        await interp.run("'1' INTERPRET")


# ===== IF / IF-RUN / WHEN =====


@pytest.mark.asyncio
async def test_if_is_pure_value_selection():
    assert await run("TRUE 1 2 IF") == 1
    assert await run("FALSE 1 2 IF") == 2
    # The post-scrub contract: IF does NOT execute — strings stay strings
    assert await run("TRUE '1 +' 'x' IF") == "1 +"


@pytest.mark.asyncio
async def test_if_uses_js_truthiness():
    assert await run("0 1 2 IF") == 2
    assert await run("'' 1 2 IF") == 2
    assert await run("NULL 1 2 IF") == 2
    # Empty arrays are TRUTHY (JS Boolean([]) === true)
    assert await run("[ ] 1 2 IF") == 1


@pytest.mark.asyncio
async def test_if_run_executes_the_chosen_branch():
    assert await run("TRUE '40 2 +' '0' IF-RUN") == 42
    assert await run("FALSE '40 2 +' '0' IF-RUN") == 0


@pytest.mark.asyncio
async def test_if_run_null_branch_is_noop():
    interp = StandardInterpreter()
    await interp.run("9 FALSE '1' NULL IF-RUN")
    assert interp.get_stack().get_items() == [9]


@pytest.mark.asyncio
async def test_when_runs_only_on_truthy():
    assert await run("1 TRUE '10 *' WHEN") == 10
    assert await run("1 FALSE '10 *' WHEN") == 1


# ===== DEFAULT-RUN =====


@pytest.mark.asyncio
async def test_default_run_is_lazy():
    # Non-empty value: forthic never runs
    assert await run("5 'NO-SUCH-WORD' DEFAULT-RUN") == 5
    # NULL and "" trigger the default computation
    assert await run("NULL '40 2 +' DEFAULT-RUN") == 42
    assert await run("'' '40 2 +' DEFAULT-RUN") == 42


@pytest.mark.asyncio
async def test_classic_star_default_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match=r"\*DEFAULT"):
        await interp.run("NULL '1' *DEFAULT")


# ===== Predicates =====


@pytest.mark.asyncio
async def test_null_q():
    assert await run("NULL NULL?") is True
    assert await run("0 NULL?") is False
    assert await run("'' NULL?") is False


@pytest.mark.asyncio
async def test_empty_q():
    assert await run("NULL EMPTY?") is True
    assert await run("'' EMPTY?") is True
    assert await run("[ ] EMPTY?") is True
    assert await run("[ ] REC EMPTY?") is True
    assert await run("'x' EMPTY?") is False
    assert await run("[ 1 ] EMPTY?") is False
    assert await run("0 EMPTY?") is False


@pytest.mark.asyncio
async def test_string_q_and_record_q():
    assert await run("'x' STRING?") is True
    assert await run("1 STRING?") is False
    assert await run("[ [ 'a' 1 ] ] REC RECORD?") is True
    assert await run("[ 1 ] RECORD?") is False
    assert await run("NULL RECORD?") is False


@pytest.mark.asyncio
async def test_number_q_infinity_yes_nan_no():
    # ts #31 contract
    assert await run("42 NUMBER?") is True
    assert await run("3.25 NUMBER?") is True
    assert await run("'42' NUMBER?") is False

    interp = StandardInterpreter()
    interp.stack_push(math.inf)
    await interp.run("NUMBER?")
    assert interp.stack_pop() is True
    interp.stack_push(math.nan)
    await interp.run("NUMBER?")
    assert interp.stack_pop() is False


@pytest.mark.asyncio
async def test_number_q_booleans_are_not_numbers():
    # py-specific pin: bool is an int subclass in Python; JS typeof true
    # is "boolean", so NUMBER? must reject it
    assert await run("TRUE NUMBER?") is False


# ===== CONTAINS? / ANY? / ALL? =====


@pytest.mark.asyncio
async def test_contains_q_is_haystack_first():
    assert await run("[ 1 2 3 ] 2 CONTAINS?") is True
    assert await run("[ 1 2 3 ] 9 CONTAINS?") is False
    # Non-array haystack is false, not an error
    assert await run("NULL 2 CONTAINS?") is False


@pytest.mark.asyncio
async def test_classic_in_is_gone():
    # Tombstone: classic item-first IN dropped when CONTAINS? landed
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="IN"):
        await interp.run("2 [ 1 2 ] IN")


@pytest.mark.asyncio
async def test_any_q_and_all_q():
    assert await run("[ FALSE TRUE ] ANY?") is True
    assert await run("[ FALSE FALSE ] ANY?") is False
    assert await run("[ ] ANY?") is False, "any of nothing is false"
    assert await run("[ TRUE TRUE ] ALL?") is True
    assert await run("[ TRUE FALSE ] ALL?") is False
    assert await run("[ ] ALL?") is True, "all of nothing is vacuously true"
    # JS truthiness on elements
    assert await run("[ 1 'x' ] ALL?") is True
    assert await run("[ 1 0 ] ALL?") is False


@pytest.mark.asyncio
async def test_any_q_requires_an_array():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="requires an array"):
        await interp.run("5 ANY?")


# ===== OR / AND arity =====


@pytest.mark.asyncio
async def test_or_and_are_strictly_two_operand():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match=r"ANY\?"):
        await interp.run("FALSE [ TRUE ] OR")
    interp.reset()
    with pytest.raises(Exception, match=r"ALL\?"):
        await interp.run("TRUE [ TRUE ] AND")
    # Two-value form returns the selecting operand (JS || / &&)
    assert await run("NULL 5 OR") == 5
    assert await run("3 5 AND") == 5


# ===== PEEK! / STACK! =====


@pytest.mark.asyncio
async def test_peek_and_stack_stop_intentionally():
    interp = StandardInterpreter()
    with pytest.raises(IntentionalStopError):
        await interp.run("42 PEEK!")
    # The stack survives — PEEK! only peeks
    assert interp.get_stack().get_items() == [42]

    interp = StandardInterpreter()
    with pytest.raises(IntentionalStopError):
        await interp.run("1 2 STACK!")
