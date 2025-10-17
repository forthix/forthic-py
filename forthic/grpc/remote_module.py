"""
Phase 11.6: RemoteModule - Module that wraps TypeScript words

RemoteModule is a proxy module that discovers and wraps words from a remote
runtime (e.g., TypeScript). Each word becomes a RemoteWord that delegates
execution via gRPC.

Usage:
    client = GrpcClient("localhost:50052")
    module = RemoteModule("array", client, "typescript")
    await module.initialize()  # Discovers words from remote runtime
    interp.register_module(module)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from forthic.module import Module
from forthic.grpc.remote_word import RemoteWord

if TYPE_CHECKING:
    from forthic.interpreter import Interpreter
    from forthic.grpc.client import GrpcClient


class RemoteModule(Module):
    """Module that wraps words from a remote runtime

    RemoteModule discovers words from a remote Forthic runtime (like TypeScript)
    and creates RemoteWord proxies for each. The module must be initialized
    before use to fetch word metadata from the remote runtime.

    The module acts as a transparent proxy - when a word is executed, it
    delegates to the remote runtime via gRPC.
    """

    def __init__(
        self, module_name: str, client: GrpcClient, runtime_name: str = "remote"
    ):
        """
        Initialize RemoteModule

        Args:
            module_name: Name of the module to wrap (e.g., "array", "math")
            client: gRPC client connected to remote runtime
            runtime_name: Name of the runtime (e.g., "typescript", "ruby")
        """
        super().__init__(module_name)
        self.client = client
        self.runtime_name = runtime_name
        self.initialized = False
        self.module_info: dict[str, Any] | None = None

    async def initialize(self) -> None:
        """Discover words from remote runtime and create proxies

        Fetches module metadata from the remote runtime and creates a RemoteWord
        for each discovered word. Must be called before the module can be used.

        Raises:
            RuntimeError: If module not found in remote runtime or gRPC fails
        """
        if self.initialized:
            return

        # Fetch module info from remote runtime
        self.module_info = await self.client.get_module_info(self.name)

        # Create RemoteWord for each discovered word
        for word_info in self.module_info["words"]:
            remote_word = RemoteWord(
                word_info["name"],
                self.client,
                self.runtime_name,
                self.name,
                word_info["stack_effect"],
                word_info["description"],
            )
            self.add_exportable_word(remote_word)

        self.initialized = True

    def set_interp(self, interp: Interpreter) -> None:
        """Set interpreter for this module

        Overrides Module.set_interp() to enforce initialization requirement.

        Args:
            interp: Interpreter instance

        Raises:
            RuntimeError: If module not initialized before use
        """
        if not self.initialized:
            raise RuntimeError(
                f"RemoteModule '{self.name}' must be initialized before use. "
                f"Call await module.initialize() first."
            )
        super().set_interp(interp)

    def get_runtime_name(self) -> str:
        """Get the runtime name for debugging/introspection"""
        return self.runtime_name

    def get_module_info(self) -> dict[str, Any] | None:
        """Get the cached module info from remote runtime"""
        return self.module_info
