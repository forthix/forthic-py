"""
RemoteWord is a proxy word that delegates execution to a remote runtime
(e.g., TypeScript). When executed:
1. Captures current interpreter stack
2. Sends word name + stack to remote runtime via gRPC
3. Replaces local stack with result stack from remote execution

This allows seamless integration of remote runtime words into the local
Python interpreter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from forthic.module import Word

if TYPE_CHECKING:
    from forthic.interpreter import Interpreter
    from forthic.grpc.client import GrpcClient


class RuntimeInfo:
    """Runtime execution information for a word"""

    def __init__(
        self,
        runtime: str,
        is_remote: bool,
        is_standard: bool,
        available_in: list[str],
    ):
        self.runtime = runtime
        self.is_remote = is_remote
        self.is_standard = is_standard
        self.available_in = available_in


class RemoteWord(Word):
    """Proxy word that delegates execution to a remote runtime

    When executed:
    1. Captures current interpreter stack
    2. Sends word name + stack to remote runtime via gRPC
    3. Replaces local stack with result stack from remote execution

    This allows seamless integration of remote runtime words (like TypeScript stdlib)
    into the local Python interpreter.
    """

    def __init__(
        self,
        name: str,
        client: GrpcClient,
        runtime_name: str,
        module_name: str,
        stack_effect: str = "( -- )",
        description: str = "",
    ):
        """
        Initialize RemoteWord

        Args:
            name: Word name (e.g., "REVERSE")
            client: gRPC client connected to remote runtime
            runtime_name: Name of remote runtime (e.g., "typescript")
            module_name: Module name (e.g., "array")
            stack_effect: Stack notation (e.g., "( array -- array )")
            description: Human-readable description
        """
        super().__init__(name)
        self.client = client
        self.runtime_name = runtime_name
        self.module_name = module_name
        self.stack_effect = stack_effect
        self.description = description

    async def execute(self, interp: Interpreter) -> None:
        """Execute word in remote runtime

        Captures entire stack, sends to remote runtime, and replaces stack with result.
        This is inefficient but correct - future phases may optimize to only send needed items.
        """
        try:
            # Capture current stack state
            stack = interp.get_stack()
            stack_items = stack.get_items()

            # Execute word in remote runtime
            # The server has already imported the module, so just send the word name
            result_stack = await self.client.execute_word(self.name, stack_items)

            # Clear local stack and replace with result
            while len(interp.get_stack()) > 0:
                interp.stack_pop()

            # Push all result items
            for item in result_stack:
                interp.stack_push(item)
        except Exception as error:
            raise RuntimeError(
                f"Error executing remote word {self.module_name}.{self.name} "
                f"in {self.runtime_name} runtime: {error}"
            ) from error

    def get_runtime_name(self) -> str:
        """Get runtime name for debugging/introspection"""
        return self.runtime_name

    def get_module_name(self) -> str:
        """Get module name for debugging/introspection"""
        return self.module_name

    def get_runtime_info(self) -> dict[str, Any]:
        """Get runtime execution information

        RemoteWords are runtime-specific and can only execute in their designated runtime
        """
        return {
            "runtime": self.runtime_name,
            "is_remote": True,
            "is_standard": False,
            "available_in": [self.runtime_name],
        }
