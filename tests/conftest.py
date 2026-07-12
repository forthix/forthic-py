"""Pytest collection guards for tests that depend on optional packages.

The module-loader tests need `pyyaml`. It is listed as an install
requirement in pyproject.toml, but a bare checkout without
`pip install -e ".[dev]"` may be missing it.

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
    "yaml": (
        "unit/jsonrpc/test_module_loader.py",
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
