"""
This module provides words that allow Forthic code to connect to remote runtimes
(like TypeScript, Ruby, etc.) and load their modules dynamically.

Usage example:
    # Connect to TypeScript runtime
    "typescript" "localhost:50052" CONNECT-RUNTIME

    # Load TypeScript modules
    ["array" "math"] USE-TS-MODULES

    # Load with prefix
    ["fs" "http"] "ts" USE-TS-MODULES-AS
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from forthic.decorators import DecoratedModule, ForthicDirectWord, register_module_doc
from forthic.decorators import ForthicWord as WordDecorator
from forthic.grpc.runtime_manager import RuntimeManager
from forthic.grpc.remote_module import RemoteModule

if TYPE_CHECKING:
    from forthic.interpreter import Interpreter


class RemoteRuntimeModule(DecoratedModule):
    """Module for connecting to and using remote Forthic runtimes

    Provides words to connect to remote runtimes (TypeScript, Ruby, etc.) and
    dynamically load their modules into the current interpreter.
    """

    def __init__(self):
        super().__init__("remote_runtime")
        self.runtime_manager = RuntimeManager()

        register_module_doc(
            RemoteRuntimeModule,
            """
Module for connecting to and using remote Forthic runtimes.

Enables bidirectional gRPC communication between Python and other runtimes
like TypeScript, allowing you to execute words from remote runtimes as if
they were local.

## Categories
- Connection: CONNECT-RUNTIME, DISCONNECT-RUNTIME, LIST-RUNTIMES
- TypeScript: USE-TS-MODULES, USE-TS-MODULES-AS

## Examples
# Connect to TypeScript runtime
"typescript" "localhost:50052" CONNECT-RUNTIME

# Load TypeScript array module
["array"] USE-TS-MODULES

# Use TypeScript words
[1 2 3] REVERSE  # Executes in TypeScript!

# Load with prefix for namespace isolation
["fs" "http"] "ts" USE-TS-MODULES-AS
"/path/to/file" ts.READ-FILE
            """,
        )

    @ForthicDirectWord("( name:str address:str -- )", "Connect to a remote runtime", "CONNECT-RUNTIME")
    async def CONNECT_RUNTIME(self, interp: Interpreter) -> None:
        """Connect to a remote Forthic runtime (e.g., TypeScript, Ruby)

        Establishes a gRPC connection to a remote runtime. The connection is
        reused for subsequent module loads.

        Args (from stack):
            address: gRPC address (e.g., "localhost:50052")
            name: Runtime name (e.g., "typescript", "ruby")

        Example:
            "typescript" "localhost:50052" CONNECT-RUNTIME
        """
        address = interp.stack_pop()
        name = interp.stack_pop()
        self.runtime_manager.connect_runtime(name, address)

    @ForthicDirectWord("( name:str -- )", "Disconnect from a remote runtime", "DISCONNECT-RUNTIME")
    async def DISCONNECT_RUNTIME(self, interp: Interpreter) -> None:
        """Disconnect from a remote runtime

        Closes the gRPC connection to the specified runtime.

        Args (from stack):
            name: Runtime name to disconnect

        Example:
            "typescript" DISCONNECT-RUNTIME
        """
        name = interp.stack_pop()
        self.runtime_manager.disconnect_runtime(name)

    @WordDecorator("( -- runtimes:list )", "List connected runtime names", "LIST-RUNTIMES")
    async def LIST_RUNTIMES(self) -> list[str]:
        """Get list of connected runtime names

        Returns:
            List of runtime names that are currently connected

        Example:
            LIST-RUNTIMES  # ["typescript", "ruby"]
        """
        return self.runtime_manager.list_connections()

    @ForthicDirectWord("( modules:list -- )", "Import TypeScript modules", "USE-TS-MODULES")
    async def USE_TS_MODULES(self, interp: Interpreter) -> None:
        """Load TypeScript modules from connected TypeScript runtime

        Discovers and loads modules from the TypeScript runtime, making their
        words available in the current interpreter without a prefix.

        Args (from stack):
            modules: List of module names to load

        Example:
            ["array" "math"] USE-TS-MODULES
            [1 2 3] REVERSE  # Uses TypeScript's REVERSE

        Raises:
            RuntimeError: If TypeScript runtime not connected
        """
        module_names = interp.stack_pop()
        await self._load_modules("typescript", module_names, prefix=None, interp=interp)

    @ForthicDirectWord("( modules:list prefix:str -- )", "Import TypeScript modules with prefix", "USE-TS-MODULES-AS")
    async def USE_TS_MODULES_AS(self, interp: Interpreter) -> None:
        """Load TypeScript modules with a prefix (e.g., 'ts.WORD')

        Similar to USE-TS-MODULES but adds a namespace prefix to all words.
        This helps avoid naming conflicts.

        Args (from stack):
            prefix: Namespace prefix for words
            modules: List of module names to load

        Example:
            ["fs" "http"] "ts" USE-TS-MODULES-AS
            "/path/to/file" ts.READ-FILE
            "https://example.com" ts.HTTP-GET

        Raises:
            RuntimeError: If TypeScript runtime not connected
        """
        prefix = interp.stack_pop()
        module_names = interp.stack_pop()
        await self._load_modules("typescript", module_names, prefix=prefix, interp=interp)

    async def _load_modules(
        self, runtime_name: str, module_names: list, prefix: str | None, interp: Interpreter
    ) -> None:
        """Helper to load modules from a runtime

        Args:
            runtime_name: Name of the runtime (e.g., "typescript")
            module_names: List of module names to load
            prefix: Optional namespace prefix for words
            interp: Interpreter instance

        Raises:
            RuntimeError: If runtime not connected or module not found
        """
        client = self.runtime_manager.get_runtime(runtime_name)
        if not client:
            raise RuntimeError(
                f"Runtime '{runtime_name}' not connected. "
                f"Use CONNECT-RUNTIME first."
            )

        for module_name in module_names:
            # Create and initialize remote module
            remote_module = RemoteModule(module_name, client, runtime_name)
            await remote_module.initialize()

            # Register with interpreter
            if prefix:
                # Register with prefix (e.g., "ts.array")
                prefixed_name = f"{prefix}.{module_name}"
                interp.register_module(remote_module, name=prefixed_name)
            else:
                # Register without prefix
                interp.register_module(remote_module)

            # Import the module to make its words available
            interp.use_modules([remote_module.name])
