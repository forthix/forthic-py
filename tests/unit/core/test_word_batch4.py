"""Batch 4 words: strings & interpolation.

Port of forthic-rs tests/word_batch4_test.rs. py notes: STR-LENGTH/
SUBSTR/SPLICE count code points (host-native units — same as rs; ts
counts UTF-16 units); RE-MATCH pushes False for no-match/null input (ts
parity — rs pushes NULL there, both falsy); regex compile failures are
clean errors (ts throws a raw SyntaxError).
"""

import pytest

from forthic.interpreter import StandardInterpreter


async def run(code: str):
    interp = StandardInterpreter()
    await interp.run(code)
    return interp.stack_pop()


# ===== STR-LENGTH =====


@pytest.mark.asyncio
async def test_str_length_counts_chars():
    assert await run("'hello' STR-LENGTH") == 5
    assert await run("'' STR-LENGTH") == 0
    assert await run("NULL STR-LENGTH") == 0
    # Host-native units: py counts code points (ts .length would say 2)
    assert await run("'🦀' STR-LENGTH") == 1


@pytest.mark.asyncio
async def test_str_length_rejects_containers():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="use LENGTH"):
        await interp.run("[ 1 2 ] STR-LENGTH")


# ===== SUBSTR / SPLICE =====


@pytest.mark.asyncio
async def test_substr_js_slice_semantics():
    assert await run("'hello' 1 3 SUBSTR") == "el"
    # Negative indices count from the end
    assert await run("'hello' -3 -1 SUBSTR") == "ll"
    # Out-of-range clamps; crossed range is empty
    assert await run("'hi' 0 99 SUBSTR") == "hi"
    assert await run("'hello' 3 1 SUBSTR") == ""
    assert await run("NULL 0 2 SUBSTR") == ""
    # Char indices — astral chars never split (ts can cut a surrogate)
    assert await run("'a🦀b' 1 2 SUBSTR") == "🦀"


@pytest.mark.asyncio
async def test_splice_replaces_a_char_range():
    assert await run("'hello' 1 3 'XY' SPLICE") == "hXYlo"
    # NULL insert deletes the range
    assert await run("'hello' 1 3 NULL SPLICE") == "hlo"
    # Insert-at-point via an empty range
    assert await run("'ab' 1 1 'X' SPLICE") == "aXb"
    # Non-string inserts stringify
    assert await run("'ab' 1 1 42 SPLICE") == "a42b"


# ===== STARTS-WITH? / ENDS-WITH? / TRIM-PREFIX / TRIM-SUFFIX =====


@pytest.mark.asyncio
async def test_starts_and_ends_with():
    assert await run("'hello' 'he' STARTS-WITH?") is True
    assert await run("'hello' 'lo' STARTS-WITH?") is False
    assert await run("'hello' 'lo' ENDS-WITH?") is True
    # Non-string operands are false, not an error
    assert await run("NULL 'x' STARTS-WITH?") is False
    assert await run("'x' NULL ENDS-WITH?") is False


@pytest.mark.asyncio
async def test_trim_prefix_and_suffix():
    assert await run("'foobar' 'foo' TRIM-PREFIX") == "bar"
    assert await run("'foobar' 'zzz' TRIM-PREFIX") == "foobar"
    assert await run("'foobar' 'bar' TRIM-SUFFIX") == "foo"
    # Trims at most ONE occurrence
    assert await run("'aaX' 'a' TRIM-PREFIX") == "aX"
    # Empty/non-string prefix: unchanged (including non-string values)
    assert await run("'foo' '' TRIM-PREFIX") == "foo"
    assert await run("42 'x' TRIM-PREFIX") == 42


# ===== Regex words =====


@pytest.mark.asyncio
async def test_re_match_q():
    assert await run(r"'abc123' '\d+' RE-MATCH?") is True
    assert await run(r"'abc' '\d' RE-MATCH?") is False
    assert await run(r"NULL '\d' RE-MATCH?") is False


@pytest.mark.asyncio
async def test_re_match_returns_groups_array():
    # [full, group1, group2, ...]
    assert await run(r"'2026-07-11' '(\d+)-(\d+)' RE-MATCH") == ["2026-07", "2026", "07"]
    # Non-participating groups are NULL
    assert await run(r"'ab' '(a)(z)?(b)' RE-MATCH") == ["ab", "a", None, "b"]
    # No match / NULL input: False (ts parity — rs pushes NULL; both falsy)
    assert await run(r"'abc' '\d' RE-MATCH") is False
    assert await run(r"NULL 'a' RE-MATCH") is False


