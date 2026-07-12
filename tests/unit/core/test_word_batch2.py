"""Batch 2 words: higher-order, sorting, grouping.

Port of forthic-rs tests/word_batch2_test.rs. Contracts per the ts
implementation spec; sanctioned deviations noted inline (structural
equality for KEY-OF/UNIQUE-BY, insertion order everywhere, group keys
coerce like JS object keys — strings in every runtime).
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


# ===== FILTER / FOREACH / REDUCE / FIND / COUNT =====


@pytest.mark.asyncio
async def test_filter_arrays_and_records():
    assert await run("[ 1 2 3 4 ] '2 >' FILTER") == [3, 4]
    # Record in -> record out, insertion order kept
    result = await run("[ [ 'z' 1 ] [ 'a' 5 ] [ 'm' 2 ] ] REC '2 >' FILTER")
    assert list(result.keys()) == ["a"]


@pytest.mark.asyncio
async def test_filter_with_key():
    # Keep elements whose INDEX is > 0 (key pushed beneath value; drop value)
    assert await run("[ 10 20 30 ] 'DROP 0 >' [ .with_key TRUE ] ~> FILTER") == [20, 30]


@pytest.mark.asyncio
async def test_classic_select_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="SELECT"):
        await interp.run("[ 1 ] '1' SELECT")


@pytest.mark.asyncio
async def test_foreach_leaves_results_on_stack():
    assert await run_all("[ 1 2 3 ] '2 *' FOREACH") == [2, 4, 6]


@pytest.mark.asyncio
async def test_reduce():
    assert await run("[ 1 2 3 4 ] 0 '+' REDUCE") == 10
    # Record reduces over values
    assert await run("[ [ 'a' 2 ] [ 'b' 3 ] ] REC 1 '*' REDUCE") == 6
    # Null container -> initial
    assert await run("NULL 42 '+' REDUCE") == 42


@pytest.mark.asyncio
async def test_find_short_circuits():
    assert await run("[ 1 5 2 ] '3 >' FIND") == 5
    assert await run("[ 1 2 ] '10 >' FIND") is None
    # Short-circuit proof: the poison element after the match never runs
    assert await run("[ 1 'NO-SUCH-WORD' ] 'STRING? NOT' FIND") == 1


@pytest.mark.asyncio
async def test_count():
    assert await run("[ 1 5 2 6 ] '3 >' COUNT") == 2
    assert await run("NULL '3 >' COUNT") == 0


# ===== SORT family =====


@pytest.mark.asyncio
async def test_sort_natural():
    assert await run("[ 3 1 2 ] SORT") == [1, 2, 3]
    # NULL sorts last
    assert await run("[ 3 NULL 1 ] SORT") == [1, 3, None]
    # Strings lexicographic
    assert await run("[ 'b' 'a' ] SORT") == ["a", "b"]
    # Int and Float share the number line
    assert await run("[ 2.5 1 3 ] SORT") == [1, 2.5, 3]


@pytest.mark.asyncio
async def test_sort_comparator_is_a_key_function():
    # The comparator option is a KEY function: '-1 *' sorts descending
    assert await run("[ 1 3 2 ] [ .comparator '-1 *' ] ~> SORT") == [3, 2, 1]


@pytest.mark.asyncio
async def test_sort_non_array_passes_through():
    result = await run("[ [ 'z' 1 ] ] REC SORT")
    assert list(result.keys()) == ["z"]
    assert await run("NULL SORT") is None


@pytest.mark.asyncio
async def test_sort_by_stable_ties():
    # Equal keys keep input order (decorate-stable-sort-undecorate)
    assert await run("[ 21 11 22 12 ] '10 MOD' SORT-BY") == [21, 11, 22, 12]
    assert await run("[ 3 1 2 ] 'DUP *' SORT-BY") == [1, 2, 3]


@pytest.mark.asyncio
async def test_min_by_max_by():
    assert await run("[ 3 1 2 ] 'DUP *' MIN-BY") == 1
    assert await run("[ 3 1 2 ] 'DUP *' MAX-BY") == 3
    # Empty and non-array -> NULL
    assert await run("[ ] 'DUP' MIN-BY") is None
    assert await run("NULL 'DUP' MAX-BY") is None
    # Ties keep the EARLIEST element: both have key 1
    assert await run("[ -1 1 ] 'DUP *' MIN-BY") == -1


@pytest.mark.asyncio
async def test_unique_by_keeps_first():
    assert await run("[ 21 11 31 12 ] '10 MOD' UNIQUE-BY") == [21, 12]


@pytest.mark.asyncio
async def test_sort_u():
    assert await run("[ 3 1 3 2 1 ] SORT-U") == [1, 2, 3]
    assert await run("[ 'b' 'a' 'b' ] SORT-U") == ["a", "b"]


# ===== Grouping =====


@pytest.mark.asyncio
async def test_group_by():
    result = await run("[ 1 2 3 4 5 ] '2 MOD' GROUP-BY")
    assert list(result.keys()) == ["1", "0"], "first-encounter order"
    assert result["1"] == [1, 3, 5]
    assert result["0"] == [2, 4]


@pytest.mark.asyncio
async def test_group_by_field_with_multi_membership():
    code = (
        "[ [ [ 'name' 'a' ] [ 'tags' [ 'x' 'y' ] ] ] REC "
        "[ [ 'name' 'b' ] [ 'tags' [ 'x' ] ] ] REC ] 'tags' GROUP-BY-FIELD"
    )
    result = await run(code)
    assert list(result.keys()) == ["x", "y"]
    assert len(result["x"]) == 2, "a and b both tagged x"


@pytest.mark.asyncio
async def test_group_by_field_null_record_errors():
    interp = StandardInterpreter()
    interp.stack_push([None])
    with pytest.raises(Exception, match="of NULL"):
        await interp.run("'id' GROUP-BY-FIELD")


@pytest.mark.asyncio
async def test_by_field_last_wins_and_skips_falsy():
    code = "[ [ [ 'id' 'k' ] [ 'v' 1 ] ] REC NULL [ [ 'id' 'k' ] [ 'v' 2 ] ] REC ] 'id' BY-FIELD"
    result = await run(code)
    assert list(result.keys()) == ["k"]
    assert result["k"]["v"] == 2


@pytest.mark.asyncio
async def test_groups_of():
    assert await run("[ 1 2 3 4 5 ] 2 GROUPS-OF") == [[1, 2], [3, 4], [5]]
    # Records chunk into sub-records
    result = await run("[ [ 'a' 1 ] [ 'b' 2 ] [ 'c' 3 ] ] REC 2 GROUPS-OF")
    assert list(result[0].keys()) == ["a", "b"]
    assert list(result[1].keys()) == ["c"]


@pytest.mark.asyncio
async def test_groups_of_rejects_nonpositive():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="group size"):
        await interp.run("[ 1 ] 0 GROUPS-OF")


@pytest.mark.asyncio
async def test_index_lowercases_and_multi_buckets():
    result = await run("[ 'Apple' 'Avocado' ] \"DROP [ 'A' 'FRUIT' ]\" INDEX")
    assert list(result.keys()) == ["a", "fruit"]
    assert len(result["fruit"]) == 2


@pytest.mark.asyncio
async def test_key_of_structural():
    assert await run("[ 'a' 'b' ] 'b' KEY-OF") == 1
    assert await run("[ [ 'k' 'b' ] ] REC 'b' KEY-OF") == "k"
    assert await run("[ 'a' ] 'z' KEY-OF") is None
    # Structural equality: a distinct-but-equal record matches
    assert await run("[ [ [ 'a' 1 ] ] REC ] [ [ 'a' 1 ] ] REC KEY-OF") == 0


@pytest.mark.asyncio
async def test_numbered():
    assert await run("[ 'a' 'b' ] NUMBERED") == [[0, "a"], [1, "b"]]
    # Non-arrays (including records) yield an EMPTY array
    assert await run("NULL NUMBERED") == []


# ===== ZIP-WITH / TIMES-RUN / MAP-AT =====


@pytest.mark.asyncio
async def test_zip_with_arrays_pads_null():
    assert await run("[ 1 2 ] [ 10 20 ] '+' ZIP-WITH") == [11, 22]
    # c1 longer: missing c2 entries are NULL; use DEFAULT to absorb
    assert await run("[ 1 2 3 ] [ 10 ] '0 DEFAULT +' ZIP-WITH") == [11, 2, 3]


@pytest.mark.asyncio
async def test_zip_with_records():
    result = await run("[ [ 'a' 1 ] ] REC [ [ 'a' 10 ] ] REC '+' ZIP-WITH")
    assert result["a"] == 11


@pytest.mark.asyncio
async def test_times_run():
    assert await run("1 3 '2 *' TIMES-RUN") == 8
    # Zero/negative and empty code are no-ops
    assert await run("7 0 '2 *' TIMES-RUN") == 7
    assert await run("7 3 '' TIMES-RUN") == 7


@pytest.mark.asyncio
async def test_classic_repeat_is_gone():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="REPEAT"):
        await interp.run("0 '1 +' 3 <REPEAT")


@pytest.mark.asyncio
async def test_map_at_single_key_and_path():
    result = await run("[ [ 'a' 1 ] [ 'b' 2 ] ] REC 'a' '10 *' MAP-AT")
    assert result["a"] == 10
    assert result["b"] == 2, "sibling untouched"

    # Deep path through record + array
    result = await run("[ [ 'xs' [ 1 2 3 ] ] ] REC [ 'xs' 1 ] '10 *' MAP-AT")
    assert result["xs"] == [1, 20, 3]


@pytest.mark.asyncio
async def test_map_at_copies_instead_of_mutating():
    interp = StandardInterpreter()
    original = {"a": 1}
    interp.stack_push(original)
    await interp.run("'a' '10 *' MAP-AT")
    assert interp.stack_pop() == {"a": 10}
    assert original == {"a": 1}, "input must not be mutated"


@pytest.mark.asyncio
async def test_map_at_misses_are_silent():
    # Missing key, out-of-range index, scalar mid-path: unchanged, no error
    result = await run("[ [ 'a' 1 ] ] REC 'zzz' '10 *' MAP-AT")
    assert result["a"] == 1
    assert await run("[ 1 2 ] 9 '10 *' MAP-AT") == [1, 2]
    assert await run("NULL 'a' '10 *' MAP-AT") is None


@pytest.mark.asyncio
async def test_map_at_empty_path_transforms_whole_container():
    assert await run("[ 1 2 ] [ ] 'LENGTH' MAP-AT") == 2


@pytest.mark.asyncio
async def test_map_at_numeric_string_index():
    # ts Number(head) coercion: '1' works as an array index
    assert await run("[ 1 2 3 ] '1' '10 *' MAP-AT") == [1, 20, 3]
