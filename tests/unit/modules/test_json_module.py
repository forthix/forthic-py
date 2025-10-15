"""Tests for JSON Module - ported from TypeScript."""

import json

import pytest

from forthic import StandardInterpreter


@pytest.fixture
def interp():
    """Create a fresh StandardInterpreter for each test."""
    return StandardInterpreter()


# ========================================
# >JSON - Object to JSON string
# ========================================


class TestToJSON:
    """Test >JSON serialization."""

    @pytest.mark.asyncio
    async def test_with_simple_object(self, interp):
        """Test >JSON with simple object."""
        await interp.run("[['a' 1] ['b' 2]] REC >JSON")
        result = interp.stack_pop()
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_with_nested_object(self, interp):
        """Test >JSON with nested object."""
        await interp.run("""
            [['name' 'Alice'] ['data' [['age' 30] ['city' 'NYC']] REC]] REC >JSON
        """)
        result = interp.stack_pop()
        parsed = json.loads(result)
        assert parsed["name"] == "Alice"
        assert parsed["data"]["age"] == 30
        assert parsed["data"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_with_array(self, interp):
        """Test >JSON with array."""
        await interp.run("[1 2 3 4 5] >JSON")
        assert interp.stack_pop() == "[1, 2, 3, 4, 5]"

    @pytest.mark.asyncio
    async def test_with_string(self, interp):
        """Test >JSON with string."""
        await interp.run("'hello world' >JSON")
        assert interp.stack_pop() == '"hello world"'

    @pytest.mark.asyncio
    async def test_with_number(self, interp):
        """Test >JSON with number."""
        await interp.run("42 >JSON")
        assert interp.stack_pop() == "42"

    @pytest.mark.asyncio
    async def test_with_boolean(self, interp):
        """Test >JSON with boolean."""
        await interp.run("TRUE >JSON")
        assert interp.stack_pop() == "true"

    @pytest.mark.asyncio
    async def test_with_null(self, interp):
        """Test >JSON with null."""
        await interp.run("NULL >JSON")
        assert interp.stack_pop() == "null"

    @pytest.mark.asyncio
    async def test_with_array_of_objects(self, interp):
        """Test >JSON with array of objects."""
        await interp.run("""
            [
                [['name' 'Alice'] ['age' 30]] REC
                [['name' 'Bob'] ['age' 25]] REC
            ] >JSON
        """)
        result = interp.stack_pop()
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "Alice"
        assert parsed[1]["name"] == "Bob"


# ========================================
# JSON> - JSON string to Object
# ========================================


class TestFromJSON:
    """Test JSON> deserialization."""

    @pytest.mark.asyncio
    async def test_with_simple_object(self, interp):
        """Test JSON> with simple object."""
        await interp.run('\'{"a": 1, "b": 2}\' JSON>')
        result = interp.stack_pop()
        assert sorted(result.keys()) == ["a", "b"]
        assert result["a"] == 1
        assert result["b"] == 2

    @pytest.mark.asyncio
    async def test_with_nested_object(self, interp):
        """Test JSON> with nested object."""
        await interp.run('\'{"name":"Alice","data":{"age":30,"city":"NYC"}}\' JSON>')
        result = interp.stack_pop()
        assert result["name"] == "Alice"
        assert result["data"]["age"] == 30
        assert result["data"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_with_array(self, interp):
        """Test JSON> with array."""
        await interp.run("'[1,2,3,4,5]' JSON>")
        result = interp.stack_pop()
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_with_string(self, interp):
        """Test JSON> with string."""
        await interp.run('\'"hello world"\' JSON>')
        assert interp.stack_pop() == "hello world"

    @pytest.mark.asyncio
    async def test_with_number(self, interp):
        """Test JSON> with number."""
        await interp.run("'42' JSON>")
        assert interp.stack_pop() == 42

    @pytest.mark.asyncio
    async def test_with_boolean(self, interp):
        """Test JSON> with boolean."""
        await interp.run("'true' JSON>")
        assert interp.stack_pop() is True

    @pytest.mark.asyncio
    async def test_with_null(self, interp):
        """Test JSON> with null."""
        await interp.run("'null' JSON>")
        assert interp.stack_pop() is None

    @pytest.mark.asyncio
    async def test_with_array_of_objects(self, interp):
        """Test JSON> with array of objects."""
        await interp.run('\'[{"name":"Alice","age":30},{"name":"Bob","age":25}]\' JSON>')
        result = interp.stack_pop()
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_with_empty_string_returns_null(self, interp):
        """Test JSON> with empty string returns null."""
        await interp.run("'' JSON>")
        assert interp.stack_pop() is None


# ========================================
# JSON-PRETTIFY - Format JSON
# ========================================


class TestJSONPrettify:
    """Test JSON-PRETTIFY formatting."""

    @pytest.mark.asyncio
    async def test_formats_compact_json(self, interp):
        """Test JSON-PRETTIFY formats compact JSON."""
        await interp.run('\'{"a":1,"b":2,"c":3}\' JSON-PRETTIFY')
        result = interp.stack_pop()
        assert result == '{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}'

    @pytest.mark.asyncio
    async def test_with_nested_object(self, interp):
        """Test JSON-PRETTIFY with nested object."""
        await interp.run('\'{"name":"Alice","data":{"age":30,"city":"NYC"}}\' JSON-PRETTIFY')
        result = interp.stack_pop()
        lines = result.split("\n")
        assert len(lines) > 3  # Should be multi-line
        assert "  " in result  # Should have indentation

    @pytest.mark.asyncio
    async def test_with_array(self, interp):
        """Test JSON-PRETTIFY with array."""
        await interp.run("'[1,2,3,4,5]' JSON-PRETTIFY")
        result = interp.stack_pop()
        assert "\n" in result  # Should be multi-line

    @pytest.mark.asyncio
    async def test_with_empty_string(self, interp):
        """Test JSON-PRETTIFY with empty string."""
        await interp.run("'' JSON-PRETTIFY")
        assert interp.stack_pop() == ""


# ========================================
# Round-trip tests
# ========================================


class TestRoundTrip:
    """Test round-trip conversions."""

    @pytest.mark.asyncio
    async def test_object_to_json_to_object(self, interp):
        """Test round-trip: object -> JSON -> object."""
        await interp.run("""
            [['x' 10] ['y' 20] ['z' 30]] REC
            >JSON
            JSON>
        """)
        result = interp.stack_pop()
        assert result["x"] == 10
        assert result["y"] == 20
        assert result["z"] == 30

    @pytest.mark.asyncio
    async def test_array_to_json_to_array(self, interp):
        """Test round-trip: array -> JSON -> array."""
        await interp.run("""
            [1 2 3 4 5]
            >JSON
            JSON>
        """)
        result = interp.stack_pop()
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_with_prettify(self, interp):
        """Test round-trip with PRETTIFY."""
        await interp.run("""
            [['a' 1] ['b' 2]] REC
            >JSON
            JSON-PRETTIFY
            JSON>
        """)
        result = interp.stack_pop()
        assert result["a"] == 1
        assert result["b"] == 2