@pytest.mark.asyncio
async def test_re_match_all_prefers_group_one():
    # With a capture group: collect group 1 per match
    assert await run(r"'a=1, b=2' '(\w)=\d' RE-MATCH-ALL") == ["a", "b"]
    # Without groups: full matches (the old code errored here)
    assert await run(r"'a1b22' '\d+' RE-MATCH-ALL") == ["1", "22"]
    assert await run(r"'abc' '\d' RE-MATCH-ALL") == []
    assert await run(r"NULL 'a' RE-MATCH-ALL") == []


@pytest.mark.asyncio
async def test_re_replace_normalizes_js_backrefs():
    assert await run(r"'hello world' 'o' '0' RE-REPLACE") == "hell0 w0rld", "replaces ALL matches"
    # JS $1 backrefs work even when followed by a word character
    assert await run(r"'ab' '(a)(b)' '$2$1x' RE-REPLACE") == "bax"
    # $& is the whole match; $$ is a literal dollar
    assert await run(r"'hi' 'hi' '<$&>' RE-REPLACE") == "<hi>"
    assert await run(r"'x' 'x' '$$5' RE-REPLACE") == "$5"
    # NULL contracts: null string stays NULL; null pattern is a no-op;
    # null replacement deletes matches
    assert await run(r"NULL 'a' 'b' RE-REPLACE") is None
    assert await run(r"'ab' NULL 'x' RE-REPLACE") == "ab"
    assert await run(r"'a1b' '\d' NULL RE-REPLACE") == "ab"


@pytest.mark.asyncio
async def test_replace_stays_literal():
    # No regex, no backref surprises — RE-REPLACE is the regex word
    assert await run(r"'a.c a.c' 'a.c' 'X' REPLACE") == "X X"
    assert await run(r"'abc' NULL 'X' REPLACE") == "abc"


@pytest.mark.asyncio
async def test_invalid_regex_is_a_clean_error():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="Invalid regex"):
        await interp.run(r"'x' '(' RE-MATCH?")


# ===== LINES / UNLINES =====


@pytest.mark.asyncio
async def test_lines_splits_on_newline_exactly():
    assert await run("'a\nb\nc' LINES") == ["a", "b", "c"]
    # "" is one empty line (JS ''.split('\\n') parity)
    assert await run("'' LINES") == [""]
    # \r\n is NOT normalized — the \r stays on the line
    assert await run("'a\r\nb' LINES") == ["a\r", "b"]
    assert await run("NULL LINES") == []


@pytest.mark.asyncio
async def test_unlines_joins_and_stringifies():
    assert await run("[ 'a' 'b' ] UNLINES") == "a\nb"
    # NULL elements render empty; non-strings stringify
    assert await run("[ 'a' NULL 42 ] UNLINES") == "a\n\n42"
    assert await run("NULL UNLINES") == ""


# ===== GREP / GREP-V / SED / CUT =====


@pytest.mark.asyncio
async def test_grep_keeps_matching_strings_only():
    assert await run(r"[ 'apple' 'banana' 'cherry' ] 'an' GREP") == ["banana"]
    # Non-string elements are dropped (they can't match)
    assert await run(r"[ 'a1' 42 'b2' ] '\d' GREP") == ["a1", "b2"]
    # Non-string pattern or non-array input: empty
    assert await run(r"[ 'a' ] NULL GREP") == []
    assert await run(r"NULL 'a' GREP") == []


@pytest.mark.asyncio
async def test_grep_v_keeps_non_matches_including_non_strings():
    assert await run(r"[ 'a1' 42 'bb' ] '\d' GREP-V") == [42, "bb"], (
        "deliberate asymmetry: -v keeps non-strings"
    )
    # Non-string pattern filters nothing
    assert await run(r"[ 'a' 42 ] NULL GREP-V") == ["a", 42]


@pytest.mark.asyncio
async def test_sed_replaces_per_element():
    assert await run(r"[ 'a1' 'b2' ] '\d' 'X' SED") == ["aX", "bX"]
    # Non-strings pass through untouched
    assert await run(r"[ 'a1' 42 ] '\d' 'X' SED") == ["aX", 42]
    # Backref normalization matches RE-REPLACE
    assert await run(r"[ 'ab' ] '(a)' '<$1>' SED") == ["<a>b"]


