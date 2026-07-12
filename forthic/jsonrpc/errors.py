"""JSON-RPC error codes and helpers.

RemoteErrorInfo / RemoteRuntimeError preserve message, stack trace, and
context from a remote Forthic runtime across the wire boundary.
"""

from __future__ import annotations

from typing import Any


class RemoteErrorInfo:
    """Error information from a remote runtime"""

    def __init__(
        self,
        message: str,
        runtime: str,
        stack_trace: list[str],
        error_type: str,
        word_location: str | None = None,
        module_name: str | None = None,
        context: dict[str, str] | None = None,
    ):
        self.message = message
        self.runtime = runtime
        self.stack_trace = stack_trace
        self.error_type = error_type
        self.word_location = word_location
        self.module_name = module_name
        self.context = context or {}


class RemoteRuntimeError(Exception):
    """
    Custom error class for errors that occur in remote runtimes
    Preserves stack trace and context from the remote runtime
    """

    def __init__(self, error_info: RemoteErrorInfo):
        # Build a rich error message
        message = f"Error in {error_info.runtime} runtime: {error_info.message}"

        if error_info.module_name:
            message += f"\n  Module: {error_info.module_name}"

        if error_info.word_location:
            message += f"\n  Location: {error_info.word_location}"

        if error_info.context:
            message += "\n  Context:"
            for key, value in error_info.context.items():
                message += f"\n    {key}: {value}"

        super().__init__(message)

        self.runtime = error_info.runtime
        self.remote_stack_trace = error_info.stack_trace
        self.error_type = error_info.error_type
        self.word_location = error_info.word_location
        self.module_name = error_info.module_name
        self.context = error_info.context

    def get_full_stack_trace(self) -> str:
        """Get the full stack trace including both local and remote context"""
        import traceback

        result = f"{self.__class__.__name__}: {str(self)}\n"

        # Add local Python stack
        result += "\nLocal stack (Python):\n"
        result += "".join(traceback.format_tb(self.__traceback__))

        # Add remote stack trace
        if self.remote_stack_trace:
            result += f"\n\nRemote stack ({self.runtime}):\n"
            result += "\n".join(self.remote_stack_trace)

        return result

    def get_error_report(self) -> str:
        """Get a formatted error report with all available context"""
        report = "=" * 80 + "\n"
        report += "REMOTE RUNTIME ERROR\n"
        report += "=" * 80 + "\n\n"

        report += f"Runtime: {self.runtime}\n"
        report += f"Error Type: {self.error_type}\n"
        report += f"Message: {self.args[0] if self.args else 'Unknown error'}\n"

        if self.module_name:
            report += f"Module: {self.module_name}\n"

        if self.word_location:
            report += f"Location: {self.word_location}\n"

        if self.context:
            report += "\nContext:\n"
            for key, value in self.context.items():
                report += f"  {key}: {value}\n"

        report += "\n" + "-" * 80 + "\n"
        report += "Stack Trace:\n"
        report += "-" * 80 + "\n"

        if self.remote_stack_trace:
            report += "\n".join(self.remote_stack_trace)

        report += "\n" + "=" * 80 + "\n"

        return report


class JsonRpcErrorCode:
    """Standard JSON-RPC 2.0 codes plus our server-defined codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Server-defined (-32000 to -32099)
    RUNTIME_ERROR = -32000  # Forthic runtime error; data carries ErrorInfo
    MODULE_NOT_FOUND = -32001


def parse_error_info_dict(data: dict[str, Any]) -> RemoteErrorInfo:
    """Build a RemoteErrorInfo from the JSON-RPC error.data payload."""
    return RemoteErrorInfo(
        message=data.get("message") or "Unknown error",
        runtime=data.get("runtime") or "unknown",
        stack_trace=list(data.get("stack_trace") or []),
        error_type=data.get("error_type") or "Error",
        word_location=data.get("word_location") or None,
        module_name=data.get("module_name") or None,
        context=dict(data.get("context") or {}),
    )


__all__ = [
    "JsonRpcErrorCode",
    "RemoteErrorInfo",
    "RemoteRuntimeError",
    "parse_error_info_dict",
]
