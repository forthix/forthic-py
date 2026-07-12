"""Batch 3 words: records & JQ paths.

Port of forthic-rs tests/word_batch3_test.rs. Documented divergences from
ts: records iterate/index/enumerate in INSERTION order (ts sorted keys as
a JS-object-order workaround pre-scrub); strict integer parsing in [n];
OMIT stringifies drop keys.
"""

import pytest

from forthic.interpreter import StandardInterpreter

# users: [{name: alice, tags: [a b]}, {name: bob, tags: [c]}]
USERS = (
    "[ [ [ 'name' 'alice' ] [ 'tags' [ 'a' 'b' ] ] ] REC "
    "[ [ 'name' 'bob' ] [ 'tags' [ 'c' ] ] ] REC ]"
)


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


async def run_code_on(value, code: str):
    interp = StandardInterpreter()
    interp.stack_push(value)
    await interp.run(code)
    return interp.stack_pop()


# ===== JQ@ =====


@pytest.mark.asyncio
async def test_jq_at_string_paths():
    assert await run("[ [ 'a' [ [ 'b' 7 ] ] REC ] ] REC 'a.b' JQ@") == 7
    assert await run(f"{USERS} '[0].name' JQ@") == "alice"
    assert await run("[ 10 20 30 ] '[-1]' JQ@") == 30
    # Quoted keys for names with dots/brackets
    assert await run("[ [ 'a.b' 5 ] ] REC '[\"a.b\"]' JQ@") == 5


@pytest.mark.asyncio
async def test_jq_at_misses_are_null():
    assert await run("[ [ 'a' 1 ] ] REC 'zzz' JQ@") is None
    assert await run("[ [ 'a' 1 ] ] REC 'a.b.c' JQ@") is None
    assert await run("[ 1 ] '[9]' JQ@") is None
    assert await run("NULL 'a' JQ@") is None


@pytest.mark.asyncio
async def test_jq_at_iterate_flattens_conditionally():
    # Single []: one level of mapping, flat result
    assert await run(f"{USERS} '[].name' JQ@") == ["alice", "bob"]
    # .[].tags -> array of arrays (no later iterate)
    assert await run(f"{USERS} '[].tags' JQ@") == [["a", "b"], ["c"]]
    # .[].tags[] -> flattened
    assert await run(f"{USERS} '[].tags[]' JQ@") == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_jq_at_array_paths_are_dynamic_keys():
    assert await run(f"{USERS} [ 0 'tags' 1 ] JQ@") == "b"


@pytest.mark.asyncio
async def test_jq_at_record_index_uses_insertion_order():
    assert await run("[ [ 'z' 1 ] [ 'a' 2 ] ] REC '[0]' JQ@") == 1


@pytest.mark.asyncio
async def test_jq_path_strict_integer_parse():
    # ts parseInt('1x') == 1 silently; the contract errors (fixed by design)
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="invalid index"):
        await interp.run("[ 1 2 ] '[1x]' JQ@")


# ===== JQ! =====


@pytest.mark.asyncio
async def test_jq_set_deep_with_autocreate():
    # Missing intermediates auto-create by NEXT segment kind
    result = await run("NULL 42 'a.b[0]' JQ!")
    assert await run_code_on(result, "'a.b' JQ@") == [42]
    # Existing values untouched elsewhere
    result = await run("[ [ 'keep' 1 ] ] REC 2 'new' JQ!")
    assert list(result.keys()) == ["keep", "new"]


@pytest.mark.asyncio
async def test_jq_set_pads_arrays_with_null():
    # No JS holes: out-of-range set indexes pad explicitly
    assert await run("[ 1 ] 9 '[3]' JQ!") == [1, None, None, 9]


@pytest.mark.asyncio
async def test_jq_set_rejects_iterate_and_bad_shapes():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match=r"\[\] iteration not supported"):
        await interp.run("[ [ 'a' 1 ] ] REC 5 'a[]' JQ!")
    interp.reset()
    with pytest.raises(Exception, match="cannot set field"):
        await interp.run("[ 1 2 ] 5 'field' JQ!")
    interp.reset()
    with pytest.raises(Exception, match="negative set index"):
        await interp.run("[ 1 2 ] 5 '[-1]' JQ!")


@pytest.mark.asyncio
async def test_jq_set_empty_path_replaces_container():
    assert await run("[ 1 2 ] 42 '' JQ!") == 42


# ===== JQ-DEL =====


