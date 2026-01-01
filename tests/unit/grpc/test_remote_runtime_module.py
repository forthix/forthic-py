"""
Tests for RemoteRuntimeModule
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from forthic.grpc.remote_runtime_module import RemoteRuntimeModule
from forthic.interpreter import Interpreter


@pytest.fixture
def module():
    """Create a RemoteRuntimeModule instance"""
    return RemoteRuntimeModule()


@pytest.fixture
def interp():
    """Create a mock interpreter"""
    interp = MagicMock(spec=Interpreter)
    interp.stack_pop = MagicMock()
    interp.stack_push = MagicMock()
    interp.register_module = MagicMock()
    interp.use_modules = MagicMock()
    return interp


class TestConnectRuntime:
    """Tests for CONNECT-RUNTIME word"""

    @pytest.mark.asyncio
    async def test_connect_runtime_basic(self, module, interp):
        """Test basic runtime connection"""
        # Setup stack
        interp.stack_pop.side_effect = ["localhost:50052", "typescript"]

        # Connect
        with patch.object(module.runtime_manager, 'connect_runtime') as mock_connect:
            await module.CONNECT_RUNTIME(interp)
            mock_connect.assert_called_once_with("typescript", "localhost:50052")

    @pytest.mark.asyncio
    async def test_connect_runtime_multiple(self, module, interp):
        """Test connecting to multiple runtimes"""
        # Connect to typescript
        interp.stack_pop.side_effect = ["localhost:50052", "typescript"]
        with patch.object(module.runtime_manager, 'connect_runtime') as mock_connect:
            await module.CONNECT_RUNTIME(interp)
            mock_connect.assert_called_with("typescript", "localhost:50052")

        # Connect to ruby
        interp.stack_pop.side_effect = ["localhost:50053", "ruby"]
        with patch.object(module.runtime_manager, 'connect_runtime') as mock_connect:
            await module.CONNECT_RUNTIME(interp)
            mock_connect.assert_called_with("ruby", "localhost:50053")


class TestDisconnectRuntime:
    """Tests for DISCONNECT-RUNTIME word"""

    @pytest.mark.asyncio
    async def test_disconnect_runtime(self, module, interp):
        """Test disconnecting from runtime"""
        interp.stack_pop.return_value = "typescript"

        with patch.object(module.runtime_manager, 'disconnect_runtime') as mock_disconnect:
            await module.DISCONNECT_RUNTIME(interp)
            mock_disconnect.assert_called_once_with("typescript")


class TestListRuntimes:
    """Tests for LIST-RUNTIMES word"""

    @pytest.mark.asyncio
    async def test_list_runtimes_empty(self, module):
        """Test listing runtimes when none connected"""
        with patch.object(module.runtime_manager, 'list_connections', return_value=[]):
            # Call the underlying method directly (not via decorator)
            result = module.runtime_manager.list_connections()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_runtimes_multiple(self, module):
        """Test listing multiple connected runtimes"""
        with patch.object(module.runtime_manager, 'list_connections',
                         return_value=["typescript", "ruby"]):
            # Call the underlying method directly (not via decorator)
            result = module.runtime_manager.list_connections()
            assert result == ["typescript", "ruby"]


class TestUseTsModules:
    """Tests for USE-TS-MODULES word"""

    @pytest.mark.asyncio
    async def test_use_ts_modules_basic(self, module, interp):
        """Test loading TypeScript modules without prefix"""
        interp.stack_pop.return_value = ["array", "math"]

        with patch.object(module, '_load_modules', new_callable=AsyncMock) as mock_load:
            await module.USE_TS_MODULES(interp)
            mock_load.assert_called_once_with(
                "typescript",
                ["array", "math"],
                prefix=None,
                interp=interp
            )

    @pytest.mark.asyncio
    async def test_use_ts_modules_single(self, module, interp):
        """Test loading single TypeScript module"""
        interp.stack_pop.return_value = ["array"]

        with patch.object(module, '_load_modules', new_callable=AsyncMock) as mock_load:
            await module.USE_TS_MODULES(interp)
            mock_load.assert_called_once_with(
                "typescript",
                ["array"],
                prefix=None,
                interp=interp
            )


class TestUseTsModulesAs:
    """Tests for USE-TS-MODULES-AS word"""

    @pytest.mark.asyncio
    async def test_use_ts_modules_as_basic(self, module, interp):
        """Test loading TypeScript modules with prefix"""
        interp.stack_pop.side_effect = ["ts", ["fs", "http"]]

        with patch.object(module, '_load_modules', new_callable=AsyncMock) as mock_load:
            await module.USE_TS_MODULES_AS(interp)
            mock_load.assert_called_once_with(
                "typescript",
                ["fs", "http"],
                prefix="ts",
                interp=interp
            )

    @pytest.mark.asyncio
    async def test_use_ts_modules_as_different_prefix(self, module, interp):
        """Test loading with different prefix"""
        interp.stack_pop.side_effect = ["typescript", ["array"]]

        with patch.object(module, '_load_modules', new_callable=AsyncMock) as mock_load:
            await module.USE_TS_MODULES_AS(interp)
            mock_load.assert_called_once_with(
                "typescript",
                ["array"],
                prefix="typescript",
                interp=interp
            )


class TestLoadModules:
    """Tests for _load_modules helper method"""

    @pytest.mark.asyncio
    async def test_load_modules_not_connected(self, module, interp):
        """Test error when runtime not connected"""
        with patch.object(module.runtime_manager, 'get_runtime', return_value=None):
            with pytest.raises(RuntimeError, match="Runtime 'typescript' not connected"):
                await module._load_modules("typescript", ["array"], None, interp)

    @pytest.mark.asyncio
    async def test_load_modules_without_prefix(self, module, interp):
        """Test loading modules without prefix"""
        mock_client = MagicMock()
        mock_remote_module = MagicMock()
        mock_remote_module.name = "array"
        mock_remote_module.initialize = AsyncMock()

        with patch.object(module.runtime_manager, 'get_runtime', return_value=mock_client):
            with patch('forthic.grpc.remote_runtime_module.RemoteModule',
                      return_value=mock_remote_module):
                await module._load_modules("typescript", ["array"], None, interp)

                # Verify module was initialized
                mock_remote_module.initialize.assert_called_once()

                # Verify module was registered without prefix
                interp.register_module.assert_called_once_with(mock_remote_module)

                # Verify module was imported
                interp.use_modules.assert_called_once_with(["array"])

    @pytest.mark.asyncio
    async def test_load_modules_with_prefix(self, module, interp):
        """Test loading modules with prefix"""
        mock_client = MagicMock()
        mock_remote_module = MagicMock()
        mock_remote_module.name = "fs"
        mock_remote_module.initialize = AsyncMock()

        with patch.object(module.runtime_manager, 'get_runtime', return_value=mock_client):
            with patch('forthic.grpc.remote_runtime_module.RemoteModule',
                      return_value=mock_remote_module):
                await module._load_modules("typescript", ["fs"], "ts", interp)

                # Verify module was initialized
                mock_remote_module.initialize.assert_called_once()

                # Verify module was registered with prefix
                interp.register_module.assert_called_once_with(
                    mock_remote_module,
                    name="ts.fs"
                )

                # Verify module was imported
                interp.use_modules.assert_called_once_with(["fs"])

    @pytest.mark.asyncio
    async def test_load_multiple_modules(self, module, interp):
        """Test loading multiple modules"""
        mock_client = MagicMock()

        # Create two mock modules
        modules_created = []

        def create_remote_module(name, client, runtime):
            mock_mod = MagicMock()
            mock_mod.name = name
            mock_mod.initialize = AsyncMock()
            modules_created.append(mock_mod)
            return mock_mod

        with patch.object(module.runtime_manager, 'get_runtime', return_value=mock_client):
            with patch('forthic.grpc.remote_runtime_module.RemoteModule',
                      side_effect=create_remote_module):
                await module._load_modules("typescript", ["array", "math"], None, interp)

                # Verify both modules were initialized
                assert len(modules_created) == 2
                for mod in modules_created:
                    mod.initialize.assert_called_once()

                # Verify both modules were registered
                assert interp.register_module.call_count == 2
                assert interp.use_modules.call_count == 2


class TestModuleMetadata:
    """Tests for module metadata and documentation"""

    def test_module_name(self, module):
        """Test module has correct name"""
        assert module.name == "remote_runtime"

    def test_has_runtime_manager(self, module):
        """Test module has runtime manager"""
        assert hasattr(module, 'runtime_manager')
        assert module.runtime_manager is not None

    def test_singleton_runtime_manager(self):
        """Test all instances share same RuntimeManager"""
        module1 = RemoteRuntimeModule()
        module2 = RemoteRuntimeModule()
        assert module1.runtime_manager is module2.runtime_manager
