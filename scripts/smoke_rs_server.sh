#!/usr/bin/env bash
# Cross-runtime smoke: start the forthic-rs JSON-RPC server, drive it with
# the real forthic-py JsonRpcClient (see smoke_rs_server.py).
#
# Requires: cargo, and a forthic-rs checkout at FORTHIC_RS_DIR (default:
# ../forthic-rs relative to this repo).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORTHIC_RS_DIR="${FORTHIC_RS_DIR:-$REPO_DIR/../forthic-rs}"
PORT="${PORT:-18997}"

if [ ! -f "$FORTHIC_RS_DIR/Cargo.toml" ]; then
  echo "forthic-rs checkout not found at $FORTHIC_RS_DIR (set FORTHIC_RS_DIR)" >&2
  exit 2
fi

(cd "$FORTHIC_RS_DIR" && cargo build --features jsonrpc --quiet)
"$FORTHIC_RS_DIR/target/debug/forthic-jsonrpc" --port "$PORT" > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

# Wait for the server to accept connections
for _ in $(seq 1 50); do
  if curl -s -o /dev/null -X POST "127.0.0.1:$PORT/rpc" \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","id":0,"method":"listModules","params":{}}'; then
    break
  fi
  sleep 0.1
done

cd "$REPO_DIR"
uv run --no-sync python scripts/smoke_rs_server.py "$PORT"
