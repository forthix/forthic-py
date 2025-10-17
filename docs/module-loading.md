# Configuration-Based Module Loading

The Forthic Python gRPC server supports loading custom modules via a YAML configuration file, enabling extensibility without code modifications.

## Quick Start

### 1. Create a Custom Module

```python
# my_module.py
from forthic.decorators import DecoratedModule, Word

class MyModule(DecoratedModule):
    def __init__(self):
        super().__init__("mymodule")

    @Word("( a b -- c )", "Add two numbers")
    async def ADD(self, a, b):
        return a + b

    @Word("( text -- text )", "Convert to uppercase")
    async def UPPERCASE(self, text: str) -> str:
        return text.upper()
```

### 2. Create Module Configuration

```yaml
# modules.yaml
modules:
  - name: mymodule
    import_path: my_module:MyModule
    optional: false
    description: "My custom module"
```

### 3. Start Server with Configuration

```bash
python -m forthic.grpc.server --modules-config modules.yaml
```

Or use the console script if you installed the package:

```bash
forthic-py-server --modules-config modules.yaml
```

### 4. Use from TypeScript

```typescript
import { GrpcClient } from '@forthix/forthic-ts/grpc';

const client = new GrpcClient('localhost:50051');

// Discover available modules
const modules = await client.listModules();
console.log(modules); // [{ name: 'mymodule', ... }]

// Get module details
const info = await client.getModuleInfo('mymodule');
console.log(info.words); // [{ name: 'ADD', stack_effect: '( a b -- c )', ... }]

// Execute words
const result = await client.executeWord('ADD', [5, 3]);
console.log(result); // [8]

const result2 = await client.executeWord('UPPERCASE', ['hello']);
console.log(result2); // ['HELLO']
```

## Configuration Schema

```yaml
modules:
  - name: <module-name>           # Name exposed via gRPC (required)
    import_path: <module:Class>   # Python import path (required)
    optional: <true|false>         # Fail server if can't load? (default: false)
    description: <description>     # Human-readable description (optional)
```

### Fields

- **name**: Module name as exposed via gRPC. Used when calling `USE-PY-MODULES` from Forthic code.
- **import_path**: Python import path in format `"module.path:ClassName"`. The module must be importable from the server's Python path.
- **optional**: If `true`, module loading failure won't stop server startup. If `false` (default), server will exit if the module cannot be loaded.
- **description**: Human-readable description for documentation purposes.

## Environment Variable

You can specify the modules configuration via environment variable:

```bash
export FORTHIC_MODULES_CONFIG=/etc/forthic/modules.yaml
python -m forthic.grpc.server

# Config file location precedence:
# 1. --modules-config command line argument
# 2. FORTHIC_MODULES_CONFIG environment variable
# 3. None (default behavior - loads pandas if available)
```

## Example Configuration

See `examples/example_modules_config.yaml` for a complete example:

```yaml
modules:
  # Load the example module (required)
  - name: example
    import_path: examples.dynamic_module_example:ExampleModule
    optional: false
    description: "Example module with math, string, and list operations"

  # Load pandas (optional - won't fail if not installed)
  - name: pandas
    import_path: forthic.modules.pandas_module:PandasModule
    optional: true
    description: "Pandas DataFrame operations"
```

## Production Deployment

### Option 1: Separate Configuration Package

This approach keeps your custom modules separate from the Forthic installation:

```bash
# Install Forthic
pip install forthic[grpc]

# Install your custom modules package
pip install my-company-forthic-modules

# Configuration managed separately
python -m forthic.grpc.server --modules-config /etc/forthic/modules.yaml
```

**Directory structure:**
```
/etc/forthic/
  modules.yaml          # Configuration file

/opt/my-company/
  my_modules/
    __init__.py
    sales_module.py     # Custom module
    analytics_module.py # Custom module
```

**Configuration file:**
```yaml
# /etc/forthic/modules.yaml
modules:
  - name: sales
    import_path: my_modules.sales_module:SalesModule
    optional: false

  - name: analytics
    import_path: my_modules.analytics_module:AnalyticsModule
    optional: false
```

### Option 2: Custom Server Package

Create a custom server that pre-configures module loading:

```python
# my_company_server/server.py
from forthic.grpc.server import serve
import os

def main():
    config_path = os.getenv(
        'COMPANY_MODULES_CONFIG',
        '/etc/company/forthic-modules.yaml'
    )
    serve(port=50051, modules_config=config_path)

if __name__ == "__main__":
    main()
```

**Package setup:**
```python
# setup.py or pyproject.toml
[project.scripts]
company-forthic-server = "my_company_server.server:main"
```

Then deploy:
```bash
pip install my-company-forthic-server
company-forthic-server
```

### Option 3: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10

# Install Forthic
RUN pip install forthic[grpc]

# Install custom modules
COPY ./my_modules /app/my_modules
COPY ./modules.yaml /app/modules.yaml

WORKDIR /app
EXPOSE 50051

CMD ["python", "-m", "forthic.grpc.server", "--modules-config", "modules.yaml"]
```

## Creating Custom Modules

### Basic Module Structure

```python
from forthic.decorators import DecoratedModule, Word

class MyModule(DecoratedModule):
    def __init__(self):
        super().__init__("mymodule")  # Module name

    @Word("( a b -- c )", "Description of word")
    async def MY_WORD(self, a, b):
        """
        Docstring for the word.
        This appears in module documentation.
        """
        # Implementation
        return a + b
```

### Word Decorator

The `@Word` decorator marks methods as Forthic words:

```python
@Word("( input1 input2 -- output )", "Human-readable description")
async def WORD_NAME(self, param1, param2, ...):
    # Stack items are passed as parameters (top-to-bottom)
    # Return value is pushed to stack
    return result
