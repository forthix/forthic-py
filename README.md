# Forthic Python Runtime

A modern Python runtime for Forthic - a stack-based, concatenative programming language.

## Status

- ✅ **Phase 1**: Core Infrastructure (COMPLETE)
- ✅ **Phase 2**: Decorator System (COMPLETE)
- ✅ **Phase 10.5**: Configuration-Based Module Loading (COMPLETE)

## Phase 1 Status: Core Infrastructure (COMPLETE)

Phase 1 implementation includes:

- ✅ Project setup with modern Python tooling (pyproject.toml, ruff, mypy, pytest)
- ✅ Tokenizer for parsing Forthic syntax
- ✅ Basic literal handlers (int, float, bool, string)
- ✅ Core module system (Word classes, Variable, Module, Stack)
- ✅ Basic interpreter with stack management
- ✅ Word definitions (`:` and `@:` for memos)
- ✅ Module system with imports
- ✅ Arrays and nested structures
- ✅ Comprehensive test suite

## Installation (Development)

```bash
cd forthic-py
pip install -e ".[dev]"
```

## Quick Start

```python
import asyncio
from forthic import Interpreter

async def main():
    interp = Interpreter()

    # Push some numbers
    await interp.run("42 3.14 TRUE")

    # Create an array
    await interp.run("[1 2 3]")

    # Define a word
    await interp.run(": DOUBLE 2 * ;")  # Note: * not implemented in Phase 1

    # Get the stack
    stack = interp.get_stack()
    print("Stack:", stack.get_items())

asyncio.run(main())
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=forthic

# Run specific test file
pytest tests/test_tokenizer.py

# Run with verbose output
pytest -v
```

## Code Quality

```bash
# Format code
ruff format forthic tests

# Lint code
ruff check forthic tests

# Type check
mypy forthic
```

## Project Structure

```
forthic-py/
├── forthic/              # Main package
│   ├── __init__.py      # Public API
│   ├── errors.py        # Error classes
│   ├── tokenizer.py     # Tokenizer
│   ├── literals.py      # Literal handlers
│   ├── module.py        # Word, Module, Stack classes
│   └── interpreter.py   # Core interpreter
├── tests/               # Test suite
│   ├── test_tokenizer.py
│   ├── test_literals.py
│   └── test_interpreter.py
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## gRPC Server with Dynamic Module Loading

The Python runtime includes a production-ready gRPC server that supports configuration-based module loading:

```bash
# Install with gRPC support
pip install -e ".[grpc]"

# Start server with default modules
python -m forthic.grpc.server

# Start with custom module configuration
python -m forthic.grpc.server --modules-config modules.yaml

# Or use the console script
forthic-py-server --modules-config modules.yaml
```

### Creating Custom Modules

```python
# my_module.py
from forthic.decorators import DecoratedModule, Word

class MyModule(DecoratedModule):
    def __init__(self):
        super().__init__("mymodule")

    @Word("( a b -- c )", "Add two numbers")
    async def ADD(self, a, b):
        return a + b
```

### Module Configuration

```yaml
# modules.yaml
modules:
  - name: mymodule
    import_path: my_module:MyModule
    optional: false
    description: "My custom module"
```

### Using from TypeScript

```typescript
import { GrpcClient } from '@forthix/forthic-ts/grpc';

const client = new GrpcClient('localhost:50051');
const result = await client.executeWord('ADD', [5, 3]); // [8]
```

See [Module Loading Documentation](docs/module-loading.md) for complete details.

## What's Next

See `IMPLEMENTATION_PLAN.md` for the full development roadmap.

## Features Implemented (Phase 1)

### Tokenizer
- String literals (single, double, triple quotes)
- Word tokens
- Comments
- Arrays `[...]`
- Modules `{name ...}`
- Definitions `: NAME ... ;`
- Memos `@: NAME ... ;`
- Dot symbols `.key`

### Literals
- Booleans: `TRUE`, `FALSE`
- Integers: `42`, `-10`
- Floats: `3.14`, `-2.5`
- Strings: `"hello"`, `'world'`, `"""multiline"""`

### Interpreter
- Stack-based execution
- Word definitions and execution
- Module system with registration and imports
- Variable system
- Memoized words
- Error handling with location tracking
- Profiling support

### Module System
- Word classes: `Word`, `PushValueWord`, `DefinitionWord`
- Module class with word/variable management
- Stack class with array-like access
- Module imports with optional prefixes
- Exportable word lists

## License

BSD 2-Clause License - See LICENSE file for details
