"""
Unit tests for RemoteModule
Tests module that wraps remote runtime words via gRPC
"""
import pytest
from unittest.mock import Mock, AsyncMock
from forthic.grpc.remote_module import RemoteModule
from forthic.grpc.remote_word import RemoteWord
from forthic.interpreter import Interpreter


class TestRemoteModule:
    """Test suite for RemoteModule"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock GrpcClient"""
        client = Mock()
        client.get_module_info = AsyncMock()
        client.execute_word = AsyncMock()
        return client

    @pytest.fixture
    def interp(self):
        """Create an interpreter instance"""
        return Interpreter()

    @pytest.mark.asyncio
    async def test_remote_module_initialization(self, mock_client):
        """Test RemoteModule initialization with all parameters"""
        module = RemoteModule(
            module_name="array", client=mock_client, runtime_name="typescript"
        )

        assert module.name == "array"
        assert module.get_runtime_name() == "typescript"
        assert module.initialized is False
        assert module.module_info is None

    @pytest.mark.asyncio
    async def test_remote_module_default_runtime_name(self, mock_client):
        """Test RemoteModule with default runtime name"""
        module = RemoteModule(module_name="test", client=mock_client)

        assert module.get_runtime_name() == "remote"

    @pytest.mark.asyncio
    async def test_initialize_discovers_words(self, mock_client):
        """Test that initialize() discovers words from remote runtime"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "array",
            "description": "Array manipulation module",
            "words": [
                {
                    "name": "REVERSE",
                    "stack_effect": "( array -- array )",
                    "description": "Reverse an array",
                },
                {
                    "name": "MAP",
                    "stack_effect": "( array lambda -- array )",
                    "description": "Map function over array",
                },
                {
                    "name": "FILTER",
                    "stack_effect": "( array lambda -- array )",
                    "description": "Filter array elements",
                },
            ],
        }

        # Initialize module
        module = RemoteModule("array", mock_client, "typescript")
        await module.initialize()

        # Verify initialization
        assert module.initialized is True
        assert module.module_info is not None
        assert module.module_info["name"] == "array"

        # Verify words were created
        words = module.exportable_words()
        assert len(words) == 3

        # Verify word names
        word_names = {word.name for word in words}
        assert word_names == {"REVERSE", "MAP", "FILTER"}

        # Verify words are RemoteWord instances
        for word in words:
            assert isinstance(word, RemoteWord)
            assert word.get_runtime_name() == "typescript"
            assert word.get_module_name() == "array"

    @pytest.mark.asyncio
    async def test_initialize_creates_exportable_words(self, mock_client):
        """Test that discovered words are added as exportable"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "math",
            "description": "Math module",
            "words": [
                {
                    "name": "ADD",
                    "stack_effect": "( a b -- sum )",
                    "description": "Add two numbers",
                }
            ],
        }

        # Initialize module
        module = RemoteModule("math", mock_client, "typescript")
        await module.initialize()

        # Verify word is exportable
        exportable_words = module.exportable_words()
        assert len(exportable_words) == 1
        assert exportable_words[0].name == "ADD"

        # Verify word is in exportable list
        assert "ADD" in module.exportable

    @pytest.mark.asyncio
    async def test_initialize_preserves_word_metadata(self, mock_client):
        """Test that word metadata is preserved from remote runtime"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "string",
            "description": "String module",
            "words": [
                {
                    "name": "UPPERCASE",
                    "stack_effect": "( str -- str )",
                    "description": "Convert to uppercase",
                }
            ],
        }

        # Initialize module
        module = RemoteModule("string", mock_client, "typescript")
        await module.initialize()

        # Get the word
        word = module.find_word("UPPERCASE")
        assert word is not None
        assert isinstance(word, RemoteWord)
        assert word.stack_effect == "( str -- str )"
        assert word.description == "Convert to uppercase"

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, mock_client):
        """Test that calling initialize() multiple times is safe"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "test",
            "description": "Test module",
            "words": [
                {
                    "name": "WORD1",
                    "stack_effect": "( -- )",
                    "description": "Test word",
                }
            ],
        }

        # Initialize multiple times
        module = RemoteModule("test", mock_client, "typescript")
        await module.initialize()
        await module.initialize()
        await module.initialize()

        # Verify get_module_info was only called once
        assert mock_client.get_module_info.call_count == 1

        # Verify only one word exists (not duplicated)
        words = module.exportable_words()
        assert len(words) == 1

    @pytest.mark.asyncio
    async def test_initialize_with_empty_module(self, mock_client):
        """Test initializing module with no words"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "empty",
            "description": "Empty module",
            "words": [],
        }

        # Initialize module
        module = RemoteModule("empty", mock_client, "typescript")
        await module.initialize()

        # Verify initialization succeeded
        assert module.initialized is True

        # Verify no words exist
        words = module.exportable_words()
        assert len(words) == 0

    @pytest.mark.asyncio
    async def test_set_interp_requires_initialization(self, mock_client, interp):
        """Test that set_interp() raises error if not initialized"""
        module = RemoteModule("test", mock_client, "typescript")

        # Should raise error when not initialized
        with pytest.raises(RuntimeError) as exc_info:
            module.set_interp(interp)

        # Verify error message
        error_msg = str(exc_info.value)
        assert "must be initialized before use" in error_msg
        assert "test" in error_msg
        assert "await module.initialize()" in error_msg

    @pytest.mark.asyncio
    async def test_set_interp_after_initialization(self, mock_client, interp):
        """Test that set_interp() works after initialization"""
        # Setup and initialize
        mock_client.get_module_info.return_value = {
            "name": "test",
            "description": "Test module",
            "words": [],
        }

        module = RemoteModule("test", mock_client, "typescript")
        await module.initialize()

        # Should work after initialization
        module.set_interp(interp)
        assert module.get_interp() == interp

    @pytest.mark.asyncio
    async def test_get_module_info(self, mock_client):
        """Test getting cached module info"""
        # Setup and initialize
        module_info = {
            "name": "test",
            "description": "Test module",
            "words": [
                {
                    "name": "TEST-WORD",
                    "stack_effect": "( -- )",
                    "description": "Test",
                }
            ],
        }
        mock_client.get_module_info.return_value = module_info

        module = RemoteModule("test", mock_client, "typescript")

        # Before initialization
        assert module.get_module_info() is None

        # After initialization
        await module.initialize()
        cached_info = module.get_module_info()
        assert cached_info == module_info

    @pytest.mark.asyncio
    async def test_find_word_after_initialization(self, mock_client):
        """Test finding words by name after initialization"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "test",
            "description": "Test module",
            "words": [
                {
                    "name": "WORD1",
                    "stack_effect": "( -- )",
                    "description": "First word",
                },
                {
                    "name": "WORD2",
                    "stack_effect": "( -- )",
                    "description": "Second word",
                },
            ],
        }

        # Initialize module
        module = RemoteModule("test", mock_client, "typescript")
        await module.initialize()

        # Find words
        word1 = module.find_word("WORD1")
        word2 = module.find_word("WORD2")
        word3 = module.find_word("NONEXISTENT")

        assert word1 is not None
        assert word1.name == "WORD1"
        assert word2 is not None
        assert word2.name == "WORD2"
        assert word3 is None

    @pytest.mark.asyncio
    async def test_remote_words_can_execute(self, mock_client, interp):
        """Test that remote words created by module can execute"""
        # Setup mock response
        mock_client.get_module_info.return_value = {
            "name": "array",
            "description": "Array module",
            "words": [
                {
                    "name": "REVERSE",
                    "stack_effect": "( array -- array )",
                    "description": "Reverse array",
                }
            ],
        }

        # Mock execute_word
        mock_client.execute_word.return_value = [[3, 2, 1]]

        # Initialize module and set interpreter
        module = RemoteModule("array", mock_client, "typescript")
        await module.initialize()
        module.set_interp(interp)

        # Find and execute word
        word = module.find_word("REVERSE")
        assert word is not None

        interp.stack_push([1, 2, 3])
        await word.execute(interp)

        # Verify result
        result = interp.stack_pop()
        assert result == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_module_with_many_words(self, mock_client):
        """Test module with many words (realistic scenario)"""
        # Setup mock response with many words
        words_data = [
            {
                "name": f"WORD{i}",
                "stack_effect": f"( arg{i} -- result{i} )",
                "description": f"Word number {i}",
            }
            for i in range(20)
        ]

        mock_client.get_module_info.return_value = {
            "name": "large",
            "description": "Large module",
            "words": words_data,
        }

        # Initialize module
        module = RemoteModule("large", mock_client, "typescript")
        await module.initialize()

        # Verify all words created
        exportable_words = module.exportable_words()
        assert len(exportable_words) == 20

        # Verify each word exists
        for i in range(20):
            word = module.find_word(f"WORD{i}")
            assert word is not None
            assert word.description == f"Word number {i}"

    @pytest.mark.asyncio
    async def test_module_name_matches(self, mock_client):
        """Test that module name is preserved"""
        module = RemoteModule("custom_name", mock_client, "typescript")

        assert module.get_name() == "custom_name"
        assert module.name == "custom_name"

    @pytest.mark.asyncio
    async def test_error_during_initialization(self, mock_client):
        """Test error handling when get_module_info fails"""
        # Setup mock to raise error
        mock_client.get_module_info.side_effect = Exception("Connection failed")

        # Initialize should propagate error
        module = RemoteModule("test", mock_client, "typescript")

        with pytest.raises(Exception) as exc_info:
            await module.initialize()

        assert "Connection failed" in str(exc_info.value)
        assert module.initialized is False

    @pytest.mark.asyncio
    async def test_module_inheritance_from_base_module(self, mock_client):
        """Test that RemoteModule properly inherits from Module"""
        from forthic.module import Module

        module = RemoteModule("test", mock_client, "typescript")

        # Verify inheritance
        assert isinstance(module, Module)

        # Verify base class methods work
        assert module.get_name() == "test"
        assert len(module.exportable_words()) == 0  # Before initialization

    @pytest.mark.asyncio
    async def test_multiple_modules_same_client(self, mock_client):
        """Test creating multiple modules with same client"""
        # Setup mock responses
        async def get_module_info_side_effect(module_name):
            if module_name == "array":
                return {
                    "name": "array",
                    "description": "Array module",
                    "words": [
                        {
                            "name": "REVERSE",
                            "stack_effect": "( array -- array )",
                            "description": "Reverse",
                        }
                    ],
                }
            elif module_name == "math":
                return {
                    "name": "math",
                    "description": "Math module",
                    "words": [
                        {
                            "name": "ADD",
                            "stack_effect": "( a b -- sum )",
                            "description": "Add",
                        }
                    ],
                }
            return {"name": module_name, "description": "", "words": []}

        mock_client.get_module_info.side_effect = get_module_info_side_effect

        # Create and initialize multiple modules
        array_module = RemoteModule("array", mock_client, "typescript")
        math_module = RemoteModule("math", mock_client, "typescript")

        await array_module.initialize()
        await math_module.initialize()

        # Verify both initialized correctly
        assert array_module.find_word("REVERSE") is not None
        assert math_module.find_word("ADD") is not None

        # Verify they're separate modules
        assert array_module.find_word("ADD") is None
        assert math_module.find_word("REVERSE") is None
