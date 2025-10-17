"""
Phase 11.4: Python gRPC Client for Forthic
Connects to TypeScript runtime and executes remote words
Supports all basic Forthic types and module discovery
"""
import grpc
import os
from typing import Any

# Import generated proto files
from forthic.grpc import forthic_runtime_pb2
from forthic.grpc import forthic_runtime_pb2_grpc
from forthic.grpc.serializer import serialize_value, deserialize_value
from forthic.grpc.errors import RemoteRuntimeError, parse_error_info


class GrpcClient:
    """gRPC client for executing words in remote Forthic runtimes"""

    def __init__(self, address: str = "localhost:50052"):
        """
        Initialize the gRPC client

        Args:
            address: Address of the remote runtime (default: localhost:50052 for TypeScript)
        """
        self.address = address

        # Create gRPC channel
        self.channel = grpc.insecure_channel(address)

        # Create client stub
        self.stub = forthic_runtime_pb2_grpc.ForthicRuntimeStub(self.channel)

    async def execute_word(self, word_name: str, stack: list[Any]) -> list[Any]:
        """
        Execute a word in the remote runtime

        Args:
            word_name: Name of the word to execute
            stack: Current stack values

        Returns:
            Result stack after execution

        Raises:
            RemoteRuntimeError: If the remote runtime raises an error
        """
        # Serialize the stack
        serialized_stack = [serialize_value(value) for value in stack]

        # Create request
        request = forthic_runtime_pb2.ExecuteWordRequest(
            word_name=word_name, stack=serialized_stack
        )

        # Execute RPC call
        response = self.stub.ExecuteWord(request)

        # Check for errors
        if response.HasField("error"):
            error_info = parse_error_info(response.error)
            raise RemoteRuntimeError(error_info)

        # Deserialize result stack
        result_stack = [deserialize_value(value) for value in response.result_stack]
        return result_stack

    async def execute_sequence(
        self, word_names: list[str], stack: list[Any]
    ) -> list[Any]:
        """
        Execute a sequence of words in one remote call (batched execution)

        Args:
            word_names: Array of word names to execute in order
            stack: Current stack values

        Returns:
            Result stack after executing all words

        Raises:
            RemoteRuntimeError: If the remote runtime raises an error
        """
        # Serialize the stack
        serialized_stack = [serialize_value(value) for value in stack]

        # Create request
        request = forthic_runtime_pb2.ExecuteSequenceRequest(
            word_names=word_names, stack=serialized_stack
        )

        # Execute RPC call
        response = self.stub.ExecuteSequence(request)

        # Check for errors
        if response.HasField("error"):
            error_info = parse_error_info(response.error)
            raise RemoteRuntimeError(error_info)

        # Deserialize result stack
        result_stack = [deserialize_value(value) for value in response.result_stack]
        return result_stack

    async def list_modules(self) -> list[dict[str, Any]]:
        """
        List available runtime-specific modules

        Returns:
            Array of module summaries with name, description, word_count, runtime_specific
        """
        request = forthic_runtime_pb2.ListModulesRequest()
        response = self.stub.ListModules(request)

        modules = []
        for module_summary in response.modules:
            modules.append(
                {
                    "name": module_summary.name,
                    "description": module_summary.description,
                    "word_count": module_summary.word_count,
                    "runtime_specific": module_summary.runtime_specific,
                }
            )

        return modules

    async def get_module_info(self, module_name: str) -> dict[str, Any]:
        """
        Get detailed information about a specific module

        Args:
            module_name: Name of the module

        Returns:
            Module details including word list with stack effects and descriptions
        """
        request = forthic_runtime_pb2.GetModuleInfoRequest(module_name=module_name)
        response = self.stub.GetModuleInfo(request)

        words = []
        for word_info in response.words:
            words.append(
                {
                    "name": word_info.name,
                    "stack_effect": word_info.stack_effect,
                    "description": word_info.description,
                }
            )

        return {
            "name": response.name,
            "description": response.description,
            "words": words,
        }

    def close(self) -> None:
        """Close the gRPC channel"""
        self.channel.close()
