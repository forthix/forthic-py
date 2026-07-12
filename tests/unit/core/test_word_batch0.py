"""Batch 0 word-inventory fixes (plans/WORD-INVENTORY.md): the
same-name-different-meaning collisions and contract divergences that had
to be fixed before porting more of the ts vocabulary.

Port of forthic-rs tests/word_batch0_test.rs, extended with the
py-specific items: the underscore-name renames, the +/* arity fixes, and
the stack-effect-driven decorator push.

py note vs the rs file: RANGE lands in Batch 5 (absent here, not a
collision) and FLATTEN is already ts-shaped (verify list).
"""

import pytest

from forthic.interpreter import StandardInterpreter


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


# ===== DROP / SKIP (the worst collision) =====


@pytest.mark.asyncio
async def test_drop_pops_the_stack_ts_semantics():
    # ts core DROP: ( a -- ). The old py DROP meant skip-first-n.
    interp = StandardInterpreter()
    await interp.run("1 2 DROP")
    assert interp.get_stack().get_items() == [1]


@pytest.mark.asyncio
async def test_skip_skips_first_n():
    assert await run("[ 1 2 3 ] 2 SKIP") == [3]


@pytest.mark.asyncio
async def test_classic_pop_is_gone():
    # Classic words with canonical replacements are dropped, not aliased
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="POP"):
        await interp.run("1 POP")


@pytest.mark.asyncio
async def test_classic_identity_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="IDENTITY"):
        await interp.run("IDENTITY")
    interp.reset()
    await interp.run("NOP")  # the canonical no-op remains


# ===== CONCAT (single contract) =====


@pytest.mark.asyncio
async def test_concat_joins_string_arrays():
    assert await run("[ 'a' 'b' 'c' ] CONCAT") == "abc"
    # Null elements become empty strings (ts contract)
    assert await run("[ 'a' NULL 'b' ] CONCAT") == "ab"


@pytest.mark.asyncio
async def test_concat_rejects_two_strings():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match=r"\[s1 s2\] CONCAT"):
        await interp.run("'a' 'b' CONCAT")


# ===== + and * are strictly two-operand =====


@pytest.mark.asyncio
async def test_plus_rejects_arrays_toward_sum():
    # The old array-collapse form `[...] +` is gone: + pops two operands
    # (so a lone array underflows), and an array operand errors toward SUM
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="SUM"):
        await interp.run("0 [ 1 2 3 ] +")
    interp.reset()
    with pytest.raises(Exception, match="Stack underflow"):
        await interp.run("[ 1 2 3 ] +")
    interp.reset()
    await interp.run("[ 1 2 3 ] SUM")
    assert interp.stack_pop() == 6


@pytest.mark.asyncio
async def test_times_rejects_arrays_toward_product():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="PRODUCT"):
        await interp.run("1 [ 2 3 4 ] *")


@pytest.mark.asyncio
async def test_product():
    assert await run("[ 2 3 4 ] PRODUCT") == 24
    # Empty product is 1; a null element nulls the whole result
    # (deliberate ts asymmetry with SUM's null-skipping)
    assert await run("[ ] PRODUCT") == 1
    assert await run("[ 2 NULL ] PRODUCT") is None


@pytest.mark.asyncio
async def test_classic_arithmetic_words_are_gone():
    for word in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]:
        interp = StandardInterpreter()
        with pytest.raises(Exception, match=word):
            await interp.run(f"1 2 {word}")


# ===== MAX / MIN: array-only, null-skipping =====


@pytest.mark.asyncio
async def test_max_min_are_array_only():
    assert await run("[ 1 5 3 ] MAX") == 5
    assert await run("[ 1 5 3 ] MIN") == 1
    # Null elements skipped; empty/all-null -> null
    assert await run("[ 1 NULL 5 ] MAX") == 5
    assert await run("[ ] MAX") is None
    assert await run("[ NULL NULL ] MIN") is None


@pytest.mark.asyncio
async def test_max_min_reject_two_operands():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="requires an array"):
        await interp.run("2 3 MAX")


# ===== APPEND: arrays only, copy-on-write =====


@pytest.mark.asyncio
async def test_append_copies_instead_of_mutating():
    interp = StandardInterpreter()
    original = [1, 2]
    interp.stack_push(original)
    await interp.run("3 APPEND")
    assert interp.stack_pop() == [1, 2, 3]
    assert original == [1, 2], "input must not be mutated"


@pytest.mark.asyncio
async def test_append_rejects_records_toward_jq_bang():
    interp = StandardInterpreter()
    interp.stack_push({"a": 1})
    with pytest.raises(Exception, match="JQ!"):
        await interp.run("[ 'b' 2 ] APPEND")


# ===== LENGTH / STR-LENGTH split =====


@pytest.mark.asyncio
async def test_length_rejects_strings_toward_str_length():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="STR-LENGTH"):
        await interp.run("'hello' LENGTH")
    interp.reset()
    await interp.run("'hello' STR-LENGTH")
    assert interp.stack_pop() == 5
    assert await run("NULL STR-LENGTH") == 0


# ===== Underscore renames: canonical hyphen names serve; old names error =====


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "old_name",
    [
        "GROUP_BY",
        "GROUP_BY_FIELD",
        "GROUPS_OF",
        "BY_FIELD",
        "KEY_OF",
        "ZIP_WITH",
        "RE_MATCH",
        "RE_MATCH_ALL",
        "RE_MATCH_GROUP",
        "URL_ENCODE",
        "URL_DECODE",
        "INVERT_KEYS",
        "REC_DEFAULTS",
        "USE_MODULES",
    ],
)
async def test_underscore_names_are_gone(old_name):
    interp = StandardInterpreter()
    with pytest.raises(Exception, match=old_name.replace("_", "_")):
        await interp.run(old_name)


@pytest.mark.asyncio
async def test_hyphen_names_serve():
    assert await run("[ 1 2 3 4 5 ] 2 GROUPS-OF") == [[1, 2], [3, 4], [5]]
    assert await run("[ 'a' 'b' ] 'b' KEY-OF") == 1
    assert await run("'x y' URL-ENCODE") == "x%20y"


# ===== |REC@ tombstone (never-port: injection-shaped, ts #27) =====


@pytest.mark.asyncio
async def test_pipe_rec_at_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="REC@"):
        await interp.run("[ ] 'key' |REC@")


# ===== Stack-effect-driven push (the decorator contract) =====


@pytest.mark.asyncio
async def test_declared_output_pushes_null():
    # A declared output always pushes — a Python None return is Forthic
    # NULL, not "push nothing" (the old decorator quirk stranded these)
    interp = StandardInterpreter()
    await interp.run("[ ] LAST NULL ==")
    assert interp.stack_pop() is True
    assert len(interp.get_stack()) == 0


@pytest.mark.asyncio
async def test_null_passthrough_words_push_null():
    interp = StandardInterpreter()
    await interp.run("NULL REVERSE")
    assert interp.stack_pop() is None
    assert len(interp.get_stack()) == 0
