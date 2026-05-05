"""JSON-RPC 2.0 transport for Forthic.

Mirrors forthic.grpc surface (executeWord / executeSequence / listModules /
getModuleInfo) over plain HTTP + JSON, no protobuf required. Wire format
matches the TypeScript JSON-RPC server in forthic-ts so the two are
interoperable.
"""

from forthic.jsonrpc.client import JsonRpcClient
from forthic.jsonrpc.errors import JsonRpcErrorCode
from forthic.jsonrpc.server import serve

__all__ = ["JsonRpcClient", "JsonRpcErrorCode", "serve"]
