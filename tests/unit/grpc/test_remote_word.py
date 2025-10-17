"""
Unit tests for RemoteWord
Tests proxy word that executes in remote runtime via gRPC
"""
import pytest
from unittest.mock import Mock, AsyncMock
from forthic.grpc.remote_word import RemoteWord
from forthic.interpreter import Interpreter
from forthic.grpc.errors import RemoteRuntimeError


class TestRemoteWord:
    """Test suite for RemoteWord"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock GrpcClient"""
        client = Mock()
        client.execute_word = AsyncMock()
        return client

    @pytest.fixture
    def interp(self):
        """Create an interpreter instance"""
        return Interpreter()

    @pytest.mark.asyncio
    async def test_remote_word_initialization(self, mock_client):
        """Test RemoteWord initialization with all parameters"""
        word = RemoteWord(
            name="REVERSE",
            client=mock_client,
            runtime_name="typescript",
            module_name="array",
            stack_effect="( array -- array )",
            description="Reverse an array",
        )

        assert word.name == "REVERSE"
        assert word.get_runtime_name() == "typescript"
        assert word.get_module_name() == "array"
        assert word.stack_effect == "( array -- array )"
        assert word.description == "Reverse an array"

    @pytest.mark.asyncio
    async def test_remote_word_default_parameters(self, mock_client):
        """Test RemoteWord with default stack_effect and description"""
        word = RemoteWord(
            name="SOME-WORD",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        assert word.stack_effect == "( -- )"
        assert word.description == ""

    @pytest.mark.asyncio
    async def test_execute_basic_word(self, mock_client, interp):
        """Test executing a basic remote word"""
        # Setup
        word = RemoteWord(
            name="DUP",
            client=mock_client,
            runtime_name="typescript",
            module_name="stdlib",
        )

        # Mock client returns duplicated value
        mock_client.execute_word.return_value = [42, 42]

        # Push value and execute
        interp.stack_push(42)
        await word.execute(interp)

        # Verify
        mock_client.execute_word.assert_called_once_with("DUP", [42])
        assert len(interp.get_stack()) == 2
        assert interp.stack_pop() == 42
        assert interp.stack_pop() == 42

    @pytest.mark.asyncio
    async def test_execute_with_array(self, mock_client, interp):
        """Test executing remote word with array input"""
        # Setup
        word = RemoteWord(
            name="REVERSE",
            client=mock_client,
            runtime_name="typescript",
            module_name="array",
        )

        # Mock client returns reversed array
        mock_client.execute_word.return_value = [[3, 2, 1]]

        # Push array and execute
        interp.stack_push([1, 2, 3])
        await word.execute(interp)

        # Verify
        mock_client.execute_word.assert_called_once_with("REVERSE", [[1, 2, 3]])
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_execute_clears_stack_correctly(self, mock_client, interp):
        """Test that execute properly clears and replaces stack"""
        # Setup
        word = RemoteWord(
            name="SWAP",
            client=mock_client,
            runtime_name="typescript",
            module_name="stdlib",
        )

        # Mock client returns swapped values
        # Stack is: [10, 20] (20 is on top)
        # After swap: [20, 10] (10 is on top)
        mock_client.execute_word.return_value = [20, 10]

        # Push two values
        interp.stack_push(10)
        interp.stack_push(20)
        await word.execute(interp)

        # Verify stack is replaced correctly
        # Pop from top to bottom: 10, then 20
        assert len(interp.get_stack()) == 2
        assert interp.stack_pop() == 10
        assert interp.stack_pop() == 20

    @pytest.mark.asyncio
    async def test_execute_with_multiple_stack_items(self, mock_client, interp):
        """Test executing with multiple items on stack"""
        # Setup
        word = RemoteWord(
            name="+",
            client=mock_client,
            runtime_name="typescript",
            module_name="math",
        )

        # Mock client returns sum
        mock_client.execute_word.return_value = [30]

        # Push two numbers
        interp.stack_push(10)
        interp.stack_push(20)
        await word.execute(interp)

        # Verify
        mock_client.execute_word.assert_called_once_with("+", [10, 20])
        assert len(interp.get_stack()) == 1
        assert interp.stack_pop() == 30

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self, mock_client, interp):
        """Test executing word that returns empty stack"""
        # Setup
        word = RemoteWord(
            name="DROP",
            client=mock_client,
            runtime_name="typescript",
            module_name="stdlib",
        )

        # Mock client returns empty stack
        mock_client.execute_word.return_value = []

        # Push value and execute
        interp.stack_push(42)
        await word.execute(interp)

        # Verify stack is empty
        assert len(interp.get_stack()) == 0

    @pytest.mark.asyncio
    async def test_execute_with_error(self, mock_client, interp):
        """Test error handling when remote execution fails"""
        from forthic.grpc.errors import RemoteErrorInfo

        # Setup
        word = RemoteWord(
            name="/",
            client=mock_client,
            runtime_name="typescript",
            module_name="math",
        )

        # Mock client raises error
        error_info = RemoteErrorInfo(
            message="Division by zero",
            runtime="typescript",
            error_type="ArithmeticError",
            stack_trace=["Line 1: error"],
        )
        mock_client.execute_word.side_effect = RemoteRuntimeError(error_info)

        # Push values and expect error
        interp.stack_push(10)
        interp.stack_push(0)

        with pytest.raises(RuntimeError) as exc_info:
            await word.execute(interp)

        # Verify error message includes context
        error_msg = str(exc_info.value)
        assert "math./" in error_msg
        assert "typescript runtime" in error_msg

    @pytest.mark.asyncio
    async def test_execute_with_complex_types(self, mock_client, interp):
        """Test executing with complex types (records, nested arrays)"""
        # Setup
        word = RemoteWord(
            name="PROCESS",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        # Mock client returns processed record
        mock_client.execute_word.return_value = [{"name": "Alice", "age": 31}]

        # Push complex data
        interp.stack_push({"name": "Alice", "age": 30})
        await word.execute(interp)

        # Verify
        result = interp.stack_pop()
        assert result["name"] == "Alice"
        assert result["age"] == 31

    @pytest.mark.asyncio
    async def test_get_runtime_info(self, mock_client):
        """Test getting runtime information"""
        word = RemoteWord(
            name="TEST-WORD",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        info = word.get_runtime_info()

        assert info["runtime"] == "typescript"
        assert info["is_remote"] is True
        assert info["is_standard"] is False
        assert info["available_in"] == ["typescript"]

    @pytest.mark.asyncio
    async def test_multiple_executions(self, mock_client, interp):
        """Test executing the same remote word multiple times"""
        # Setup
        word = RemoteWord(
            name="INC",
            client=mock_client,
            runtime_name="typescript",
            module_name="math",
        )

        # First execution
        mock_client.execute_word.return_value = [11]
        interp.stack_push(10)
        await word.execute(interp)
        assert interp.stack_pop() == 11

        # Second execution
        mock_client.execute_word.return_value = [21]
        interp.stack_push(20)
        await word.execute(interp)
        assert interp.stack_pop() == 21

        # Verify called twice
        assert mock_client.execute_word.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_string_values(self, mock_client, interp):
        """Test executing with string values"""
        # Setup
        word = RemoteWord(
            name="UPPERCASE",
            client=mock_client,
            runtime_name="typescript",
            module_name="string",
        )

        # Mock client returns uppercase string
        mock_client.execute_word.return_value = ["HELLO"]

        # Push string and execute
        interp.stack_push("hello")
        await word.execute(interp)

        # Verify
        assert interp.stack_pop() == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_preserves_stack_order(self, mock_client, interp):
        """Test that stack order is preserved through remote execution"""
        # Setup
        word = RemoteWord(
            name="NOOP",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        # Mock client returns same stack
        mock_client.execute_word.return_value = [1, 2, 3]

        # Push multiple values
        interp.stack_push(1)
        interp.stack_push(2)
        interp.stack_push(3)
        await word.execute(interp)

        # Verify order (top to bottom: 3, 2, 1)
        assert interp.stack_pop() == 3
        assert interp.stack_pop() == 2
        assert interp.stack_pop() == 1

    @pytest.mark.asyncio
    async def test_execute_with_none_value(self, mock_client, interp):
        """Test executing with None/null values"""
        # Setup
        word = RemoteWord(
            name="TEST",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        # Mock client returns None
        mock_client.execute_word.return_value = [None]

        # Push None and execute
        interp.stack_push(None)
        await word.execute(interp)

        # Verify
        assert interp.stack_pop() is None

    @pytest.mark.asyncio
    async def test_word_location_preserved(self, mock_client):
        """Test that word location information is preserved"""
        from forthic.tokenizer import CodeLocation

        word = RemoteWord(
            name="TEST",
            client=mock_client,
            runtime_name="typescript",
            module_name="test",
        )

        # Set location
        location = CodeLocation(source="test.forthic", line=1, column=1)
        word.set_location(location)

        # Verify location is preserved
        assert word.get_location() == location
        assert word.get_location().source == "test.forthic"
