# Forthic Python Runtime Implementation Plan

## Overview
Create a modern Python runtime for Forthic that mirrors the TypeScript implementation, with special focus on the elegant Word decorator pattern for easy module creation.

## Architecture Analysis

### Key TypeScript Patterns to Mirror:

1. **Decorator-based Word Registration** (`@Word`, `@DirectWord`)
   - Automatic stack marshalling
   - Stack effect notation parsing
   - Optional `WordOptions` parameter support
   - Metadata storage for documentation

2. **Module System**
   - `DecoratedModule` base class with automatic word registration
   - Module metadata with categories, examples, options info
   - Import/export with prefixing support

3. **Core Components**
   - Interpreter with stack management
   - Tokenizer for parsing Forthic syntax
   - Module registry and module stack
   - Literal handlers (dates, numbers, booleans)
   - WordOptions for flexible parameter passing

## Phased Implementation Plan

### Phase 1: Core Infrastructure (Foundation)
**Goal:** Establish the basic runtime without decorators

#### 1.1 Project Setup
- Create `forthic-py/` directory structure
- Setup modern Python tooling:
  - `pyproject.toml` (PEP 517/518)
  - `ruff` for linting/formatting
  - `mypy` for type checking
  - `pytest` for testing
- Use Python 3.10+ features (dataclasses, pattern matching, type hints)

#### 1.2 Basic Types & Tokenizer
- `tokenizer.py`: Port token types, Tokenizer class
- `literals.py`: Basic literal handlers (int, float, bool, string)
- Create Token, CodeLocation, PositionedString classes

#### 1.3 Core Module System
- `module.py`:
  - Word base class
  - PushValueWord, DefinitionWord, ExecuteWord
  - Variable class
  - Module class (without decorators)
- Stack class with proper typing

#### 1.4 Basic Interpreter
- `interpreter.py`:
  - Stack operations
  - Module stack management
  - Token handling
  - Word execution
  - Error handling classes

**Deliverable:** Basic interpreter that can execute simple Forthic code with manually registered words

---

### Phase 2: Decorator System (The Magic)
**Goal:** Implement the elegant @Word decorator pattern

#### 2.1 Decorator Infrastructure
- `decorators/word.py`:
  - Stack effect parser (extract input count, detect WordOptions)
  - Metadata storage using weak references
  - `@Word` decorator with automatic stack marshalling
  - `@DirectWord` decorator for manual stack access

#### 2.2 DecoratedModule Base Class
- Auto-registration of decorated words on `set_interp()`
- `getWordDocs()` method for introspection
- `getModuleMetadata()` for module-level docs

#### 2.3 Module Documentation
- `registerModuleDoc()` helper
- Markdown doc string parser (Categories, Options, Examples)
- Support for categorized word lists

**Deliverable:** Decorator system allowing natural Python method definitions to become Forthic words

---

### Phase 3: WordOptions System
**Goal:** Enable flexible optional parameters

#### 3.1 WordOptions Class
- `word_options.py`:
  - Parse flat array `[.key1 val1 .key2 val2]` into dict
  - `get()`, `has()`, `toDict()` methods
  - Integration with @Word decorator

#### 3.2 Core Module ~> Operator
- Implement array-to-WordOptions conversion
- Test with simple options-accepting words

**Deliverable:** Options system for flexible word parameters (like `[.depth 1] ~> FLATTEN`)

---

### Phase 4: Standard Library Modules
**Goal:** Port essential modules using decorators

#### 4.1 Core Module
- Stack operations: `POP`, `DUP`, `SWAP`
- Variables: `!`, `@`, `!@`, `VARIABLES`
- Module system: `EXPORT`, `USE_MODULES`
- Control flow: `IDENTITY`, `NOP`, `DEFAULT`, `*DEFAULT`
- String interpolation: `INTERPOLATE`, `PRINT`

#### 4.2 Array Module
- Transform: `MAP`, `SELECT`, `REDUCE`, `FOREACH`
- Access: `NTH`, `LAST`, `SLICE`, `TAKE`, `DROP`
- Combine: `APPEND`, `ZIP`, `CONCAT`
- Group: `GROUP_BY`, `GROUP_BY_FIELD`, `BY_FIELD`
- Options support: `with_key`, `push_error`, `depth`, `push_rest`

#### 4.3 Other Standard Modules
- `boolean_module.py`: `==`, `<`, `>`, `AND`, `OR`, `NOT`, `IN`
- `math_module.py`: `+`, `-`, `*`, `/`, `ROUND`, `ABS`, `MIN`, `MAX`
- `string_module.py`: `SPLIT`, `JOIN`, `UPPERCASE`, `LOWERCASE`, `TRIM`
- `record_module.py`: `REC@`, `<REC`, `MERGE`, `KEYS`, `VALUES`
- `json_module.py`: `>JSON`, `JSON>`, `JSON-PRETTIFY`

**Deliverable:** Full standard library matching TypeScript functionality

---

### Phase 5: Advanced Features
**Goal:** Complete feature parity

#### 5.1 DateTime Support
- Use `zoneinfo` (Python 3.9+) for timezone handling
- Implement temporal literal handlers
- DateTime module: `>DATE`, `>DATETIME`, `ADD_DAYS`, `FORMAT`, `SUBTRACT_DAYS`

