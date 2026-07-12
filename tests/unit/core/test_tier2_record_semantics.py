"""Tier 2 regression tests: insertion-ordered records and the record
contracts for container words.

Port of forthic-rs tests/tier2_record_semantics_test.rs (the post-scrub ts
#31/#33 behavior). Records iterate, index, slice, and serialize in
INSERTION order — every sorted() on record keys was a bug.

Deferred to its word batch: DELETE (Batch 3).
The DROP -> SKIP rename (Batch 0) has landed — the SKIP tests here use SKIP.
"""

import pytest

from forthic.interpreter import StandardInterpreter

# A record with deliberately non-alphabetical insertion order: z, a, m
ZAM = "[ [ 'z' 1 ] [ 'a' 2 ] [ 'm' 3 ] ] REC"


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


async def run_all(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.get_stack().get_items()


# ===== Insertion order =====


@pytest.mark.asyncio
async def test_record_preserves_insertion_order():
    assert list((await run(ZAM)).keys()) == ["z", "a", "m"]


@pytest.mark.asyncio
async def test_keys_and_values_follow_insertion_order():
    assert await run(f"{ZAM} KEYS") == ["z", "a", "m"]
    assert await run(f"{ZAM} VALUES") == [1, 2, 3]


@pytest.mark.asyncio
async def test_nth_first_last_use_insertion_order():
    # Sorted-key order would give a=2 first and z=1 last; insertion order
    # gives z=1 first and m=3 last
    assert await run(f"{ZAM} 0 NTH") == 1
    assert await run(f"{ZAM} FIRST") == 1
    assert await run(f"{ZAM} LAST") == 3
    assert await run(f"{ZAM} 1 NTH") == 2


@pytest.mark.asyncio
async def test_to_json_is_insertion_ordered():
    # Compact like JSON.stringify, keys in insertion order
    assert await run(f"{ZAM} >JSON") == '{"z":1,"a":2,"m":3}'


@pytest.mark.asyncio
async def test_json_round_trip_preserves_order():
    result = await run("""'{"z":1,"a":2,"m":3}' JSON> >JSON""")
    assert result == '{"z":1,"a":2,"m":3}'


# ===== TAKE / SKIP on records =====


@pytest.mark.asyncio
async def test_take_on_record_preserves_shape_and_order():
    taken = await run(f"{ZAM} 2 TAKE")
    assert isinstance(taken, dict)
    assert list(taken.keys()) == ["z", "a"]


@pytest.mark.asyncio
async def test_take_push_rest_option():
    stack = await run_all(f"{ZAM} 2 [ .push_rest TRUE ] ~> TAKE")
    assert len(stack) == 2
    assert list(stack[0].keys()) == ["z", "a"]
    assert list(stack[1].keys()) == ["m"]


@pytest.mark.asyncio
async def test_take_push_rest_on_arrays():
    stack = await run_all("[ 1 2 3 ] 2 [ .push_rest TRUE ] ~> TAKE")
    assert stack[0] == [1, 2]
    assert stack[1] == [3]


@pytest.mark.asyncio
async def test_skip_on_record():
    rest = await run(f"{ZAM} 1 SKIP")
    assert isinstance(rest, dict)
    assert list(rest.keys()) == ["a", "m"]
    # n <= 0 skips nothing
    unchanged = await run(f"{ZAM} 0 SKIP")
    assert list(unchanged.keys()) == ["z", "a", "m"]


@pytest.mark.asyncio
async def test_take_last():
    assert await run("[ 1 2 3 4 ] 2 TAKE-LAST") == [3, 4]
    tail = await run(f"{ZAM} 2 TAKE-LAST")
    assert list(tail.keys()) == ["a", "m"]
    assert await run("[ 1 2 ] 0 TAKE-LAST") == []


# ===== SLICE on records + span guard =====


@pytest.mark.asyncio
async def test_slice_on_record():
    sliced = await run(f"{ZAM} 0 1 SLICE")
    assert list(sliced.keys()) == ["z", "a"]
    # Negative indexes count from the end
    tail = await run(f"{ZAM} -2 -1 SLICE")
    assert list(tail.keys()) == ["a", "m"]


@pytest.mark.asyncio
async def test_slice_record_skips_out_of_range():
    # Arrays null-pad out-of-range; records skip (ts #33)
    sliced = await run(f"{ZAM} 1 5 SLICE")
    assert list(sliced.keys()) == ["a", "m"]
    padded = await run("[ 1 2 3 ] 1 4 SLICE")
    assert padded == [2, 3, None, None]


@pytest.mark.asyncio
async def test_slice_span_guard():
    # Materializing a ~billion-element span must error, not OOM
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="too large"):
        await interp.run("[ 1 ] 0 999999999 SLICE")


