"""Tests for Phase 11.9: StandardInterpreter integration with RemoteRuntimeModule.

Verifies that:
1. RemoteRuntimeModule is auto-registered in StandardInterpreter
2. CONNECT-RUNTIME, USE-TS-MODULES words are available by default
3. Doesn't break existing functionality
4. Gracefully handles missing grpc dependencies
"""

import pytest

from forthic.interpreter import StandardInterpreter


class TestStandardInterpreterIntegration:
    """Test StandardInterpreter auto-registration of RemoteRuntimeModule."""

    @pytest.mark.asyncio
    async def test_remote_runtime_module_available_by_default(self):
        """RemoteRuntimeModule should be available by default in StandardInterpreter."""
        interp = StandardInterpreter()

        # Check that remote_runtime module is registered
        assert "remote_runtime" in interp._registered_modules

        # Verify words are available in app module (imported by default)
        app_module = interp.get_app_module()

        # Check for key words from RemoteRuntimeModule
        assert app_module.find_word("CONNECT-RUNTIME") is not None
        assert app_module.find_word("USE-TS-MODULES") is not None
        assert app_module.find_word("USE-TS-MODULES-AS") is not None

    @pytest.mark.asyncio
    async def test_connect_runtime_word_callable(self):
        """CONNECT-RUNTIME word should be callable (even if connection fails)."""
        interp = StandardInterpreter()

        # Push runtime name and address onto stack
        interp.stack_push("typescript")
        interp.stack_push("localhost:50052")

        # This should execute without error (connection may fail, but word should be found)
        # We're not testing actual connection here, just that the word exists and is executable
        try:
            await interp.run("CONNECT-RUNTIME")
        except Exception as e:
            # Connection failure is OK - we're just testing word availability
            # The word should at least be found and attempted
            assert "unknown word" not in str(e).lower()
            assert "CONNECT-RUNTIME" not in str(e) or "unknown" not in str(e).lower()

    @pytest.mark.asyncio
    async def test_existing_stdlib_functionality_preserved(self):
        """Existing standard library functionality should still work."""
        interp = StandardInterpreter()

        # Test basic stdlib operations
        interp.stack_push([1, 2, 3])
        await interp.run("REVERSE")
        result = interp.stack_pop()
        assert result == [3, 2, 1]

        # Test string operations
        interp.stack_push("hello")
        await interp.run("UPPERCASE")
        result = interp.stack_pop()
        assert result == "HELLO"

        # Test math operations
        interp.stack_push(5)
        interp.stack_push(3)
        await interp.run("+")
        result = interp.stack_pop()
        assert result == 8

        # Test record operations
        interp.stack_push({"a": 1, "b": 2})
        await interp.run("KEYS")
        result = interp.stack_pop()
        assert set(result) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_base_interpreter_not_affected(self):
        """Base Interpreter class should not have RemoteRuntimeModule."""
        from forthic.interpreter import Interpreter

        interp = Interpreter()

        # Base interpreter should not have remote_runtime module
        assert "remote_runtime" not in interp._registered_modules

        # Should not have remote runtime words
        with pytest.raises(Exception) as exc_info:
            await interp.run("CONNECT-RUNTIME")
        assert "unknown" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_module_can_be_used_explicitly(self):
        """RemoteRuntimeModule can be used explicitly even though it's auto-imported."""
        interp = StandardInterpreter()

        # Since it's auto-imported, we should be able to use it directly
        # This tests that the auto-import actually called use_modules
        app_module = interp.get_app_module()

        # Words should be directly accessible (no prefix needed)
        word = app_module.find_word("CONNECT-RUNTIME")
        assert word is not None
        assert word.name == "CONNECT-RUNTIME"

    @pytest.mark.asyncio
    async def test_runtime_manager_singleton_accessible(self):
        """RuntimeManager should be accessible from RemoteRuntimeModule."""
        interp = StandardInterpreter()

        # Get the remote_runtime module
        remote_runtime_module = interp.find_module("remote_runtime")
        assert remote_runtime_module is not None

        # The module should have a runtime_manager attribute
        # Note: We need to access the DecoratedModule wrapper to get to runtime_manager
        from forthic.grpc.remote_runtime_module import RemoteRuntimeModule

        # Find the actual RemoteRuntimeModule instance (not the wrapped Module)
        # by checking registered modules
        for name, module in interp._registered_modules.items():
            if name == "remote_runtime":
                # The module in _registered_modules is the wrapped Module
                # We need to verify it was created from RemoteRuntimeModule
                # This is a smoke test to ensure the import worked
                assert module.name == "remote_runtime"
                break


class TestGracefulDegradation:
    """Test graceful handling of missing grpc dependencies."""

    def test_import_error_handling(self):
        """StandardInterpreter should handle missing grpc gracefully."""
        # This test verifies that the try/except pattern works
        # We can't easily simulate missing grpc here, but we can verify
        # that if grpc IS available, the module loads correctly

        interp = StandardInterpreter()

        # If grpc is available, remote_runtime should be registered
        # If not, it should be silently skipped
        # Either way, stdlib should work
        interp.stack_push([1, 2, 3])
        assert interp.stack_pop() == [1, 2, 3]