@pytest.mark.asyncio
async def test_jq_del():
    result = await run("[ [ 'a' 1 ] [ 'b' 2 ] ] REC 'a' JQ-DEL")
    assert list(result.keys()) == ["b"]
    # Array delete shifts left
    assert await run("[ 1 2 3 ] '[1]' JQ-DEL") == [1, 3]
    # Missing paths: silent no-op
    result = await run("[ [ 'a' 1 ] ] REC 'x.y.z' JQ-DEL")
    assert list(result.keys()) == ["a"]
    # Iterate rejected
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="not supported in delete"):
        await interp.run("[ [ 'a' 1 ] ] REC '[]' JQ-DEL")


# ===== MERGE / PICK / OMIT =====


@pytest.mark.asyncio
async def test_merge_shallow_rec2_wins():
    result = await run("[ [ 'a' 1 ] [ 'b' 2 ] ] REC [ [ 'b' 20 ] [ 'c' 3 ] ] REC MERGE")
    assert list(result.keys()) == ["a", "b", "c"], "shared keys keep rec1's position"
    assert result["b"] == 20
    # Non-records coerce to empty
    result = await run("NULL [ [ 'x' 1 ] ] REC MERGE")
    assert list(result.keys()) == ["x"]


@pytest.mark.asyncio
async def test_classic_rec_defaults_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="REC-DEFAULTS"):
        await interp.run("[ ] REC [ ] REC REC-DEFAULTS")


@pytest.mark.asyncio
async def test_pick_and_omit():
    rec = "[ [ 'a' 1 ] [ 'b' 2 ] [ 'c' 3 ] ] REC"
    picked = await run(f"{rec} [ 'c' 'a' 'zzz' ] PICK")
    assert list(picked.keys()) == ["c", "a"], "keys-list order; missing skipped"
    omitted = await run(f"{rec} [ 'b' ] OMIT")
    assert list(omitted.keys()) == ["a", "c"]
    # OMIT stringifies drop keys ([ 1 ] matches key "1")
    omitted = await run("[ [ '1' 'x' ] [ 'b' 2 ] ] REC [ 1 ] OMIT")
    assert list(omitted.keys()) == ["b"]


# ===== HAS-KEY? / DELETE =====


@pytest.mark.asyncio
async def test_has_key_is_presence_not_nonnull():
    assert await run("[ [ 'a' NULL ] ] REC 'a' HAS-KEY?") is True
    assert await run("[ [ 'a' 1 ] ] REC 'z' HAS-KEY?") is False
    assert await run("NULL 'a' HAS-KEY?") is False


@pytest.mark.asyncio
async def test_delete_is_copy_on_write_flavor():
    result = await run("[ [ 'z' 1 ] [ 'a' 2 ] [ 'm' 3 ] ] REC 'z' DELETE")
    assert list(result.keys()) == ["a", "m"], "order preserved"
    # Arrays: negative wraps once; out-of-range is a no-op
    assert await run("[ 1 2 3 ] -1 DELETE") == [1, 2]
    assert await run("[ 1 2 ] 9 DELETE") == [1, 2]
    # Non-integer array key errors (no ts NaN->0 splice surprise)
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="integer index"):
        await interp.run("[ 1 2 ] 'x' DELETE")


@pytest.mark.asyncio
async def test_delete_does_not_mutate_input():
    interp = StandardInterpreter()
    original = {"a": 1, "b": 2}
    interp.stack_push(original)
    await interp.run("'a' DELETE")
    assert interp.stack_pop() == {"b": 2}
    assert original == {"a": 1, "b": 2}, "classic <DEL mutated; DELETE must not"


@pytest.mark.asyncio
async def test_classic_l_del_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="DEL"):
        await interp.run("[ [ 'a' 1 ] ] REC 'a' <DEL")


# ===== REC>ENTRIES / ENTRIES>REC =====


@pytest.mark.asyncio
async def test_entries_round_trip_in_insertion_order():
    entries = await run("[ [ 'z' 1 ] [ 'a' 2 ] ] REC REC>ENTRIES")
    assert entries == [["z", 1], ["a", 2]]
    back = await run("[ [ 'z' 1 ] [ 'a' 2 ] ] REC REC>ENTRIES ENTRIES>REC")
    assert list(back.keys()) == ["z", "a"]


@pytest.mark.asyncio
async def test_entries_to_rec_validates_pairs():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="exactly 2"):
        await interp.run("[ [ 'a' 1 2 ] ] ENTRIES>REC")
    interp.reset()
    with pytest.raises(Exception, match=r"\[key, value\] array"):
        await interp.run("[ 5 ] ENTRIES>REC")
    # Duplicate keys: later wins, first position kept
    rec = await run("[ [ 'a' 1 ] [ 'b' 2 ] [ 'a' 9 ] ] ENTRIES>REC")
    assert list(rec.keys()) == ["a", "b"]
    assert rec["a"] == 9
