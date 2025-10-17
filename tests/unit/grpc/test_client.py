"""
Unit tests for GrpcClient
Tests connection to TypeScript runtime and all RPC methods
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock
from forthic.grpc.client import GrpcClient
from forthic.grpc.errors import RemoteRuntimeError
from forthic.grpc import forthic_runtime_pb2


class TestGrpcClient:
    """Test suite for GrpcClient"""

    @pytest.fixture
    def mock_stub(self, monkeypatch):
        """Create a mock gRPC stub"""
        mock_stub = Mock()

        # Mock the channel and stub creation
        def mock_insecure_channel(address):
            return Mock()

        def mock_stub_init(channel):
            return mock_stub

        import grpc
        monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
        monkeypatch.setattr(
            "forthic.grpc.forthic_runtime_pb2_grpc.ForthicRuntimeStub",
            lambda channel: mock_stub
        )

        return mock_stub

    @pytest.fixture
    def client(self, mock_stub):
        """Create a GrpcClient instance with mocked stub"""
        return GrpcClient("localhost:50052")

    @pytest.mark.asyncio
    async def test_execute_word_basic(self, client, mock_stub):
        """Test executing a simple word"""
        # Setup mock response
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.int_value = 42
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("DUP", [21])

        # Verify
        assert len(result) == 1
        assert result[0] == 42
        assert mock_stub.ExecuteWord.called

    @pytest.mark.asyncio
    async def test_execute_word_with_array(self, client, mock_stub):
        """Test executing word with array input"""
        # Setup mock response with array result
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        array_value = forthic_runtime_pb2.ArrayValue()

        # Add array items
        item1 = forthic_runtime_pb2.StackValue()
        item1.int_value = 3
        item2 = forthic_runtime_pb2.StackValue()
        item2.int_value = 2
        item3 = forthic_runtime_pb2.StackValue()
        item3.int_value = 1

        array_value.items.extend([item1, item2, item3])
        result_value.array_value.CopyFrom(array_value)
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("REVERSE", [[1, 2, 3]])

        # Verify
        assert len(result) == 1
        assert result[0] == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_execute_word_with_error(self, client, mock_stub):
        """Test error handling in execute_word"""
        # Setup mock response with error
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        error_info = forthic_runtime_pb2.ErrorInfo()
        error_info.message = "Division by zero"
        error_info.runtime = "typescript"
        error_info.error_type = "ArithmeticError"
        error_info.stack_trace.extend(["Line 1: error occurred", "Line 2: in function"])
        mock_response.error.CopyFrom(error_info)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute and expect error
        with pytest.raises(RemoteRuntimeError) as exc_info:
            await client.execute_word("/", [10, 0])

        # Verify error details
        error = exc_info.value
        assert error.runtime == "typescript"
        assert error.error_type == "ArithmeticError"
        assert "Division by zero" in str(error)
        assert len(error.remote_stack_trace) == 2

    @pytest.mark.asyncio
    async def test_execute_sequence(self, client, mock_stub):
        """Test executing a sequence of words"""
        # Setup mock response
        mock_response = forthic_runtime_pb2.ExecuteSequenceResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.int_value = 9
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteSequence.return_value = mock_response

        # Execute sequence
        result = await client.execute_sequence(["DUP", "+"], [3])

        # Verify
        assert len(result) == 1
        assert result[0] == 9
        assert mock_stub.ExecuteSequence.called

    @pytest.mark.asyncio
    async def test_execute_sequence_with_error(self, client, mock_stub):
        """Test error handling in execute_sequence"""
        # Setup mock response with error
        mock_response = forthic_runtime_pb2.ExecuteSequenceResponse()
        error_info = forthic_runtime_pb2.ErrorInfo()
        error_info.message = "Stack underflow"
        error_info.runtime = "typescript"
        error_info.error_type = "StackError"
        error_info.context["word_sequence"] = "POP, POP, POP"
        mock_response.error.CopyFrom(error_info)
        mock_stub.ExecuteSequence.return_value = mock_response

        # Execute and expect error
        with pytest.raises(RemoteRuntimeError) as exc_info:
            await client.execute_sequence(["POP", "POP", "POP"], [1])

        # Verify error details
        error = exc_info.value
        assert error.runtime == "typescript"
        assert "Stack underflow" in str(error)
        assert "word_sequence" in error.context

    @pytest.mark.asyncio
    async def test_list_modules(self, client, mock_stub):
        """Test listing available modules"""
        # Setup mock response
        mock_response = forthic_runtime_pb2.ListModulesResponse()

        module1 = forthic_runtime_pb2.ModuleSummary()
        module1.name = "fs"
        module1.description = "File system operations"
        module1.word_count = 10
        module1.runtime_specific = True

        module2 = forthic_runtime_pb2.ModuleSummary()
        module2.name = "http"
        module2.description = "HTTP operations"
        module2.word_count = 5
        module2.runtime_specific = True

        mock_response.modules.extend([module1, module2])
        mock_stub.ListModules.return_value = mock_response

        # Execute
        modules = await client.list_modules()

        # Verify
        assert len(modules) == 2
        assert modules[0]["name"] == "fs"
        assert modules[0]["word_count"] == 10
        assert modules[0]["runtime_specific"] is True
        assert modules[1]["name"] == "http"

    @pytest.mark.asyncio
    async def test_get_module_info(self, client, mock_stub):
        """Test getting detailed module information"""
        # Setup mock response
        mock_response = forthic_runtime_pb2.GetModuleInfoResponse()
        mock_response.name = "array"
        mock_response.description = "Array operations"

        word1 = forthic_runtime_pb2.WordInfo()
        word1.name = "MAP"
        word1.stack_effect = "( array fn -- array )"
        word1.description = "Map function over array"

        word2 = forthic_runtime_pb2.WordInfo()
        word2.name = "FILTER"
        word2.stack_effect = "( array fn -- array )"
        word2.description = "Filter array by predicate"

        mock_response.words.extend([word1, word2])
        mock_stub.GetModuleInfo.return_value = mock_response

        # Execute
        info = await client.get_module_info("array")

        # Verify
        assert info["name"] == "array"
        assert info["description"] == "Array operations"
        assert len(info["words"]) == 2
        assert info["words"][0]["name"] == "MAP"
        assert info["words"][0]["stack_effect"] == "( array fn -- array )"
        assert info["words"][1]["name"] == "FILTER"

    @pytest.mark.asyncio
    async def test_execute_word_with_string(self, client, mock_stub):
        """Test executing word with string values"""
        # Setup mock response
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.string_value = "HELLO"
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("UPPERCASE", ["hello"])

        # Verify
        assert len(result) == 1
        assert result[0] == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_word_with_record(self, client, mock_stub):
        """Test executing word with record/dict values"""
        # Setup mock response with record
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        record_value = forthic_runtime_pb2.RecordValue()

        # Add fields
        name_value = forthic_runtime_pb2.StackValue()
        name_value.string_value = "Alice"
        age_value = forthic_runtime_pb2.StackValue()
        age_value.int_value = 30

        record_value.fields["name"].CopyFrom(name_value)
        record_value.fields["age"].CopyFrom(age_value)
        result_value.record_value.CopyFrom(record_value)
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("SOME-WORD", [{"name": "Alice", "age": 30}])

        # Verify
        assert len(result) == 1
        assert result[0] == {"name": "Alice", "age": 30}

    @pytest.mark.asyncio
    async def test_execute_word_with_null(self, client, mock_stub):
        """Test executing word with None/null values"""
        # Setup mock response with null
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.null_value.CopyFrom(forthic_runtime_pb2.NullValue())
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("SOME-WORD", [None])

        # Verify
        assert len(result) == 1
        assert result[0] is None

    @pytest.mark.asyncio
    async def test_execute_word_with_bool(self, client, mock_stub):
        """Test executing word with boolean values"""
        # Setup mock response with bool
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.bool_value = True
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("NOT", [False])

        # Verify
        assert len(result) == 1
        assert result[0] is True

    @pytest.mark.asyncio
    async def test_execute_word_with_float(self, client, mock_stub):
        """Test executing word with float values"""
        # Setup mock response with float
        mock_response = forthic_runtime_pb2.ExecuteWordResponse()
        result_value = forthic_runtime_pb2.StackValue()
        result_value.float_value = 3.14
        mock_response.result_stack.append(result_value)
        mock_stub.ExecuteWord.return_value = mock_response

        # Execute
        result = await client.execute_word("SOME-WORD", [3.14])

        # Verify
        assert len(result) == 1
        assert result[0] == 3.14

    def test_close(self, client):
        """Test closing the client connection"""
        # Should not raise any errors
        client.close()

    def test_client_initialization_custom_address(self):
        """Test client initialization with custom address"""
        client = GrpcClient("remote-host:9999")
        assert client.address == "remote-host:9999"

    def test_client_initialization_default_address(self):
        """Test client initialization with default address"""
        client = GrpcClient()
        assert client.address == "localhost:50052"