@pytest.mark.asyncio
async def test_cut_extracts_a_field_per_line():
    assert await run("[ 'a:b:c' 'x:y' ] ':' 1 CUT") == ["b", "y"]
    # Out-of-range field is NULL for that element
    assert await run("[ 'a:b' 'x' ] ':' 1 CUT") == ["b", None]
    # String field numbers coerce (ts Number('1'))
    assert await run("[ 'a:b' ] ':' '1' CUT") == ["b"]
    # Empty separator splits into chars
    assert await run("[ 'ab' ] '' 1 CUT") == ["b"]
    # Non-string elements yield NULL
    assert await run("[ 42 ] ':' 0 CUT") == [None]


# ===== INTERPOLATE =====


@pytest.mark.asyncio
async def test_interpolate_fills_holes_from_variables():
    assert await run("'World' .name ! 'Hello ${name}!' INTERPOLATE") == "Hello World!"
    # The dot-symbol spelling works too; body whitespace trims
    assert await run("'x' .v ! '${.v}' INTERPOLATE") == "x"
    assert await run("'x' .v ! '${ v }' INTERPOLATE") == "x"


@pytest.mark.asyncio
async def test_interpolate_lookup_is_read_only():
    # A miss renders as null_text (default "") and creates nothing
    assert await run("'a ${nope} b' INTERPOLATE") == "a  b"
    assert await run("NULL .v ! '<${v}>' INTERPOLATE") == "<>"
    # null_text opt-in makes misses/NULLs visible
    assert await run("'<${v}>' [ .null_text 'null' ] ~> INTERPOLATE") == "<null>"


@pytest.mark.asyncio
async def test_interpolate_miss_creates_nothing():
    # Typos can't mint variables: after a missed hole, @ still errors...
    # (@ read-only lands in Phase 5; until then prove non-creation via a
    # second interpolation with a distinct null_text)
    interp = StandardInterpreter()
    await interp.run("'x ${ghost} y' INTERPOLATE DROP")
    assert interp.find_variable("ghost") is None


@pytest.mark.asyncio
async def test_interpolate_needs_the_full_hole_shape():
    # Bare dots, braces, and dollars are literal text — only ${...} is a
    # hole (the old bare-dot grammar is gone)
    assert await run("7 .x ! 'file.x {x} $x .x' INTERPOLATE") == "file.x {x} $x .x"
    # \${ escapes a literal hole
    assert await run(r"7 .x ! '\${x} = ${x}' INTERPOLATE") == "${x} = 7"


@pytest.mark.asyncio
async def test_interpolate_holes_are_names_not_expressions():
    # The injection-safety rule: a non-name body is a hard error, so
    # templates can never execute Forthic
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="not expressions"):
        await interp.run("'${1 +}' INTERPOLATE")
    interp.reset()
    with pytest.raises(Exception, match="not expressions"):
        await interp.run("'${x:-default}' INTERPOLATE")
    interp.reset()
    # __ names are reserved (same contract as ! / @)
    with pytest.raises(Exception, match="__secret"):
        await interp.run("'${__secret}' INTERPOLATE")


@pytest.mark.asyncio
async def test_interpolate_containers_render_as_json():
    assert await run("[ [ 'a' 1 ] ] REC .rec ! '${rec}' INTERPOLATE") == '{"a":1}'
    # Arrays join with the separator option
    assert await run("[ 1 2 ] .items ! '${items}' INTERPOLATE") == "1, 2"
    assert (
        await run("[ 1 2 ] .items ! '${items}' [ .separator ' | ' ] ~> INTERPOLATE") == "1 | 2"
    )
    # json option renders any value as compact JSON
    assert await run("[ 1 2 ] .items ! '${items}' [ .json TRUE ] ~> INTERPOLATE") == "[1,2]"


@pytest.mark.asyncio
async def test_interpolate_null_template_stays_null():
    assert await run("NULL INTERPOLATE") is None


# ===== PRINT (shares INTERPOLATE's holes and rendering) =====


@pytest.mark.asyncio
async def test_print_pushes_nothing(capsys):
    interp = StandardInterpreter()
    await interp.run("1 'msg ${x}' PRINT")
    assert interp.get_stack().get_items() == [1]
    # Non-strings and options are accepted
    interp = StandardInterpreter()
    await interp.run("[ 1 2 3 ] [ .separator ' | ' ] ~> PRINT")
    assert len(interp.get_stack()) == 0
    assert "1 | 2 | 3" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_print_rejects_expression_holes_too():
    interp = StandardInterpreter()
    with pytest.raises(Exception, match="not expressions"):
        await interp.run("'value: ${6 * 7}' PRINT")
