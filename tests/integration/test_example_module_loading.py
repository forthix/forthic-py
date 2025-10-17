"""
Integration test for ExampleModule loading via configuration
Tests that the example module can be loaded and used in server
"""
import pytest
import os
from pathlib import Path

from forthic.grpc.server import ForthicRuntimeServicer
from forthic.grpc.module_loader import load_modules_from_config


class TestExampleModuleLoading:
    """Test ExampleModule loads correctly via config"""

    def test_example_module_loads_from_config(self):
        """Test that ExampleModule can be loaded via config file"""
        # Get path to example config
        repo_root = Path(__file__).parent.parent.parent
        config_path = repo_root / "examples" / "example_modules_config.yaml"

        assert config_path.exists(), f"Config file not found: {config_path}"

        # Load modules directly
        modules = load_modules_from_config(str(config_path))

        # Should have loaded example module (pandas is optional, may not be present)
        assert "example" in modules, f"example module not loaded. Available: {list(modules.keys())}"

        # Check it's the right type
        example_mod = modules["example"]
        assert example_mod.name == "example"

        # Check it has expected words via get_word_docs
        assert hasattr(example_mod, 'get_word_docs')
        word_docs = example_mod.get_word_docs()
        word_names = [doc['name'] for doc in word_docs]

        # Verify all expected words are present
        expected_words = [
            'MULTIPLY', 'SQUARE', 'POWER',
            'REVERSE_TEXT', 'COUNT_CHAR', 'MAKE_SENTENCE',
            'SUM_LIST', 'AVG_LIST', 'CHUNK_LIST',
            'FIBONACCI', 'IS_PRIME', 'MAP_RANGE'
        ]

        for word in expected_words:
            assert word in word_names, f"Expected word {word} not found in module"

    def test_example_module_in_server(self):
        """Test that server can be initialized with example module config"""
        # Get path to example config
        repo_root = Path(__file__).parent.parent.parent
        config_path = repo_root / "examples" / "example_modules_config.yaml"

        # Create servicer with config
        servicer = ForthicRuntimeServicer(modules_config=str(config_path))

        # Check example module is in runtime modules
        assert "example" in servicer.runtime_modules

        # Check interpreter has the module registered
        example_mod = servicer.runtime_modules["example"]
        assert example_mod in servicer.interpreter._registered_modules.values()

    @pytest.mark.asyncio
    async def test_example_module_words_executable(self):
        """Test that ExampleModule words can be executed via server's interpreter"""
        # Get path to example config
        repo_root = Path(__file__).parent.parent.parent
        config_path = repo_root / "examples" / "example_modules_config.yaml"

        # Create servicer with config
        servicer = ForthicRuntimeServicer(modules_config=str(config_path))

        # Test MULTIPLY word
        result = await servicer._execute_with_stack("MULTIPLY", [5, 3])
        assert result == [15], f"Expected [15], got {result}"

        # Test SQUARE word
        result = await servicer._execute_with_stack("SQUARE", [7])
        assert result == [49], f"Expected [49], got {result}"

        # Test REVERSE_TEXT word
        result = await servicer._execute_with_stack("REVERSE_TEXT", ["hello"])
        assert result == ["olleh"], f"Expected ['olleh'], got {result}"

        # Test SUM_LIST word
        result = await servicer._execute_with_stack("SUM_LIST", [[1, 2, 3, 4, 5]])
        assert result == [15], f"Expected [15], got {result}"

        # Test IS_PRIME word
        result = await servicer._execute_with_stack("IS_PRIME", [7])
        assert result == [True], f"Expected [True], got {result}"

        result = await servicer._execute_with_stack("IS_PRIME", [8])
        assert result == [False], f"Expected [False], got {result}"
