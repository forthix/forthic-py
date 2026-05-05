"""JSON-RPC 2.0 server for Forthic (Python runtime).

Exposes the same four methods as the gRPC server (executeWord,
executeSequence, listModules, getModuleInfo) over HTTP POST /rpc.
Uses only Python's standard library (http.server, socketserver) — no
external HTTP framework required.

executeSequence is a single JSON-RPC call carrying an array of words; it
is NOT a JSON-RPC batch (which would create N independent interpreters
and lose stack continuity). Batch envelopes are rejected with -32600.
"""

from __future__ import annotations

import asyncio
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from forthic.interpreter import StandardInterpreter
from forthic.jsonrpc.errors import JsonRpcErrorCode
from forthic.jsonrpc.serializer import deserialize_value, serialize_value


class _ForthicJsonRpcServicer:
    """Holds the runtime modules and dispatches the four RPC methods."""

    def __init__(self, modules_config: str | None = None) -> None:
        self.runtime_modules: dict[str, Any] = {}

        if modules_config:
            from forthic.grpc.module_loader import (
                ModuleLoadError,
                load_modules_from_config,
            )

            try:
                loaded = load_modules_from_config(modules_config)
                for name, mod in loaded.items():
                    self.runtime_modules[name] = mod
            except ModuleLoadError:
                raise
        else:
            try:
                from forthic.modules.pandas_module import PandasModule

                self.runtime_modules["pandas"] = PandasModule()
            except ImportError:
                pass

    # ---- public method handlers ----

    def execute_word(self, params: dict[str, Any]) -> dict[str, Any]:
        word_name = params.get("word_name")
        if not isinstance(word_name, str):
            raise _InvalidParams('executeWord requires string "word_name"')
        stack_param = params.get("stack")
        if not isinstance(stack_param, list):
            raise _InvalidParams('executeWord requires array "stack"')
        stack = [deserialize_value(sv) for sv in stack_param]
        result_stack = asyncio.run(self._execute_with_stack(word_name, stack))
        return {"result_stack": [serialize_value(v) for v in result_stack]}

    def execute_sequence(self, params: dict[str, Any]) -> dict[str, Any]:
        word_names = params.get("word_names")
        if not isinstance(word_names, list) or not all(
            isinstance(w, str) for w in word_names
        ):
            raise _InvalidParams('executeSequence requires string[] "word_names"')
        stack_param = params.get("stack")
        if not isinstance(stack_param, list):
            raise _InvalidParams('executeSequence requires array "stack"')
        stack = [deserialize_value(sv) for sv in stack_param]
        result_stack = asyncio.run(
            self._execute_sequence_with_stack(word_names, stack)
        )
        return {"result_stack": [serialize_value(v) for v in result_stack]}

    def list_modules(self, _params: dict[str, Any]) -> dict[str, Any]:
        modules = []
        for name, mod in self.runtime_modules.items():
            modules.append(
                {
                    "name": name,
                    "description": f"Python-specific {name} module",
                    "word_count": self._module_word_count(mod),
                    "runtime_specific": True,
                }
            )
        return {"modules": modules}

    def get_module_info(self, params: dict[str, Any]) -> dict[str, Any]:
        module_name = params.get("module_name")
        if not isinstance(module_name, str):
            raise _InvalidParams('getModuleInfo requires string "module_name"')
        if module_name not in self.runtime_modules:
            raise _MethodError(
                JsonRpcErrorCode.MODULE_NOT_FOUND,
                f"Module '{module_name}' not found",
            )
        mod = self.runtime_modules[module_name]
        words: list[dict[str, Any]] = []
        if hasattr(mod, "get_word_docs"):
            for doc in mod.get_word_docs():
                words.append(
                    {
                        "name": doc["name"],
                        "stack_effect": doc["stackEffect"],
                        "description": doc["description"],
                    }
                )
        else:
            for attr_name in dir(mod):
                if attr_name.isupper() and not attr_name.startswith("_"):
                    words.append(
                        {
                            "name": attr_name,
                            "stack_effect": "( -- )",
                            "description": f"{attr_name} word from {module_name} module",
                        }
                    )
        return {
            "name": module_name,
            "description": f"Python-specific {module_name} module",
            "words": words,
        }

    # ---- error info ----

    def build_runtime_error(
        self,
        exception: Exception,
        word_name: str | None = None,
        context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        stack_trace = [line.rstrip() for line in tb_lines]
        error_type = type(exception).__name__

        error_context: dict[str, str] = {}
        if word_name:
            error_context["word_name"] = word_name
        if context:
            error_context.update({k: str(v) for k, v in context.items()})

        module_name: str | None = None
        word_location: str | None = None
        for frame_summary in traceback.extract_tb(exception.__traceback__):
            filename = frame_summary.filename
            if "forthic/modules/" in filename:
                module_name = (
                    filename.split("forthic/modules/")[-1]
                    .split(".")[0]
                    .replace("_module", "")
                )
                word_location = f"{filename}:{frame_summary.lineno}"
                break
            if "forthic/jsonrpc/" in filename or "forthic/grpc/" in filename:
                word_location = f"{filename}:{frame_summary.lineno}"

        info: dict[str, Any] = {
            "message": str(exception),
            "runtime": "python",
            "stack_trace": stack_trace,
            "error_type": error_type,
            "context": error_context,
        }
        if word_location:
            info["word_location"] = word_location
        if module_name:
            info["module_name"] = module_name
        return info

    # ---- internals ----

    async def _execute_with_stack(self, word_name: str, stack: list) -> list:
        interp = StandardInterpreter()
        for mod in self.runtime_modules.values():
            interp.register_module(mod)
        if self.runtime_modules:
            interp.use_modules(list(self.runtime_modules.keys()))
        for item in stack:
            interp.stack_push(item)
        await interp.run(word_name)
        return interp.get_stack().get_items()

    async def _execute_sequence_with_stack(
        self, word_names: list[str], stack: list
    ) -> list:
        interp = StandardInterpreter()
        for mod in self.runtime_modules.values():
            interp.register_module(mod)
        if self.runtime_modules:
            interp.use_modules(list(self.runtime_modules.keys()))
        for item in stack:
            interp.stack_push(item)
        for word_name in word_names:
            await interp.run(word_name)
        return interp.get_stack().get_items()

    @staticmethod
    def _module_word_count(mod: Any) -> int:
        if hasattr(mod, "get_word_docs"):
            return len(mod.get_word_docs())
        return len(
            [w for w in dir(mod) if w.isupper() and not w.startswith("_")]
        )


class _MethodError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


class _InvalidParams(_MethodError):
    def __init__(self, message: str) -> None:
        super().__init__(JsonRpcErrorCode.INVALID_PARAMS, message)


def _make_handler(servicer: _ForthicJsonRpcServicer) -> type[BaseHTTPRequestHandler]:
    class _JsonRpcHandler(BaseHTTPRequestHandler):
        # Quiet logging; keep prints elsewhere consistent with the gRPC server.
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
            if self.path not in ("/rpc", "/"):
                self._send_text(404, "Not Found")
                return
            ctype = self.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                self._send_text(415, "Unsupported Media Type")
                return

            length_header = self.headers.get("Content-Length")
            try:
                length = int(length_header) if length_header is not None else 0
            except ValueError:
                length = 0

            try:
                raw = self.rfile.read(length).decode("utf-8") if length else ""
            except Exception as exc:
                self._send_jsonrpc(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": JsonRpcErrorCode.PARSE_ERROR,
                            "message": f"Failed to read body: {exc}",
                        },
                    }
                )
                return

            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError as exc:
                self._send_jsonrpc(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": JsonRpcErrorCode.PARSE_ERROR,
                            "message": f"Parse error: {exc.msg}",
                        },
                    }
                )
                return

            if isinstance(parsed, list):
                self._send_jsonrpc(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": JsonRpcErrorCode.INVALID_REQUEST,
                            "message": "Batch requests are not supported",
                        },
                    }
                )
                return

            if (
                not isinstance(parsed, dict)
                or parsed.get("jsonrpc") != "2.0"
                or not isinstance(parsed.get("method"), str)
                or "id" not in parsed
            ):
                rid = parsed.get("id") if isinstance(parsed, dict) else None
                self._send_jsonrpc(
                    {
                        "jsonrpc": "2.0",
                        "id": rid,
                        "error": {
                            "code": JsonRpcErrorCode.INVALID_REQUEST,
                            "message": "Invalid JSON-RPC 2.0 request",
                        },
                    }
                )
                return

            response = self._dispatch(parsed)
            self._send_jsonrpc(response)

        def do_GET(self) -> None:  # noqa: N802
            self._send_text(405, "Method Not Allowed", extra_headers={"Allow": "POST"})

        def do_PUT(self) -> None:  # noqa: N802
            self._send_text(405, "Method Not Allowed", extra_headers={"Allow": "POST"})

        def do_DELETE(self) -> None:  # noqa: N802
            self._send_text(405, "Method Not Allowed", extra_headers={"Allow": "POST"})

        # ---- helpers ----

        def _dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
            rid = request.get("id")
            method = request["method"]
            params = request.get("params") or {}
            if not isinstance(params, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {
                        "code": JsonRpcErrorCode.INVALID_PARAMS,
                        "message": "params must be an object",
                    },
                }

            try:
                if method == "executeWord":
                    try:
                        result = servicer.execute_word(params)
                    except _MethodError:
                        raise
                    except Exception as exc:
                        data = servicer.build_runtime_error(
                            exc, word_name=params.get("word_name")
                        )
                        raise _MethodError(
                            JsonRpcErrorCode.RUNTIME_ERROR, data["message"], data
                        ) from exc
                elif method == "executeSequence":
                    try:
                        result = servicer.execute_sequence(params)
                    except _MethodError:
                        raise
                    except Exception as exc:
                        seq_ctx: dict[str, str] = {}
                        if isinstance(params.get("word_names"), list):
                            seq_ctx["word_sequence"] = ", ".join(
                                str(w) for w in params["word_names"]
                            )
                        data = servicer.build_runtime_error(exc, context=seq_ctx)
                        raise _MethodError(
                            JsonRpcErrorCode.RUNTIME_ERROR, data["message"], data
                        ) from exc
                elif method == "listModules":
                    result = servicer.list_modules(params)
                elif method == "getModuleInfo":
                    result = servicer.get_module_info(params)
                else:
                    raise _MethodError(
                        JsonRpcErrorCode.METHOD_NOT_FOUND,
                        f"Method not found: {method}",
                    )
            except _MethodError as exc:
                err: dict[str, Any] = {"code": exc.code, "message": str(exc)}
                if exc.data is not None:
                    err["data"] = exc.data
                return {"jsonrpc": "2.0", "id": rid, "error": err}
            except Exception as exc:  # pragma: no cover - safety net
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {
                        "code": JsonRpcErrorCode.INTERNAL_ERROR,
                        "message": str(exc),
                    },
                }

            return {"jsonrpc": "2.0", "id": rid, "result": result}

        def _send_jsonrpc(self, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_text(
            self,
            status: int,
            text: str,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

    return _JsonRpcHandler


class JsonRpcHttpServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that exposes the underlying servicer for tests."""

    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        servicer: _ForthicJsonRpcServicer,
    ) -> None:
        super().__init__(server_address, _make_handler(servicer))
        self.servicer = servicer


def serve(
    port: int = 8765,
    host: str = "0.0.0.0",
    modules_config: str | None = None,
    *,
    blocking: bool = True,
) -> JsonRpcHttpServer:
    """Start the JSON-RPC server.

    Args:
        port: TCP port to listen on. Defaults to 8765.
        host: Bind address. Defaults to all interfaces.
        modules_config: Optional path to a YAML module config (same format
            as the gRPC server's --modules-config).
        blocking: If True (default), call serve_forever() and never return.
            If False, start a background thread and return the server so
            callers (e.g. tests) can shut it down.

    Returns:
        The JsonRpcHttpServer instance (only meaningful when blocking=False).
    """
    servicer = _ForthicJsonRpcServicer(modules_config=modules_config)
    server = JsonRpcHttpServer((host, port), servicer)

    loaded = list(servicer.runtime_modules.keys())
    if loaded:
        print(f"  - Available runtime modules: {', '.join(loaded)}")
    else:
        print("  - No runtime-specific modules loaded")
    print(f"Forthic Python JSON-RPC server listening on {host}:{port}")

    if blocking:
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return server

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main() -> None:
    """CLI entry point for the JSON-RPC server."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Forthic Python JSON-RPC server")
    parser.add_argument("--port", type=int, default=8765, help="Port (default 8765)")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Bind address"
    )
    parser.add_argument(
        "--modules-config",
        type=str,
        default=None,
        help="Path to modules YAML config",
    )
    args = parser.parse_args()

    modules_config = args.modules_config or os.getenv("FORTHIC_MODULES_CONFIG")
    serve(port=args.port, host=args.host, modules_config=modules_config)


if __name__ == "__main__":
    main()
