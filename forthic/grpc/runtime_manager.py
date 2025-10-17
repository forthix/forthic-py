"""
Phase 11.7: Python Runtime Manager
Singleton for managing gRPC connections to remote runtimes
Reuses connections and provides centralized connection management
"""
from typing import Optional
from forthic.grpc.client import GrpcClient


class RuntimeManager:
    """Singleton for managing gRPC connections to remote runtimes"""

    _instance: Optional["RuntimeManager"] = None

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connections = {}
        return cls._instance

    def connect_runtime(self, name: str, address: str) -> GrpcClient:
        """
        Connect to a runtime or return existing connection

        Args:
            name: Unique name for this runtime (e.g., 'typescript', 'python')
            address: gRPC address (e.g., 'localhost:50052')

        Returns:
            GrpcClient instance for the runtime
        """
        if name not in self.connections:
            client = GrpcClient(address)
            self.connections[name] = client
        return self.connections[name]

    def get_runtime(self, name: str) -> Optional[GrpcClient]:
        """
        Get existing runtime connection

        Args:
            name: Name of the runtime

        Returns:
            GrpcClient instance if connected, None otherwise
        """
        return self.connections.get(name)

    def disconnect_runtime(self, name: str) -> None:
        """
        Disconnect from a runtime

        Args:
            name: Name of the runtime to disconnect
        """
        if name in self.connections:
            self.connections[name].close()
            del self.connections[name]

    def disconnect_all(self) -> None:
        """Disconnect from all runtimes"""
        for client in self.connections.values():
            client.close()
        self.connections.clear()

    def list_connections(self) -> list[str]:
        """
        Get list of connected runtime names

        Returns:
            List of runtime names that are currently connected
        """
        return list(self.connections.keys())

    def is_connected(self, name: str) -> bool:
        """
        Check if a runtime is connected

        Args:
            name: Name of the runtime

        Returns:
            True if connected, False otherwise
        """
        return name in self.connections
