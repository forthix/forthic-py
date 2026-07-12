"""Tests for String Module - ported from TypeScript."""

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


class TestStringModule:
    """Test string module operations."""

    @pytest.mark.asyncio
    async def test_to_str(self, interp):
        """Test >STR conversion."""
        await interp.run("42 >STR")
        assert interp.stack_pop() == "42"

    @pytest.mark.asyncio
    async def test_concat_two_strings(self, interp):
        """Test CONCAT rejects two loose strings (array-only now)."""
        with pytest.raises(Exception, match=r"\[s1 s2\] CONCAT"):
            await interp.run("'Hello' ' World' CONCAT")

    @pytest.mark.asyncio
    async def test_concat_null_elements(self, interp):
        """Test CONCAT renders null elements as empty strings."""
        await interp.run("['Hello' NULL ' World'] CONCAT")
        assert interp.stack_pop() == "Hello World"

    @pytest.mark.asyncio
    async def test_concat_array_of_strings(self, interp):
        """Test CONCAT with array of strings."""
        await interp.run("['Hello' ' ' 'World'] CONCAT")
        assert interp.stack_pop() == "Hello World"

    @pytest.mark.asyncio
    async def test_split(self, interp):
        """Test SPLIT."""
        await interp.run("'a,b,c' ',' SPLIT")
        assert interp.stack_pop() == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_join(self, interp):
        """Test JOIN."""
        await interp.run("['a' 'b' 'c'] ',' JOIN")
        assert interp.stack_pop() == "a,b,c"

    @pytest.mark.asyncio
    async def test_newline(self, interp):
        """Test /N (newline)."""
        await interp.run("/N")
        assert interp.stack_pop() == "\n"

    @pytest.mark.asyncio
    async def test_carriage_return(self, interp):
        """Test /R (carriage return)."""
        await interp.run("/R")
        assert interp.stack_pop() == "\r"

    @pytest.mark.asyncio
    async def test_tab(self, interp):
        """Test /T (tab)."""
        await interp.run("/T")
        assert interp.stack_pop() == "\t"

    @pytest.mark.asyncio
    async def test_lowercase(self, interp):
        """Test LOWERCASE."""
        await interp.run("'HELLO' LOWERCASE")
        assert interp.stack_pop() == "hello"

    @pytest.mark.asyncio
    async def test_uppercase(self, interp):
        """Test UPPERCASE."""
        await interp.run("'hello' UPPERCASE")
        assert interp.stack_pop() == "HELLO"

    @pytest.mark.asyncio
    async def test_ascii(self, interp):
        """Test ASCII removes non-ASCII characters."""
        await interp.run("'Hello\u0100World' ASCII")
        assert interp.stack_pop() == "HelloWorld"

    @pytest.mark.asyncio
    async def test_strip(self, interp):
        """Test STRIP removes whitespace."""
        await interp.run("'  hello  ' STRIP")
        assert interp.stack_pop() == "hello"

    @pytest.mark.asyncio
    async def test_replace(self, interp):
        """Test REPLACE."""
        await interp.run("'hello world' 'world' 'there' REPLACE")
        assert interp.stack_pop() == "hello there"

    @pytest.mark.asyncio
    async def test_re_match_success(self, interp):
        """Test RE-MATCH with successful match."""
        await interp.run("'test123' 'test[0-9]+' RE-MATCH")
        result = interp.stack_pop()
        assert result is not None
        assert result[0] == "test123"

    @pytest.mark.asyncio
    async def test_re_match_failure(self, interp):
        """Test RE-MATCH with no match."""
        await interp.run("'test' '[0-9]+' RE-MATCH")
        assert interp.stack_pop() is False

    @pytest.mark.asyncio
    async def test_re_match_all(self, interp):
        """Test RE-MATCH-ALL."""
        await interp.run("'test1 test2 test3' 'test([0-9])' RE-MATCH-ALL")
        assert interp.stack_pop() == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_re_match_group_is_gone(self, interp):
        """Tombstone: RE-MATCH-GROUP dropped — RE-MATCH returns [full, g1, ...] directly."""
        with pytest.raises(Exception, match="RE-MATCH-GROUP"):
            await interp.run("'ab' '(a)' RE-MATCH 1 RE-MATCH-GROUP")

    @pytest.mark.asyncio
    async def test_url_encode(self, interp):
        """Test URL-ENCODE."""
        await interp.run("'hello world' URL-ENCODE")
        assert interp.stack_pop() == "hello%20world"

    @pytest.mark.asyncio
    async def test_url_decode(self, interp):
        """Test URL-DECODE."""
        await interp.run("'hello%20world' URL-DECODE")
        assert interp.stack_pop() == "hello world"