# ===== UNPACK on records =====


@pytest.mark.asyncio
async def test_unpack_record_pushes_values_in_insertion_order():
    assert await run_all(f"{ZAM} UNPACK") == [1, 2, 3]


# ===== DIFFERENCE / INTERSECTION =====


@pytest.mark.asyncio
async def test_set_ops_on_arrays():
    assert await run("[ 1 2 3 ] [ 2 ] DIFFERENCE") == [1, 3]
    assert await run("[ 1 2 3 ] [ 2 4 ] INTERSECTION") == [2]


@pytest.mark.asyncio
async def test_record_left_set_ops_behave_like_pick_and_omit():
    # INTERSECTION with an array of keys = PICK
    picked = await run(f"{ZAM} [ 'z' 'm' ] INTERSECTION")
    assert list(picked.keys()) == ["z", "m"]
    # DIFFERENCE with an array of keys = OMIT
    omitted = await run(f"{ZAM} [ 'z' ] DIFFERENCE")
    assert list(omitted.keys()) == ["a", "m"]
    # Record right operand: membership by its keys
    picked2 = await run(f"{ZAM} [ [ 'a' 99 ] ] REC INTERSECTION")
    assert list(picked2.keys()) == ["a"]


@pytest.mark.asyncio
async def test_array_left_record_right_uses_values():
    # ts: array-left membership tests against Object.values(right)
    assert await run("[ 1 2 3 ] [ [ 'x' 2 ] ] REC INTERSECTION") == [2]


@pytest.mark.asyncio
async def test_set_ops_unify_int_and_float():
    # JS has one number type: 1 and 1.0 are the same set element
    assert await run("[ 1 2 ] [ 1.0 ] INTERSECTION") == [1]


@pytest.mark.asyncio
async def test_set_ops_distinguish_bools_from_numbers():
    # JS ===: true is not 1 (Python's True == 1 must not leak through)
    assert await run("[ TRUE ] [ 1 ] INTERSECTION") == []


# ===== >STR (coordinated ts/rs contract) =====


@pytest.mark.asyncio
async def test_to_str_matches_js_semantics():
    assert await run("NULL >STR") == ""
    assert await run("TRUE >STR") == "true"
    assert await run("42 >STR") == "42"
    assert await run("3.25 >STR") == "3.25"
    # JS (3.0).toString() === "3"
    assert await run("3.0 >STR") == "3"
    # JS Array.toString: comma-join, null elements empty, nested flattened
    assert await run("[ 1 NULL [ 2 3 ] ] >STR") == "1,,2,3"
    # Temporal-style ISO forms
    assert await run("2020-06-05 >STR") == "2020-06-05"
    assert await run("9:30 >STR") == "09:30:00"


@pytest.mark.asyncio
async def test_to_str_renders_records_as_json():
    # Coordinated contract change (all runtimes): insertion-ordered JSON
    # instead of str(dict) / "[object Object]"
    assert await run(f"{ZAM} >STR") == '{"z":1,"a":2,"m":3}'
    # Record elements inside arrays render as JSON within the comma-join
    assert await run("[ [ [ 'a' 1 ] ] REC [ [ 'b' 2 ] ] REC ] >STR") == '{"a":1},{"b":2}'
    # Temporal values inside records use their ISO forms
    assert await run("[ [ 'd' 2020-06-05 ] ] REC >STR") == '{"d":"2020-06-05"}'


# ===== Wire round-trip order (jsonrpc serializer) =====


@pytest.mark.asyncio
async def test_record_order_survives_the_wire():
    from forthic.jsonrpc.serializer import deserialize_value, serialize_value

    record = await run(ZAM)
    wire = serialize_value(record)
    back = deserialize_value(wire)
    assert list(back.keys()) == ["z", "a", "m"]
