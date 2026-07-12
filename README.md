# Forthic Python Runtime

**A Python runtime for [Forthic](https://github.com/forthix/forthic)** - *the* stack-based, concatenative language for composable transformations.

Use Forthic to wrap your Python code within composable words, leveraging categorical principles for clean, powerful abstractions.

**[Learn at forthix.com](https://forthix.com)** | **[Forthic Docs](https://github.com/forthix/forthic)** | **[Getting Started](#getting-started)** | **[Examples](examples/)** | **[API Docs](docs/)**

---

## What is Forthic?

Forthic enables **categorical coding** - a way to solve problems by viewing them in terms of transformation rather than computation. This Python runtime lets you:

1. **Wrap existing code** with simple decorators
2. **Compose transformations** cleanly using stack-based operations
3. **Build powerful abstractions** from simple primitives

**[Learn more about Categorical Coding →](https://forthix.com/blog/category-theory-for-the-rest-of-us-coders)**

See the [Forthic repository](https://github.com/forthix/forthic) for technical documentation and API references.

---

## Quick Example

### Create a Module

```python
from forthic.decorators import DecoratedModule, ForthicWord

class AnalyticsModule(DecoratedModule):
    def __init__(self):
        super().__init__("analytics")

    @ForthicWord("( numbers -- avg )", "Calculate average")
    async def AVERAGE(self, numbers):
        return sum(numbers) / len(numbers)

    @ForthicWord("( numbers stdDevs -- filtered )", "Filter outliers beyond N std devs")
    async def FILTER_OUTLIERS(self, numbers, std_devs):
        import statistics
        mean = sum(numbers) / len(numbers)
        std_dev = statistics.stdev(numbers)
        threshold = std_dev * std_devs
        return [n for n in numbers if abs(n - mean) <= threshold]
```

### Use It

```python
import asyncio
from forthic import Interpreter

async def main():
    interp = Interpreter()
    interp.register_module(AnalyticsModule())

    await interp.run("""
        ["analytics"] USE-MODULES

        [1 2 3 100 4 5] 2 FILTER-OUTLIERS AVERAGE
    """)

    result = interp.stack_pop()  # Clean average without outliers
    print(result)

asyncio.run(main())
```

---

## Installation

Install from PyPI:

```bash
pip install forthic-py
```

Or for development:

```bash
cd forthic-py
pip install -e ".[dev]"
```

---

## Getting Started

### Basic Usage

```python
import asyncio
from forthic import Interpreter

async def main():
    interp = Interpreter()

    # Execute Forthic code
    await interp.run("""
        [1 2 3 4 5] "2 *" MAP  # Double each element
    """)

    result = interp.stack_pop()  # [2, 4, 6, 8, 10]
    print(result)

asyncio.run(main())
```

### Creating Your First Module

```python
from forthic.decorators import DecoratedModule, ForthicWord

class MyModule(DecoratedModule):
    def __init__(self):
        super().__init__("mymodule")

    @ForthicWord("( data -- result )", "Process data your way")
    async def PROCESS(self, data):
        # Wrap your existing Python code
        return my_existing_function(data)

# Register and use
async def main():
    interp = Interpreter()
    interp.register_module(MyModule())

    await interp.run("""
        ["mymodule"] USE-MODULES
        SOME-DATA PROCESS
    """)

asyncio.run(main())
```

See [examples/README.md](examples/README.md) for detailed tutorials and examples.

---

## Features

### Standard Library

The Python runtime includes comprehensive standard modules:

- **array** - MAP, SELECT, SORT, GROUP-BY, ZIP, REDUCE, FLATTEN (30+ operations)
- **record** - REC@, <REC, MERGE, KEYS, VALUES, INVERT-KEYS
- **string** - SPLIT, JOIN, UPPERCASE, LOWERCASE, TRIM, REPLACE
- **math** - +, -, *, /, ROUND, ABS, MIN, MAX, AVERAGE
- **datetime** - >DATE, >DATETIME, ADD-DAYS, FORMAT, DIFF-DAYS
- **json** - >JSON, JSON>, JSON-PRETTIFY
- **boolean** - ==, <, >, AND, OR, NOT, IN

See [docs/modules/](docs/modules/) for complete reference.

### Pandas Integration

Python-specific module for DataFrame operations:

```python
await interp.run("""
    ["pandas"] USE-MODULES

    [
        [ [.name "Alice"] [.age 30] ] REC
        [ [.name "Bob"]   [.age 25] ] REC
    ] DF-FROM-RECORDS
""")
```

Includes: DF-FROM-RECORDS, DF-TO-RECORDS, DF-SELECT, DF-SORT, DF-GROUP-BY, DF-READ-CSV, DF-TO-CSV, DF-READ-EXCEL, DF-TO-EXCEL

### Easy Module Creation

The decorator system makes wrapping code trivial:

```python
@ForthicWord("( input -- output )", "Description")
async def MY_WORD(self, input):
    return your_logic(input)
```

### Python Integration

- Full Python compatibility (Python 3.8+)
- Async/await support with `asyncio`
- Works with existing Python libraries
- Native Python error handling

---

## Documentation

### Learning Resources
- **[forthix.com](https://forthix.com)** - Learn about Forthic and Categorical Coding
- **[Category Theory for Coders](https://forthix.com/blog/category-theory-for-the-rest-of-us-coders)** - Understand the foundations

### This Runtime
- **[Module API Reference](docs/modules/)** - Standard library documentation
- **[Examples](examples/)** - Working code samples

### Core Forthic Concepts
- **[Main Forthic Docs](https://github.com/forthix/forthic)** - Philosophy, language guide
- **[Why Forthic?](https://github.com/forthix/forthic/blob/main/docs/why-forthic.md)** - Motivation and core principles
- **[Category Theory](https://github.com/forthix/forthic/blob/main/docs/language/category-theory.md)** - Mathematical foundations
- **[Building Modules](https://github.com/forthix/forthic/blob/main/docs/tutorials/building-modules.md)** - Module creation patterns

---

## Examples

See the [examples/](examples/) directory for working code samples including:
- Basic usage patterns
- Custom module creation
- Multi-runtime execution
- Pandas DataFrame integration

---

## Building

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=forthic

# Generate documentation
python -m scripts.generate_docs
```

---

## JSON-RPC Transport

Expose Python-specific modules to other Forthic runtimes over JSON-RPC 2.0 (HTTP POST `/rpc`). The wire format matches the TypeScript and Rust JSON-RPC servers, so the runtimes are interoperable.

### Start the server

```bash
# Default port 8765
python -m forthic.jsonrpc.server

# With custom modules loaded from a YAML config
python -m forthic.jsonrpc.server --modules-config examples/example_modules_config.yaml
```

### Call it from Python

```python
from forthic.jsonrpc import JsonRpcClient

async def main():
    client = JsonRpcClient("localhost:8765")
    result = await client.execute_word("MULTIPLY", [5, 3])
    print(result)  # [15]
```

### Learn More

- **[Module Loading](docs/module-loading.md)** - YAML config for serving custom modules
- **[Examples](examples/)** - Working code samples

---

## Project Structure

```
forthic-py/
├── forthic/              # Core library code
│   ├── decorators/       # Decorator system for modules and words
│   ├── modules/          # Standard library modules
│   │   ├── standard/     # Standard modules (array, string, math, etc.)
│   │   └── pandas/       # Python-specific pandas integration
│   ├── jsonrpc/          # JSON-RPC 2.0 client/server transport
│   ├── interpreter.py    # Main interpreter implementation
│   ├── module.py         # Module and word classes
│   ├── tokenizer.py      # Lexical analysis
│   └── errors.py         # Error classes
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── scripts/              # Utility scripts
│   └── generate_docs.py  # Documentation generator
└── docs/                 # Documentation
```

---

## Cross-Runtime Compatibility

This Python implementation maintains compatibility with:
- **forthic-ts** (TypeScript/JavaScript)
- **forthic-rb** (Ruby)
- **forthic-rs** (Rust, in progress)

All runtimes share the same test suite and language semantics to ensure consistent behavior across platforms.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, or refer to the main [Forthic contributing guide](https://github.com/forthix/forthic/blob/main/CONTRIBUTING.md).

When adding new words or modules:

1. Use the decorator system (`@ForthicWord` or `@DirectWord`)
2. Include stack effect notation: `( input -- output )`
3. Provide clear descriptions
4. Add corresponding tests in `tests/`
5. Regenerate documentation: `python -m scripts.generate_docs`

---

## Community

- **Main Repository:** [forthix/forthic](https://github.com/forthix/forthic)
- **Issues:** [Report issues](https://github.com/forthix/forthic-py/issues)
- **Discussions:** [GitHub Discussions](https://github.com/forthix/forthic/discussions)
- **Examples:** [Real-world applications](examples/)

---

## License

[BSD-2-Clause License](LICENSE) - Copyright 2024 LinkedIn Corporation. Copyright 2025 Forthix LLC.

---

## Related

- **[Forthic (main repo)](https://github.com/forthix/forthic)** - Core documentation and concepts

---

**Forthic**: Wrap. Compose. Abstract.
