"""Integration-style tests for JsonRpcClient against a real local server."""

from __future__ import annotations

import socket

import pytest

from forthic.grpc.errors import RemoteRuntimeError
from forthic.jsonrpc.client import JsonRpcClient
from forthic.jsonrpc.server import serve


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def client():
    port = _free_port()
    srv = serve(port=port, host="127.0.0.1", blocking=False)
    try:
        yield JsonRpcClient(f"127.0.0.1:{port}")
    finally:
        srv.shutdown()
        srv.server_close()


class TestModuleDiscovery:
    async def test_list_modules_returns_array(self, client):
        modules = await client.list_modules()
        assert isinstance(modules, list)

    async def test_get_module_info_throws_for_unknown(self, client):
        with pytest.raises(Exception):
            await client.get_module_info("no_such_module")


class TestWordExecution:
    async def test_plus(self, client):
        assert await client.execute_word("+", [1, 2]) == [3]

    async def test_map(self, client):
        assert await client.execute_word("MAP", [[1, 2, 3], "2 *"]) == [[2, 4, 6]]

    async def test_rec_at(self, client):
        result = await client.execute_word("REC@", [{"name": "Alice"}, "name"])
        assert result == ["Alice"]

    async def test_unknown_word_raises_remote_runtime_error(self, client):
        with pytest.raises(RemoteRuntimeError) as excinfo:
            await client.execute_word("UNKNOWN_WORD", [])
        assert excinfo.value.runtime == "python"
        assert "UNKNOWN_WORD" in str(excinfo.value)

    async def test_stack_underflow_raises(self, client):
        with pytest.raises(RemoteRuntimeError):
            await client.execute_word("+", [])


class TestSequenceExecution:
    async def test_minus_then_divide(self, client):
        result = await client.execute_sequence(["-", "/"], [10, 5, 2])
        assert len(result) == 1
        assert result[0] == pytest.approx(3.333, abs=0.01)

    async def test_empty_sequence_returns_original(self, client):
        assert await client.execute_sequence([], [1, 2, 3]) == [1, 2, 3]

    async def test_sequence_stops_on_error(self, client):
        with pytest.raises(RemoteRuntimeError):
            await client.execute_sequence(["+", "UNKNOWN_WORD"], [1, 2])


class TestTypeSerialization:
    async def test_null_equality(self, client):
        assert await client.execute_word("==", [None, None]) == [True]

    async def test_boolean_or(self, client):
        assert await client.execute_word("OR", [True, False]) == [True]

    async def test_nested_array_flatten(self, client):
        assert await client.execute_word("FLATTEN", [[[1, 2], [3, 4]]]) == [
            [1, 2, 3, 4]
        ]

    async def test_nested_records(self, client):
        result = await client.execute_word(
            "REC@",
            [{"user": {"name": "Alice", "address": {"city": "NYC"}}}, "user"],
        )
        assert result == [{"name": "Alice", "address": {"city": "NYC"}}]
