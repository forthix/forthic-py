"""JSON-RPC error codes and helpers.

Reuses RemoteRuntimeError / RemoteErrorInfo from forthic.grpc.errors so a
caller catching one exception class works against either transport.
"""

from __future__ import annotations

from typing import Any

from forthic.grpc.errors import RemoteErrorInfo, RemoteRuntimeError


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
