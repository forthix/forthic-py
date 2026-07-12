#!/usr/bin/env python3
"""Cross-runtime smoke: drive the forthic-rs JSON-RPC server with the real
forthic-py JsonRpcClient. The other half of the wire-compatibility proof.

Usage: python scripts/smoke_rs_server.py <port>
The rs server must already be listening on <port> (smoke_rs_server.sh
handles building and starting it).
"""

import asyncio
import sys
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from forthic.jsonrpc import JsonRpcClient
from forthic.jsonrpc.errors import RemoteRuntimeError


def check(cond: bool, message: str) -> None:
    if not cond:
        print(f"SMOKE FAILED: {message}", file=sys.stderr)
        sys.exit(1)


async def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "18997"
    client = JsonRpcClient(f"127.0.0.1:{port}")

    # 1. Mixed-type stack round-trips through the rust runtime
    zoned = datetime(2020, 6, 5, 10, 15, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
    stack = [
        42,
        "hello",
        3.25,
        True,
        None,
        [1, [2, {"deep": "record"}]],
        date(2020, 6, 5),
        time(9, 30, 0),
        zoned,
    ]
    result = await client.execute_word("DUP", stack)
    check(len(result) == len(stack) + 1, f"DUP: expected {len(stack) + 1} items, got {len(result)}")
    check(result[:5] == [42, "hello", 3.25, True, None], "scalars/bool/null survived")
    check(result[5] == [1, [2, {"deep": "record"}]], "nested containers survived")
    check(result[6] == date(2020, 6, 5), "PlainDate survived")
    check(result[7] == time(9, 30, 0), "PlainTime survived")
    check(result[8] == zoned and str(result[8].tzinfo) == "America/Los_Angeles", "ZonedDateTime survived")
    check(result[9] == zoned, "DUP duplicated the zoned datetime")

    # 2. executeSequence
    seq = await client.execute_sequence(["DUP", "+"], [21])
    check(seq == [42], f"executeSequence: expected [42], got {seq!r}")

    # 3. listModules
    modules = await client.list_modules()
    check(isinstance(modules, list), "listModules returns an array")

    # 4. Rich errors surface as RemoteRuntimeError with rust metadata
    threw = False
    try:
        await client.execute_word("NO-SUCH-WORD", [])
    except RemoteRuntimeError as e:
        threw = True
        check(e.runtime == "rust", f"error runtime: {e.runtime}")
        check(e.error_type == "UnknownWord", f"error type: {e.error_type}")
        check(e.context.get("word_name") == "NO-SUCH-WORD", "error context intact")
    check(threw, "unknown word raised")

    print("cross-runtime smoke OK (py client <-> rs server)")


asyncio.run(main())
