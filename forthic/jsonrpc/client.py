"""JSON-RPC 2.0 client for Forthic.

Speaks the same async surface as forthic.grpc.client.GrpcClient
(execute_word / execute_sequence / list_modules / get_module_info) so it
can be used interchangeably by RemoteWord / RemoteModule / RuntimeManager.

Uses urllib.request from the standard library — no extra dependencies. The
synchronous HTTP call is wrapped in asyncio.to_thread so the public API
matches the async gRPC client.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import urllib.error
import urllib.request
from typing import Any

from forthic.jsonrpc.errors import (
    JsonRpcErrorCode,
    RemoteRuntimeError,
    parse_error_info_dict,
)
from forthic.jsonrpc.serializer import deserialize_value, serialize_value


class JsonRpcClient:
    """JSON-RPC 2.0 client for a remote Forthic runtime."""

    def __init__(
        self,
        address: str = "localhost:8765",
        *,
        path: str = "/rpc",
        timeout: float | None = None,
    ) -> None:
        if address.startswith(("http://", "https://")):
            self.endpoint = address
        else:
            self.endpoint = f"http://{address}{path}"
        self.timeout = timeout
        self._ids = itertools.count(1)

    async def execute_word(self, word_name: str, stack: list[Any]) -> list[Any]:
        result = await self._call(
            "executeWord",
            {
                "word_name": word_name,
                "stack": [serialize_value(v) for v in stack],
            },
        )
        return [deserialize_value(v) for v in result.get("result_stack", [])]

    async def execute_sequence(
        self, word_names: list[str], stack: list[Any]
    ) -> list[Any]:
        result = await self._call(
            "executeSequence",
            {
                "word_names": list(word_names),
                "stack": [serialize_value(v) for v in stack],
            },
        )
        return [deserialize_value(v) for v in result.get("result_stack", [])]

    async def list_modules(self) -> list[dict[str, Any]]:
        result = await self._call("listModules", {})
        return list(result.get("modules", []))

    async def get_module_info(self, module_name: str) -> dict[str, Any]:
        return await self._call("getModuleInfo", {"module_name": module_name})

    def close(self) -> None:
        """No-op; HTTP connections are not pooled."""

    # ---- internals ----

    async def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._call_sync, method, params)

    def _call_sync(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = next(self._ids)
        body = json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        ).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Connection": "close",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp is not None else ""
            if not raw:
                raise RuntimeError(
                    f"JSON-RPC HTTP {exc.code}: {exc.reason}"
                ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"JSON-RPC transport error: {exc.reason}") from exc

        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON-RPC parse error: {exc.msg}") from exc

        if "error" in envelope and envelope["error"] is not None:
            err = envelope["error"]
            code = err.get("code")
            message = err.get("message", "")
            data = err.get("data")
            if (
                code == JsonRpcErrorCode.RUNTIME_ERROR
                and isinstance(data, dict)
            ):
                raise RemoteRuntimeError(parse_error_info_dict(data))
            raise RuntimeError(f"JSON-RPC error {code}: {message}")

        return envelope.get("result") or {}
