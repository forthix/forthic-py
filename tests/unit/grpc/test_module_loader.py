"""
Unit tests for module loader functionality
"""
import pytest
from pathlib import Path
import tempfile
import yaml

from forthic.grpc.module_loader import load_modules_from_config, ModuleLoadError
from forthic.decorators import DecoratedModule, Word


# Test modules for loading
class TestModuleA(DecoratedModule):
    """Simple test module"""

    def __init__(self):
        super().__init__("test_a")

    @Word("( a b -- c )", "Add two numbers")
    async def ADD(self, a: int, b: int) -> int:
        return a + b


class TestModuleB(DecoratedModule):
    """Another test module"""

    def __init__(self):
        super().__init__("test_b")

    @Word("( a b -- c )", "Multiply two numbers")
    async def MULTIPLY(self, a: int, b: int) -> int:
        return a * b


class TestModuleLoader:
    """Test suite for module loader"""

    def test_load_valid_module(self):
        """Test loading a valid module from config"""
        config = {
            'modules': [
                {
                    'name': 'test_a',
                    'import_path': 'tests.unit.grpc.test_module_loader:TestModuleA',
                    'optional': False,
                    'description': 'Test module A'
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            modules = load_modules_from_config(config_path)

            assert 'test_a' in modules
            assert isinstance(modules['test_a'], TestModuleA)
            assert hasattr(modules['test_a'], 'ADD')

        finally:
            Path(config_path).unlink()

    def test_load_multiple_modules(self):
        """Test loading multiple modules from config"""
        config = {
            'modules': [
                {
                    'name': 'test_a',
                    'import_path': 'tests.unit.grpc.test_module_loader:TestModuleA',
                    'optional': False
                },
                {
                    'name': 'test_b',
                    'import_path': 'tests.unit.grpc.test_module_loader:TestModuleB',
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            modules = load_modules_from_config(config_path)

            assert len(modules) == 2
            assert 'test_a' in modules
            assert 'test_b' in modules
            assert isinstance(modules['test_a'], TestModuleA)
            assert isinstance(modules['test_b'], TestModuleB)

        finally:
            Path(config_path).unlink()

    def test_optional_module_missing(self):
        """Test that optional modules don't fail when missing"""
        config = {
            'modules': [
                {
                    'name': 'nonexistent',
                    'import_path': 'fake.module:FakeClass',
                    'optional': True
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Should not raise - optional module
            modules = load_modules_from_config(config_path)
            assert 'nonexistent' not in modules
            assert len(modules) == 0

        finally:
            Path(config_path).unlink()

    def test_required_module_missing(self):
        """Test that required modules fail when missing"""
        config = {
            'modules': [
                {
                    'name': 'nonexistent',
                    'import_path': 'fake.module:FakeClass',
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Should raise - required module
            with pytest.raises(ModuleLoadError):
                load_modules_from_config(config_path)

        finally:
            Path(config_path).unlink()

    def test_mix_optional_and_required(self):
        """Test loading a mix of optional and required modules"""
        config = {
            'modules': [
                {
                    'name': 'test_a',
                    'import_path': 'tests.unit.grpc.test_module_loader:TestModuleA',
                    'optional': False
                },
                {
                    'name': 'nonexistent',
                    'import_path': 'fake.module:FakeClass',
                    'optional': True
                },
                {
                    'name': 'test_b',
                    'import_path': 'tests.unit.grpc.test_module_loader:TestModuleB',
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Should load valid modules, skip optional missing one
            modules = load_modules_from_config(config_path)

            assert len(modules) == 2
            assert 'test_a' in modules
            assert 'test_b' in modules
            assert 'nonexistent' not in modules

        finally:
            Path(config_path).unlink()

    def test_invalid_import_path_format(self):
        """Test that invalid import path format raises error"""
        config = {
            'modules': [
                {
                    'name': 'invalid',
                    'import_path': 'no_colon_separator',  # Missing :ClassName
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            with pytest.raises(ModuleLoadError) as exc_info:
                load_modules_from_config(config_path)

            assert 'Invalid import_path' in str(exc_info.value)

        finally:
            Path(config_path).unlink()

    def test_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_modules_from_config('/nonexistent/path/to/config.yaml')

    def test_empty_config(self):
        """Test loading empty config returns empty dict"""
        config = {}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            modules = load_modules_from_config(config_path)
            assert len(modules) == 0

        finally:
            Path(config_path).unlink()

    def test_no_modules_key(self):
        """Test config without 'modules' key returns empty dict"""
        config = {
            'other_key': 'some_value'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            modules = load_modules_from_config(config_path)
            assert len(modules) == 0

        finally:
            Path(config_path).unlink()

    def test_empty_modules_list(self):
        """Test config with empty modules list"""
        config = {
            'modules': []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            modules = load_modules_from_config(config_path)
            assert len(modules) == 0

        finally:
            Path(config_path).unlink()

    def test_module_class_not_found(self):
        """Test that non-existent class name raises error"""
        config = {
            'modules': [
                {
                    'name': 'bad_class',
                    'import_path': 'tests.unit.grpc.test_module_loader:NonExistentClass',
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            with pytest.raises(ModuleLoadError):
                load_modules_from_config(config_path)

        finally:
            Path(config_path).unlink()
