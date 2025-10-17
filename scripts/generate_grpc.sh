#!/bin/bash
# Generate Python gRPC code from proto files

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PROTO_DIR="$( cd "$PROJECT_ROOT/../forthic/protos" && pwd )"

cd "$PROJECT_ROOT"

echo "Generating Python gRPC code from $PROTO_DIR/forthic_runtime.proto"

python -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out=./forthic/grpc \
  --grpc_python_out=./forthic/grpc \
  --pyi_out=./forthic/grpc \
  "$PROTO_DIR/forthic_runtime.proto"

echo "Generated files in forthic/grpc:"
ls -l forthic/grpc/forthic_runtime_pb2*