```

**Stack effect notation:**
- `( a b -- c )` means: takes 2 items (a, b), returns 1 item (c)
- `( -- )` means: takes nothing, returns nothing
- `( item -- item item )` means: duplicates top stack item

### DirectWord Decorator

For advanced use cases where you need direct interpreter access:

```python
from forthic.decorators import DirectWord

@DirectWord("( n forthic -- results )", "Execute Forthic code n times")
async def REPEAT(self, interp):
    """
    DirectWords receive the interpreter instance.
    They manage the stack directly.
    """
    forthic_code = interp.stack_pop()
    n = interp.stack_pop()

    results = []
    for i in range(n):
        interp.stack_push(i)
        await interp.run(forthic_code)
        results.append(interp.stack_pop())

    interp.stack_push(results)
```

Use DirectWords when you need to:
- Execute Forthic code dynamically
- Manipulate the stack in complex ways
- Access interpreter state
- Implement control flow

### Module with Multiple Categories

```python
class DataModule(DecoratedModule):
    def __init__(self):
        super().__init__("data")

    # === Database Operations ===

    @Word("( query -- results )", "Execute SQL query")
    async def SQL_QUERY(self, query: str):
        # Implementation
        return results

    @Word("( table data -- )", "Insert data into table")
    async def INSERT(self, table: str, data: dict):
        # Implementation
        pass

    # === File Operations ===

    @Word("( path -- content )", "Read file content")
    async def READ_FILE(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()

    @Word("( path content -- )", "Write content to file")
    async def WRITE_FILE(self, path: str, content: str):
        with open(path, 'w') as f:
            f.write(content)
```

## Server Command Line Options

```bash
python -m forthic.grpc.server [OPTIONS]

Options:
  --port PORT                  Port to listen on (default: 50051)
  --modules-config PATH        Path to modules configuration YAML file
  --host HOST                  Host to bind to (default: [::] for all interfaces)
  -h, --help                   Show help message

Environment Variables:
  FORTHIC_MODULES_CONFIG       Path to modules config (if --modules-config not provided)
```

### Examples

```bash
# Start with default modules (pandas if available)
python -m forthic.grpc.server

# Start with custom module configuration
python -m forthic.grpc.server --modules-config /path/to/modules.yaml

# Start on custom port
python -m forthic.grpc.server --port 50052

# Combine options
python -m forthic.grpc.server --port 50052 --modules-config modules.yaml

# Use environment variable
export FORTHIC_MODULES_CONFIG=/etc/forthic/modules.yaml
python -m forthic.grpc.server
```

## Module Discovery from TypeScript

Once modules are loaded on the Python server, TypeScript can discover and use them:

```typescript
import { GrpcClient } from '@forthix/forthic-ts/grpc';

const client = new GrpcClient('localhost:50051');

// List all available modules
const modules = await client.listModules();
for (const mod of modules) {
    console.log(`Module: ${mod.name}`);
    console.log(`  Description: ${mod.description}`);
    console.log(`  Word count: ${mod.word_count}`);
    console.log(`  Runtime-specific: ${mod.runtime_specific}`);
}

// Get detailed info about a specific module
const moduleInfo = await client.getModuleInfo('example');
console.log(`Module: ${moduleInfo.name}`);
console.log(`Description: ${moduleInfo.description}`);
console.log('Words:');
for (const word of moduleInfo.words) {
    console.log(`  ${word.name} ${word.stack_effect}`);
    console.log(`    ${word.description}`);
}

// Execute words from the module
const result = await client.executeWord('MULTIPLY', [5, 3]);
console.log(result); // [15]
```

## Troubleshooting

### Module Not Loading

**Problem:** Module doesn't appear in `listModules()` output.

**Solutions:**
1. Check server startup logs for errors:
   ```bash
   python -u -m forthic.grpc.server --modules-config modules.yaml
   ```

2. Verify import path is correct:
   ```python
   # Test import manually
   from examples.dynamic_module_example import ExampleModule
   mod = ExampleModule()
   print(mod.name)
   ```

3. Ensure module directory has `__init__.py`:
   ```bash
   ls examples/__init__.py
   ```

4. Check Python path includes module location:
   ```python
   import sys
   print(sys.path)
   ```

### Optional vs Required Modules

**Problem:** Server fails to start due to missing optional module.

**Solution:** Set `optional: true` in configuration:

```yaml
modules:
  - name: experimental
    import_path: experimental.module:ExperimentalModule
    optional: true  # Won't fail server if missing
```

### Import Errors

**Problem:** `ModuleNotFoundError` or `AttributeError`.

**Solutions:**
1. Verify package is installed:
   ```bash
   pip list | grep <package-name>
   ```

2. Check class name matches import path:
   ```yaml
   # If file is: my_modules/example.py
   # And class is: class MyExample(DecoratedModule)
   import_path: my_modules.example:MyExample  # Correct
   import_path: my_modules.example:MyModule   # Wrong - class doesn't exist
   ```

3. Ensure proper Python package structure:
   ```
   my_modules/
     __init__.py          # Required!
     example.py
   ```

## See Also

- [Creating Custom Modules Guide](./custom-modules.md)
- [Example Module](../examples/dynamic_module_example.py)
- [Configuration Examples](../examples/example_modules_config.yaml)
- [Integration Tests](../../forthic/integration-tests/test_phase10.5.ts)
- [gRPC Multi-Runtime Architecture](../../GRPC_MULTIRUNTIME_PLAN.md)
