.PHONY: help install-dev install-venv generate-grpc grpc-server test clean

help:
	@echo "Forthic Python Runtime - Make Commands"
	@echo ""
	@echo "  make install-dev      Install development dependencies (system-wide)"
	@echo "  make install-venv     Install development dependencies (into myenv venv)"
	@echo "  make generate-grpc    Generate Python gRPC code from proto files"
	@echo "  make grpc-server      Start the gRPC server (Phase 1)"
	@echo "  make test             Run tests"
	@echo "  make clean            Clean generated files"

install-dev:
	python3 -m pip install --break-system-packages -e ".[dev,grpc]"

install-venv:
	@if [ ! -d "myenv" ]; then \
		echo "Error: myenv virtual environment not found."; \
		echo "Create it with: python3 -m venv myenv"; \
		exit 1; \
	fi
	. myenv/bin/activate && pip install -e ".[dev,grpc]"

generate-grpc:
	@echo "Generating Python gRPC code from proto files..."
	@if [ -d "myenv" ]; then \
		echo "Using myenv virtual environment..."; \
		. myenv/bin/activate && python -m grpc_tools.protoc \
			-I../forthic/protos \
			--python_out=./forthic/grpc \
			--grpc_python_out=./forthic/grpc \
			--pyi_out=./forthic/grpc \
			../forthic/protos/forthic_runtime.proto && \
		python scripts/fix_grpc_imports.py; \
	else \
		python3 -m grpc_tools.protoc \
			-I../forthic/protos \
			--python_out=./forthic/grpc \
			--grpc_python_out=./forthic/grpc \
			--pyi_out=./forthic/grpc \
			../forthic/protos/forthic_runtime.proto && \
		python3 scripts/fix_grpc_imports.py; \
	fi
	@echo "Generated files:"
	@ls -l forthic/grpc/forthic_runtime_pb2*

grpc-server:
	@echo "Starting Forthic Python gRPC server on port 50051..."
	@if [ -d "myenv" ]; then \
		echo "Using myenv virtual environment..."; \
		. myenv/bin/activate && python -m forthic.grpc.server; \
	else \
		python3 -m forthic.grpc.server; \
	fi

test:
	pytest

clean:
	rm -f forthic/grpc/forthic_runtime_pb2*.py
	rm -f forthic/grpc/forthic_runtime_pb2*.pyi
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
