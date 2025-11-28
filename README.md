# Forthic Python Runtime

A Python runtime for Forthic - a stack-based, concatenative programming language.


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
    await interp.run(": DOUBLE 2 * ;")

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

## License

BSD 2-Clause License - See LICENSE file for details
