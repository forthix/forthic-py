# Forthic Python Scripts

This directory contains utility scripts for the Forthic Python implementation.

## Documentation Generation

### generate_docs.py

Automatically generates comprehensive markdown documentation for all Forthic modules.

**Features:**
- Dynamically discovers all `DecoratedModule` subclasses
- Extracts documentation from `@Word` and `@DirectWord` decorators
- Generates index and individual module documentation files
- Includes stack effects, descriptions, categories, options, and examples

**Usage:**

```bash
# Run directly
python3 scripts/generate_docs.py

# Or use the installed command (after pip install)
forthic-generate-docs
```

**Output:**
- `docs/index.md` - Main index with module overview
- `docs/modules/*.md` - Individual module documentation files

**What gets documented:**
- Word names and stack effects
- Word descriptions
- Module-level metadata (categories, options, examples)
- Automatically sorted alphabetically

The script will automatically find all modules that inherit from `DecoratedModule`, so no manual configuration is needed when adding new modules!
