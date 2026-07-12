# Forthic Python Runtime

**A Python runtime for [Forthic](https://github.com/forthix/forthic)** — *the* stack-based, concatenative language for composable transformations.

This is the official **Python** runtime, sharing a cross-runtime contract with the [TypeScript reference implementation](https://github.com/forthix/forthic-ts) and the [Rust runtime](https://github.com/forthix/forthic-rs): the same words, the same semantics, the same wire format — so Forthic programs and the systems that host them can move between runtimes.

**[Learn at forthix.com](https://forthix.com)** | **[Forthic Docs](https://github.com/forthix/forthic)** | **[Getting Started](#getting-started)** | **[Examples](examples/)**

---

## Quick start

```python
import asyncio
from forthic.interpreter import StandardInterpreter

async def main():
    interp = StandardInterpreter(timezone="America/Los_Angeles")
    await interp.run("[ 1 2 3 4 5 ] '2 *' MAP SUM")
    print(interp.stack_pop())  # 30

asyncio.run(main())
```

The interpreter is **async** — words are coroutines, so Forthic words can await your Python I/O naturally.

## Installation

```bash
pip install forthic-py            # core (includes the JSON-RPC transport)
pip install 'forthic-py[pandas]'  # + the pandas host-interop module
```

## Language highlights

- **Words and modules**: `: NAME ... ;` definitions, `{module ... }` scoping, `USE-MODULES` imports (optionally prefixed)
- **Records and JQ paths**: `[["k" "v"]] REC`, with data-driven path access — `record 'a.b[0]' JQ@` (paths are data, never interpolated source)
- **Error handling as data** (Rust `Result` semantics): `'CODE' TRY` yields `{"ok": value}` or `{"error": {...}}`; `'CODE' TRY UNWRAP ≡ CODE`. Error-tolerant mapping via MAP's `.outcomes` option
- **Injection-safe interpolation**: `"Hello ${name}!" INTERPOLATE` — holes are variable names only, never expressions, with read-only lookup
- **Word options**: `[.with_key TRUE] ~> MAP`, `[.separator " | "] ~> PRINT`

## Standard library modules

- **core**: stack ops, variables, control flow (IF/IF-RUN/WHEN), predicates, TRY family, INTERPOLATE/PRINT, USE-MODULES
- **array**: MAP, FILTER, SORT, GROUP-BY, ZIP, FIND, MAP-AT, and the rest of the higher-order vocabulary
- **record**: REC, JQ@/JQ!/JQ-DEL, MERGE, PICK/OMIT, HAS-KEY?, entry conversions
- **string**: SPLIT/JOIN, SUBSTR/SPLICE, regex (RE-MATCH family), shell-flavored text tools (GREP, SED, CUT, LINES)
- **math**: arithmetic, aggregates (SUM, PRODUCT, MEAN), SQRT/CLAMP, FORMAT-FIXED, RANGE
- **boolean**: comparison, logic, membership (CONTAINS?, ANY?, ALL?)
- **datetime**: timezone-aware dates and times (interpreter-timezone resolution), date math, components
- **json**: serialization and parsing

Every word carries a stack effect and description as data (served by `get_word_docs()` and the JSON-RPC `getModuleInfo`).

### Pandas integration (py-only host interop)

```python
await interp.run("""
    ["pandas"] USE-MODULES
    [ [["name" "Alice"] ["age" 30]] REC
      [["name" "Bob"]   ["age" 25]] REC ] DF-FROM-RECORDS
""")
```

The pandas module is deliberately **non-portable** (like ts's `fs` module) — it wraps a Python-native library and is excluded from the cross-runtime contract.

## Creating a module

```python
from forthic.decorators import DecoratedModule, ForthicWord

class AnalyticsModule(DecoratedModule):
    def __init__(self):
        super().__init__("analytics")

    @ForthicWord("( numbers:number[] -- avg:number )", "Calculate average")
    async def AVERAGE(self, numbers):
        return sum(numbers) / len(numbers)
```

```python
interp.register_module(AnalyticsModule())
await interp.run('["analytics"] USE-MODULES  [1 2 3] AVERAGE')
```

Stack effects are **load-bearing**: the input side drives how many values are popped for your method, and the output side determines whether the return value is pushed (a Python `None` return is Forthic NULL when an output is declared).

## JSON-RPC transport

Expose Python modules to other Forthic runtimes over JSON-RPC 2.0 (HTTP POST `/rpc`). The wire format is shared with the forthic-ts and forthic-rs servers/clients.

```bash
# Default port 8765
python -m forthic.jsonrpc.server

# With custom modules loaded from a YAML config
python -m forthic.jsonrpc.server --modules-config examples/example_modules_config.yaml
```

```python
from forthic.jsonrpc import JsonRpcClient

client = JsonRpcClient("localhost:8765")
result = await client.execute_word("MULTIPLY", [5, 3])  # [15]
```

Wire compatibility is proven by cross-runtime smoke tests: `make smoke-ts` drives this runtime's server with the real forthic-ts client; `make smoke-rs` drives the forthic-rs server with this runtime's client. See [docs/module-loading.md](docs/module-loading.md) for serving custom modules.

## Cross-runtime notes

Runtime behavior is aligned with forthic-ts (the reference), with a small set of documented, deliberate divergences:

- **Host-native string units**: py measures strings in Unicode code points (same as rs); ts uses UTF-16 code units. They agree on all BMP text and diverge only on astral characters (`'🦀' STR-LENGTH` is 1 in py, 2 in ts)
- **Strict parsing**: no `parseInt`/`new Date()` leniency — malformed numbers and dates are errors or NULL, never guesses
- **JS truthiness everywhere**: empty containers are truthy, NaN is falsy — Python's native `bool()` is never the arbiter
- **Insertion-order records** in every word (Python dicts already are)
- **"null", never "undefined"**: ts's `UNDEFINED` word is documented host interop and does not cross the wire
- **py extensions**: `PI` and `E` (pending upstreaming to ts/rs)

See [plans/WORD-INVENTORY.md](plans/WORD-INVENTORY.md) for the word-by-word parity map.

## Development

```bash
make install-venv   # uv venv + dev dependencies
make test           # pytest (1000+ tests)
make lint           # ruff
make typecheck      # mypy
make smoke-ts       # cross-runtime: ts client <-> py server
make smoke-rs       # cross-runtime: py client <-> rs server
```

Requires Python 3.10+. CI runs the test matrix (3.10–3.12), ruff, mypy, and a JSON-RPC wire smoke on every PR.

## Project structure

```
forthic-py/
├── forthic/              # Core library
│   ├── decorators/       # Module/word decorator system
│   ├── modules/standard/ # The 8 standard modules
│   ├── modules/          # pandas host interop
│   ├── jsonrpc/          # JSON-RPC 2.0 client/server transport
│   ├── interpreter.py    # Interpreter + StandardInterpreter
│   ├── module.py         # Module and word classes
│   ├── tokenizer.py      # Lexical analysis
│   └── errors.py         # Error classes
├── tests/                # Unit + integration tests (contract specs in tests/unit/core/)
├── scripts/              # Docs generation, cross-runtime smoke
└── plans/                # Parity scrub plans and word inventory
```

## Versioning

Versioned by parity milestone (the forthic-rs convention): **v0.6.0** corresponds to the settled cross-runtime contract shared with post-scrub forthic-ts and forthic-rs v0.6.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, or the main [Forthic contributing guide](https://github.com/forthix/forthic/blob/main/CONTRIBUTING.md).
