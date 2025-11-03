"""
Integration tests for server configuration
"""
import tempfile
import yaml
from pathlib import Path

from forthic.grpc.server import ForthicRuntimeServicer


class TestServerConfiguration:
    """Test suite for server configuration"""

    def test_backward_compatibility_no_config(self):
        """Test that server works without config (backward compatible)"""
        # Create servicer without config
        servicer = ForthicRuntimeServicer(modules_config=None)

        # Should have runtime_modules dict (even if empty)
        assert hasattr(servicer, 'runtime_modules')
        assert isinstance(servicer.runtime_modules, dict)

        # If pandas is installed, it should be loaded
        # If not, that's also fine (optional dependency)
        print(f"Loaded modules (no config): {list(servicer.runtime_modules.keys())}")

    def test_server_with_config(self):
        """Test that server loads modules from config"""
        # Create a test config
        config = {
            'modules': [
                {
                    'name': 'test_module',
                    'import_path': 'tests.unit.grpc.test_module_loader:FixtureModuleA',
                    'optional': False,
                    'description': 'Test module for server config'
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Create servicer with config
            servicer = ForthicRuntimeServicer(modules_config=config_path)

            # Should have loaded the test module
            assert 'test_module' in servicer.runtime_modules
            assert hasattr(servicer.runtime_modules['test_module'], 'ADD')

            print(f"Loaded modules (with config): {list(servicer.runtime_modules.keys())}")

        finally:
            Path(config_path).unlink()

    def test_server_with_optional_module_missing(self):
        """Test that server starts even if optional module is missing"""
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
            servicer = ForthicRuntimeServicer(modules_config=config_path)

            # Nonexistent module should not be loaded
            assert 'nonexistent' not in servicer.runtime_modules

        finally:
            Path(config_path).unlink()

    def test_server_config_loads_multiple_modules(self):
        """Test that server can load multiple modules from config"""
        config = {
            'modules': [
                {
                    'name': 'test_a',
                    'import_path': 'tests.unit.grpc.test_module_loader:FixtureModuleA',
                    'optional': False
                },
                {
                    'name': 'test_b',
                    'import_path': 'tests.unit.grpc.test_module_loader:FixtureModuleB',
                    'optional': False
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            servicer = ForthicRuntimeServicer(modules_config=config_path)

            # Both modules should be loaded
            assert 'test_a' in servicer.runtime_modules
            assert 'test_b' in servicer.runtime_modules
            assert len(servicer.runtime_modules) == 2

        finally:
            Path(config_path).unlink()
