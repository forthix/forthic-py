"""
Unit tests for RuntimeManager
Tests singleton pattern, connection management, and lifecycle
"""
import pytest
from unittest.mock import Mock, patch
from forthic.grpc.runtime_manager import RuntimeManager
from forthic.grpc.client import GrpcClient


class TestRuntimeManager:
    """Test suite for RuntimeManager singleton"""

    def teardown_method(self):
        """Clean up after each test - reset singleton"""
        # Reset the singleton instance
        RuntimeManager._instance = None

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_singleton_pattern(self, mock_client_class):
        """Test that RuntimeManager is a singleton"""
        manager1 = RuntimeManager()
        manager2 = RuntimeManager()

        # Should be the same instance
        assert manager1 is manager2

        # Should have connections dict
        assert hasattr(manager1, "connections")
        assert isinstance(manager1.connections, dict)

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_connect_runtime_creates_new_connection(self, mock_client_class):
        """Test connecting to a new runtime creates a client"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect to runtime
        manager = RuntimeManager()
        client = manager.connect_runtime("typescript", "localhost:50052")

        # Verify client was created with correct address
        mock_client_class.assert_called_once_with("localhost:50052")
        assert client is mock_client
        assert "typescript" in manager.connections
        assert manager.connections["typescript"] is mock_client

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_connect_runtime_reuses_existing_connection(self, mock_client_class):
        """Test that connecting to same runtime reuses the connection"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect twice
        manager = RuntimeManager()
        client1 = manager.connect_runtime("typescript", "localhost:50052")
        client2 = manager.connect_runtime("typescript", "localhost:50052")

        # Should only create client once
        mock_client_class.assert_called_once()
        assert client1 is client2
        assert client1 is mock_client

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_connect_multiple_runtimes(self, mock_client_class):
        """Test connecting to multiple runtimes"""
        # Setup mocks for different clients
        mock_ts_client = Mock(spec=GrpcClient)
        mock_py_client = Mock(spec=GrpcClient)
        mock_client_class.side_effect = [mock_ts_client, mock_py_client]

        # Connect to multiple runtimes
        manager = RuntimeManager()
        ts_client = manager.connect_runtime("typescript", "localhost:50052")
        py_client = manager.connect_runtime("python", "localhost:50051")

        # Verify both clients created
        assert mock_client_class.call_count == 2
        assert ts_client is mock_ts_client
        assert py_client is mock_py_client
        assert len(manager.connections) == 2
        assert manager.connections["typescript"] is mock_ts_client
        assert manager.connections["python"] is mock_py_client

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_get_runtime_existing(self, mock_client_class):
        """Test getting an existing runtime connection"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect and then get
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")
        retrieved_client = manager.get_runtime("typescript")

        # Should return the same client
        assert retrieved_client is mock_client

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_get_runtime_nonexistent(self, mock_client_class):
        """Test getting a runtime that doesn't exist"""
        manager = RuntimeManager()
        client = manager.get_runtime("nonexistent")

        # Should return None
        assert client is None

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_disconnect_runtime(self, mock_client_class):
        """Test disconnecting from a runtime"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect and disconnect
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")
        assert "typescript" in manager.connections

        manager.disconnect_runtime("typescript")

        # Verify client.close() was called
        mock_client.close.assert_called_once()

        # Verify connection removed
        assert "typescript" not in manager.connections
        assert manager.get_runtime("typescript") is None

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_disconnect_runtime_nonexistent(self, mock_client_class):
        """Test disconnecting from a runtime that doesn't exist"""
        manager = RuntimeManager()

        # Should not raise error
        manager.disconnect_runtime("nonexistent")

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_disconnect_all(self, mock_client_class):
        """Test disconnecting from all runtimes"""
        # Setup mocks
        mock_ts_client = Mock(spec=GrpcClient)
        mock_py_client = Mock(spec=GrpcClient)
        mock_rb_client = Mock(spec=GrpcClient)
        mock_client_class.side_effect = [mock_ts_client, mock_py_client, mock_rb_client]

        # Connect to multiple runtimes
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")
        manager.connect_runtime("python", "localhost:50051")
        manager.connect_runtime("ruby", "localhost:50053")

        assert len(manager.connections) == 3

        # Disconnect all
        manager.disconnect_all()

        # Verify all clients closed
        mock_ts_client.close.assert_called_once()
        mock_py_client.close.assert_called_once()
        mock_rb_client.close.assert_called_once()

        # Verify connections cleared
        assert len(manager.connections) == 0

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_list_connections_empty(self, mock_client_class):
        """Test listing connections when none exist"""
        manager = RuntimeManager()
        connections = manager.list_connections()

        assert connections == []

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_list_connections_multiple(self, mock_client_class):
        """Test listing multiple connections"""
        # Setup mocks
        mock_ts_client = Mock(spec=GrpcClient)
        mock_py_client = Mock(spec=GrpcClient)
        mock_client_class.side_effect = [mock_ts_client, mock_py_client]

        # Connect to multiple runtimes
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")
        manager.connect_runtime("python", "localhost:50051")

        connections = manager.list_connections()

        # Should list all connection names
        assert len(connections) == 2
        assert "typescript" in connections
        assert "python" in connections

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_is_connected_true(self, mock_client_class):
        """Test is_connected returns True for connected runtime"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")

        # Check connection
        assert manager.is_connected("typescript") is True

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_is_connected_false(self, mock_client_class):
        """Test is_connected returns False for non-connected runtime"""
        manager = RuntimeManager()

        # Check connection
        assert manager.is_connected("nonexistent") is False

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_is_connected_after_disconnect(self, mock_client_class):
        """Test is_connected returns False after disconnecting"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Connect and disconnect
        manager = RuntimeManager()
        manager.connect_runtime("typescript", "localhost:50052")
        assert manager.is_connected("typescript") is True

        manager.disconnect_runtime("typescript")
        assert manager.is_connected("typescript") is False

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_singleton_persists_across_instances(self, mock_client_class):
        """Test that connections persist across different RuntimeManager instances"""
        # Setup mock
        mock_client = Mock(spec=GrpcClient)
        mock_client_class.return_value = mock_client

        # Create first instance and connect
        manager1 = RuntimeManager()
        manager1.connect_runtime("typescript", "localhost:50052")

        # Create second instance
        manager2 = RuntimeManager()

        # Should have access to same connections
        assert manager2.is_connected("typescript") is True
        assert manager2.get_runtime("typescript") is mock_client

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_connect_runtime_with_different_addresses(self, mock_client_class):
        """Test connecting to different runtime types with different addresses"""
        # Setup mocks
        mock_ts_client = Mock(spec=GrpcClient)
        mock_py_client = Mock(spec=GrpcClient)
        mock_remote_client = Mock(spec=GrpcClient)
        mock_client_class.side_effect = [
            mock_ts_client,
            mock_py_client,
            mock_remote_client,
        ]

        # Connect to different addresses
        manager = RuntimeManager()
        ts_client = manager.connect_runtime("typescript", "localhost:50052")
        py_client = manager.connect_runtime("python", "localhost:50051")
        remote_client = manager.connect_runtime("remote-ts", "remote-host:9999")

        # Verify correct addresses used
        calls = mock_client_class.call_args_list
        assert calls[0][0][0] == "localhost:50052"
        assert calls[1][0][0] == "localhost:50051"
        assert calls[2][0][0] == "remote-host:9999"

        # Verify all connections exist
        assert len(manager.connections) == 3
        assert manager.is_connected("typescript")
        assert manager.is_connected("python")
        assert manager.is_connected("remote-ts")

    @patch("forthic.grpc.runtime_manager.GrpcClient")
    def test_disconnect_all_on_empty_manager(self, mock_client_class):
        """Test disconnect_all on empty manager doesn't error"""
        manager = RuntimeManager()
        manager.disconnect_all()  # Should not raise

        assert len(manager.connections) == 0
