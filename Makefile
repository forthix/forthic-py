.PHONY: help install-dev install-venv jsonrpc-server test lint typecheck clean

help:
	@echo "Forthic Python Runtime - Make Commands"
	@echo ""
	@echo "  make install-dev      Install development dependencies (system-wide)"
	@echo "  make install-venv     Install development dependencies (into .venv via uv)"
	@echo "  make jsonrpc-server   Start the JSON-RPC server"
	@echo "  make test             Run tests"
	@echo "  make lint             Run ruff"
	@echo "  make typecheck        Run mypy"
	@echo "  make clean            Clean generated files"

install-dev:
	python3 -m pip install --break-system-packages -e ".[dev]"

install-venv:
	uv venv --python 3.12
	uv pip install -e ".[dev]"

jsonrpc-server:
	@echo "Starting Forthic Python JSON-RPC server..."
	uv run python -m forthic.jsonrpc.server

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy forthic

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
