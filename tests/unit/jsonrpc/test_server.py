"""Wire-format tests for the JSON-RPC server.

Boots the real HTTP server in a background thread on a random port and
hits it with raw urllib so we exercise the on-the-wire envelope (not the
client wrapper).
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

import pytest

from forthic.jsonrpc.errors import JsonRpcErrorCode
from forthic.jsonrpc.serializer import deserialize_value, serialize_value
from forthic.jsonrpc.server import serve


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server():
    port = _free_port()
    srv = serve(port=port, host="127.0.0.1", blocking=False)
    try:
        yield port
    finally:
        srv.shutdown()
        srv.server_close()


def _post_raw(
    port: int, body: str, content_type: str = "application/json", method: str = "POST"
) -> tuple[int, str]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/rpc",
        data=body.encode("utf-8") if body else None,
        headers={"Content-Type": content_type, "Connection": "close"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8") if exc.fp else ""


_next_id = 0


def _rpc(port: int, method: str, params: Any) -> dict[str, Any]:
    global _next_id
    _next_id += 1
    body = json.dumps(
        {"jsonrpc": "2.0", "id": _next_id, "method": method, "params": params}
    )
    status, text = _post_raw(port, body)
    assert status == 200, f"unexpected HTTP status {status}: {text}"
    return json.loads(text)


class TestServerFoundation:
    def test_list_modules_returns_array(self, server):
        env = _rpc(server, "listModules", {})
        assert env["jsonrpc"] == "2.0"
        assert "result" in env
        assert isinstance(env["result"]["modules"], list)

    def test_non_post_returns_405(self, server):
        status, _ = _post_raw(server, "", method="GET")
        assert status == 405

    def test_non_json_content_type_returns_415(self, server):
        status, _ = _post_raw(server, "hello", content_type="text/plain")
        assert status == 415

    def test_parse_error_returns_minus_32700(self, server):
        status, text = _post_raw(server, "{not json")
        assert status == 200
        env = json.loads(text)
        assert env["error"]["code"] == JsonRpcErrorCode.PARSE_ERROR

    def test_batch_envelope_rejected(self, server):
        status, text = _post_raw(
            server, '[{"jsonrpc":"2.0","id":1,"method":"listModules"}]'
        )
        env = json.loads(text)
        assert env["error"]["code"] == JsonRpcErrorCode.INVALID_REQUEST

    def test_unknown_method_returns_minus_32601(self, server):
        env = _rpc(server, "bogus", {})
        assert env["error"]["code"] == JsonRpcErrorCode.METHOD_NOT_FOUND

    def test_invalid_params_returns_minus_32602(self, server):
        env = _rpc(server, "executeWord", {"word_name": 42, "stack": []})
        assert env["error"]["code"] == JsonRpcErrorCode.INVALID_PARAMS


class TestStackExecution:
    def test_dup(self, server):
        env = _rpc(
            server,
            "executeWord",
            {"word_name": "DUP", "stack": [serialize_value(42)]},
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [42, 42]

    def test_swap(self, server):
        env = _rpc(
            server,
            "executeWord",
            {
                "word_name": "SWAP",
                "stack": [serialize_value(1), serialize_value(2)],
            },
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [2, 1]

    def test_plus(self, server):
        env = _rpc(
            server,
            "executeWord",
            {
                "word_name": "+",
                "stack": [serialize_value(10), serialize_value(32)],
            },
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [42]

    def test_reverse(self, server):
        env = _rpc(
            server,
            "executeWord",
            {"word_name": "REVERSE", "stack": [serialize_value([1, 2, 3])]},
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [[3, 2, 1]]


class TestSequenceExecution:
    def test_dup_then_plus(self, server):
        env = _rpc(
            server,
            "executeSequence",
            {"word_names": ["DUP", "+"], "stack": [serialize_value(21)]},
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [42]

    def test_empty_sequence_returns_original_stack(self, server):
        env = _rpc(
            server,
            "executeSequence",
            {
                "word_names": [],
                "stack": [serialize_value(1), serialize_value(2)],
            },
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [1, 2]


class TestErrorHandling:
    def test_unknown_word_returns_minus_32000_with_error_info(self, server):
        env = _rpc(
            server,
            "executeWord",
            {"word_name": "NONEXISTENT_WORD", "stack": []},
        )
        err = env["error"]
        assert err["code"] == JsonRpcErrorCode.RUNTIME_ERROR
        assert err["data"]["runtime"] == "python"
        assert err["data"]["error_type"]
        assert err["data"]["context"]["word_name"] == "NONEXISTENT_WORD"

    def test_sequence_error_carries_word_sequence_context(self, server):
        env = _rpc(
            server,
            "executeSequence",
            {
                "word_names": ["DUP", "INVALID_WORD", "+"],
                "stack": [serialize_value(42)],
            },
        )
        err = env["error"]
        assert err["code"] == JsonRpcErrorCode.RUNTIME_ERROR
        assert "INVALID_WORD" in err["data"]["context"]["word_sequence"]

    def test_unknown_module_returns_minus_32001(self, server):
        env = _rpc(server, "getModuleInfo", {"module_name": "no_such_module"})
        assert env["error"]["code"] == JsonRpcErrorCode.MODULE_NOT_FOUND


class TestIsolation:
    def test_requests_do_not_share_state(self, server):
        e1 = _rpc(
            server,
            "executeWord",
            {"word_name": "DUP", "stack": [serialize_value(100)]},
        )
        e2 = _rpc(
            server,
            "executeWord",
            {"word_name": "DUP", "stack": [serialize_value(200)]},
        )
        s1 = [deserialize_value(v) for v in e1["result"]["result_stack"]]
        s2 = [deserialize_value(v) for v in e2["result"]["result_stack"]]
        assert s1 == [100, 100]
        assert s2 == [200, 200]


class TestComplexTypes:
    def test_records_arrays_strings_ints_round_trip(self, server):
        complex_stack = [
            serialize_value({"name": "Alice", "age": 30}),
            serialize_value([1, 2, 3]),
            serialize_value("hello"),
            serialize_value(42),
        ]
        env = _rpc(
            server, "executeWord", {"word_name": "DUP", "stack": complex_stack}
        )
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [{"name": "Alice", "age": 30}, [1, 2, 3], "hello", 42, 42]

    def test_null_with_empty_stack(self, server):
        env = _rpc(server, "executeWord", {"word_name": "NULL", "stack": []})
        stack = [deserialize_value(v) for v in env["result"]["result_stack"]]
        assert stack == [None]
