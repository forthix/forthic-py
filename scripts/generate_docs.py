#!/usr/bin/env python3
"""Documentation Generator for Forthic Modules.

Generates markdown documentation for all modules by extracting
metadata from @Word and @DirectWord decorators.

This script dynamically discovers all DecoratedModule subclasses
and generates comprehensive documentation for each.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from forthic.decorators.word import DecoratedModule


class ModuleDoc:
    """Container for module documentation."""

    def __init__(
        self, name: str, words: list[dict[str, str]], metadata: dict[str, Any] | None = None
    ):
        self.name = name
        self.words = words
        self.metadata = metadata


def discover_modules() -> list[type[DecoratedModule]]:
    """Dynamically discover all DecoratedModule subclasses.

    Returns:
        List of DecoratedModule subclasses
    """
    # Import the modules package to ensure all modules are loaded
    import forthic.modules  # noqa: F401

    # Get all subclasses recursively
    def get_all_subclasses(cls: type) -> set[type]:
        all_subclasses = set()
        for subclass in cls.__subclasses__():
            all_subclasses.add(subclass)
            all_subclasses.update(get_all_subclasses(subclass))
        return all_subclasses

    subclasses = get_all_subclasses(DecoratedModule)
    return sorted(subclasses, key=lambda cls: cls.__name__)


def get_module_description(module_name: str) -> str:
    """Get a brief description for a module.

    Args:
        module_name: Name of the module

    Returns:
        Brief description string
    """
    descriptions = {
        "array": "Array and collection operations",
        "boolean": "Comparison, logic, and membership operations",
        "core": "Core language operations and control flow",
        "datetime": "Date and time operations",
        "json": "JSON parsing and serialization",
        "math": "Mathematical operations and utilities",
        "record": "Record (object/dictionary) manipulation",
        "string": "String manipulation and processing",
    }
    return descriptions.get(module_name, "Module operations")


def generate_index_markdown(module_docs: list[ModuleDoc]) -> str:
    """Generate the main index markdown file.

    Args:
        module_docs: List of module documentation objects

    Returns:
        Markdown string for the index file
    """
    markdown = "# Forthic Module Documentation\n\n"
    markdown += f"Generated: {datetime.now().isoformat()}\n\n"

    total_words = sum(len(mod.words) for mod in module_docs)
    markdown += f"**{len(module_docs)} modules** with **{total_words} words** total\n\n"

    markdown += "## Modules\n\n"
    markdown += "| Module | Words | Description |\n"
    markdown += "|--------|-------|-------------|\n"

    for mod in module_docs:
        description = get_module_description(mod.name)
        if mod.metadata and mod.metadata.get("description"):
            # Use the first sentence of the module's description if available
            desc_text = mod.metadata["description"].split(".")[0].strip()
            if desc_text:
                description = desc_text
        markdown += f"| [{mod.name}](./modules/{mod.name}.md) | {len(mod.words)} | {description} |\n"

    markdown += "\n## Quick Links\n\n"
    for mod in module_docs:
        word_names = [w["name"] for w in mod.words][:5]
        markdown += f"- **[{mod.name}](./modules/{mod.name}.md)**: {', '.join(word_names)}"
        if len(mod.words) > 5:
            markdown += f", ... ({len(mod.words) - 5} more)"
        markdown += "\n"

    return markdown


def generate_module_markdown(module_doc: ModuleDoc) -> str:
    """Generate markdown documentation for a single module.

    Args:
        module_doc: Module documentation object

    Returns:
        Markdown string for the module file
    """
    markdown = f"# {module_doc.name} Module\n\n"
    markdown += "[← Back to Index](../index.md)\n\n"

    # Add module description if available
    if module_doc.metadata and module_doc.metadata.get("description"):
        markdown += f"{module_doc.metadata['description']}\n\n"

    markdown += f"**{len(module_doc.words)} words**\n\n"

    # Add categories section if available
    if module_doc.metadata and module_doc.metadata.get("categories"):
        categories = module_doc.metadata["categories"]
        if categories:
            markdown += "## Categories\n\n"
            for cat in categories:
                markdown += f"- **{cat['name']}**: {cat['words']}\n"
            markdown += "\n"

    # Add options section if available
    if module_doc.metadata and module_doc.metadata.get("optionsInfo"):
        markdown += "## Options\n\n"
        markdown += f"{module_doc.metadata['optionsInfo']}\n\n"

    # Add examples section if available
    if module_doc.metadata and module_doc.metadata.get("examples"):
        examples = module_doc.metadata["examples"]
        if examples:
            markdown += "## Examples\n\n"
            markdown += "```forthic\n"
            for example in examples:
                markdown += f"{example}\n"
            markdown += "```\n\n"

    markdown += "## Words\n\n"

    for word in module_doc.words:
        markdown += f"### {word['name']}\n\n"
        markdown += f"**Stack Effect:** `{word['stackEffect']}`\n\n"
        if word.get("description"):
            markdown += f"{word['description']}\n\n"
        markdown += "---\n\n"

    markdown += "\n[← Back to Index](../index.md)\n"

    return markdown


def generate_docs() -> list[ModuleDoc]:
    """Extract documentation from all discovered modules.

    Returns:
        List of ModuleDoc objects containing documentation
    """
    module_docs: list[ModuleDoc] = []

    # Discover all DecoratedModule subclasses
    module_classes = discover_modules()

    print(f"Discovered {len(module_classes)} module classes")

    # Extract documentation from each module
    for module_class in module_classes:
        try:
            # Instantiate the module
            module = module_class()
            words = module.get_word_docs()
            metadata = module.get_module_metadata()

            if words:
                # Sort words alphabetically
                words_sorted = sorted(words, key=lambda w: w["name"])
                module_docs.append(
                    ModuleDoc(name=module.get_name(), words=words_sorted, metadata=metadata)
                )
                print(f"  ✓ {module.get_name()} ({len(words)} words)")
            else:
                print(f"  ⚠ {module_class.__name__} has no documented words")
        except Exception as e:
            print(f"  ✗ Error processing {module_class.__name__}: {e}")

    # Sort modules by name
    module_docs.sort(key=lambda m: m.name)

    return module_docs


def main() -> None:
    """Main entry point for documentation generation."""
    try:
        print("Generating Forthic module documentation...\n")

        module_docs = generate_docs()

        if not module_docs:
            print("\n⚠ No modules with documentation found!")
            sys.exit(1)

        # Ensure docs directories exist
        script_dir = Path(__file__).parent
        docs_dir = script_dir.parent / "docs"
        modules_dir = docs_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write index file
        index_markdown = generate_index_markdown(module_docs)
        index_path = docs_dir / "index.md"
        index_path.write_text(index_markdown, encoding="utf-8")
        print(f"\n✓ Index generated: {index_path}")

        # Generate and write individual module files
        total_size = len(index_markdown)
        for module_doc in module_docs:
            module_markdown = generate_module_markdown(module_doc)
            module_path = modules_dir / f"{module_doc.name}.md"
            module_path.write_text(module_markdown, encoding="utf-8")
            total_size += len(module_markdown)
            print(f"  ✓ {module_doc.name}.md ({len(module_doc.words)} words)")

        print(f"\n✓ Documentation complete!")
        print(f"  Total files: {len(module_docs) + 1}")
        print(f"  Total size: {total_size / 1024:.2f} KB")

    except Exception as error:
        print(f"\n✗ Error generating documentation: {error}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
