"""Pytest collection guards for tests that depend on optional packages.

The gRPC tests need the `grpcio` package (plus generated proto files) and
several integration tests need `pyyaml`. Both are listed as install
requirements / optional extras in pyproject.toml, but a bare checkout
without `pip install -e ".[dev]"` will be missing them.

Rather than crash collection with ImportError, skip the affected paths so
the rest of `pytest` can still run. This file lives in `tests/` so it
applies to all subdirectories.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


# Map: required module -> test files (relative to tests/) that need it.
_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "grpc": (
        "unit/grpc/test_client.py",
        "unit/grpc/test_remote_module.py",
        "unit/grpc/test_remote_runtime_module.py",
        "unit/grpc/test_remote_word.py",
        "unit/grpc/test_runtime_manager.py",
        "integration/test_example_module_loading.py",
        "integration/test_server_config.py",
        "integration/test_phase11_9_standard_interpreter_integration.py",
    ),
    "yaml": (
        "unit/grpc/test_module_loader.py",
        "integration/test_example_module_loading.py",
        "integration/test_server_config.py",
    ),
}


collect_ignore: list[str] = []
for module, files in _REQUIREMENTS.items():
    if not _has(module):
        for rel_path in files:
            absolute = str(_TESTS_ROOT / rel_path)
            if absolute not in collect_ignore:
                collect_ignore.append(absolute)