#### 5.2 Profiling & Debugging
- Word execution counting
- Timestamp tracking
- `PROFILE_START`, `PROFILE_END`, `PROFILE_DATA`
- `PEEK!`, `STACK!` debug words

#### 5.3 Streaming Execution
- `streamingRun()` generator method
- Token-by-token execution
- Support for `START_LOG`, `END_LOG`

**Deliverable:** Complete runtime with all advanced features

---

### Phase 6: Python-Specific Enhancements
**Goal:** Leverage Python's strengths

#### 6.1 Pythonic Conveniences
- Context managers for module scope
- Async/await support (already in TS version)
- Generator-based iteration
- Type hints throughout

#### 6.2 Integration Patterns
- Easy integration with pandas DataFrames
- NumPy array support
- Requests/httpx for HTTP operations
- SQLAlchemy integration helpers

#### 6.3 Package Distribution
- PyPI package as `forthic`
- CLI tool: `python -m forthic` or `forthic` command
- REPL with readline support
- Documentation site (Sphinx or MkDocs)

**Deliverable:** Production-ready Python package

---

## Key Design Decisions

### Modern Python Features:
1. **Type Hints:** Full typing with `typing`, `Protocol`, `TypeAlias`
2. **Dataclasses:** For Token, CodeLocation, etc.
3. **Pattern Matching:** For token handling (Python 3.10+)
4. **Async/Await:** Support async words naturally
5. **Descriptors:** For elegant decorator implementation

### Decorator Implementation Strategy:
```python
from typing import Any, Callable
from functools import wraps

def Word(stack_effect: str, description: str = "", name: str = None):
    """Decorator that auto-marshalls stack arguments"""
    def decorator(method: Callable) -> Callable:
        # Parse stack_effect to get input_count and has_options
        parsed = parse_stack_notation(stack_effect)

        # Store metadata
        store_word_metadata(method, {
            'stack_effect': stack_effect,
            'description': description,
            'word_name': name or method.__name__.upper(),
            'input_count': parsed.input_count,
            'has_options': parsed.has_options
        })

        @wraps(method)
        async def wrapper(self, interp: Interpreter):
            # Pop inputs from stack
            inputs = []
            for _ in range(parsed.input_count):
                inputs.insert(0, interp.stack_pop())

            # Check for optional WordOptions
            options = {}
            if parsed.has_options:
                top = interp.stack_peek()
                if isinstance(top, WordOptions):
                    opts = interp.stack_pop()
                    options = opts.to_dict()
                inputs.append(options)

            # Call original method
            result = await method(self, *inputs)

            # Push result if not None
            if result is not None:
                interp.stack_push(result)

        return wrapper
    return decorator
```

### Module Example:
```python
class ArrayModule(DecoratedModule):
    """Array and collection operations"""

    def __init__(self):
        super().__init__("array")

    @Word("( array:list item:any -- array:list )", "Append item to array")
    async def APPEND(self, array: list, item: Any) -> list:
        result = array or []
        result.append(item)
        return result

    @Word("( items:list forthic:str [options:WordOptions] -- mapped:list )",
          "Map function over items")
    async def MAP(self, items: list, forthic: str, options: dict) -> list:
        with_key = options.get('with_key', False)
        result = []
        for i, item in enumerate(items):
            if with_key:
                self.interp.stack_push(i)
            self.interp.stack_push(item)
            await self.interp.run(forthic)
            result.append(self.interp.stack_pop())
        return result
```

## Testing Strategy
- Unit tests for each component (pytest)
- Port all TypeScript tests to Python
- Property-based testing with Hypothesis
- Integration tests for full workflows
- Performance benchmarking vs TypeScript runtime

## Documentation
- Docstrings following NumPy/Google style
- Auto-generated API docs (Sphinx)
- Tutorial notebooks (Jupyter)
- Examples directory matching TypeScript version

## Success Criteria
1. All TypeScript tests pass in Python
2. Decorator pattern is elegant and Pythonic
3. Performance within 2x of TypeScript (acceptable for initial version)
4. Full type coverage (mypy strict mode)
5. Package installable via pip
6. Documentation at docs.forthic.org/python

---

## Estimated Timeline
- **Phase 1:** 1 week (Core Infrastructure)
- **Phase 2:** 3-4 days (Decorator System - critical phase)
- **Phase 3:** 2 days (WordOptions System)
- **Phase 4:** 1 week (Standard Library Modules)
- **Phase 5:** 3-4 days (Advanced Features)
- **Phase 6:** 1 week (Python-Specific Enhancements)

**Total: ~4 weeks for complete implementation**

---

## Reference Implementation
The TypeScript runtime at `../forthic-ts/` serves as the reference implementation. Key files to study:
- `src/forthic/decorators/word.ts` - Decorator pattern
- `src/forthic/interpreter.ts` - Core interpreter logic
- `src/forthic/module.ts` - Module system
- `src/forthic/word_options.ts` - Options system
- `src/forthic/modules/array_module.ts` - Example module with options
- `src/forthic/modules/core_module.ts` - Core operations
