"""
Module loader for Forthic gRPC server
Loads modules from configuration file
"""
import importlib
from typing import Dict, Any
from pathlib import Path
import yaml


class ModuleLoadError(Exception):
    """Raised when a required module fails to load"""
    pass


def load_modules_from_config(config_path: str | Path) -> Dict[str, Any]:
    """
    Load Forthic modules from YAML configuration file.

    Args:
        config_path: Path to modules configuration YAML file

    Returns:
        Dictionary of {module_name: module_instance}

    Raises:
        ModuleLoadError: If a required module fails to load
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Module config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if not config or 'modules' not in config:
        print(f"[MODULE_LOADER] No modules defined in {config_path}")
        return {}

    loaded_modules = {}

    for mod_config in config['modules']:
        module_name = mod_config['name']
        import_path = mod_config['import_path']
        optional = mod_config.get('optional', False)
        description = mod_config.get('description', '')

        try:
            # Parse import path: "package.module:ClassName"
            if ':' not in import_path:
                raise ValueError(
                    f"Invalid import_path '{import_path}'. "
                    f"Expected format: 'module.path:ClassName'"
                )

            module_path, class_name = import_path.split(':', 1)

            print(f"[MODULE_LOADER] Loading module '{module_name}' from {import_path}")

            # Import the module
            module = importlib.import_module(module_path)

            # Get the class
            ModuleClass = getattr(module, class_name)

            # Instantiate the module
            mod_instance = ModuleClass()

            loaded_modules[module_name] = mod_instance

            print(f"[MODULE_LOADER] ✓ Loaded '{module_name}' successfully")
            if description:
                print(f"[MODULE_LOADER]   Description: {description}")

        except Exception as e:
            error_msg = f"Failed to load module '{module_name}': {e}"

            if optional:
                print(f"[MODULE_LOADER] ⚠ Optional module '{module_name}' not available: {e}")
            else:
                print(f"[MODULE_LOADER] ✗ {error_msg}")
                raise ModuleLoadError(error_msg) from e

    print(f"[MODULE_LOADER] Loaded {len(loaded_modules)} module(s)")
    return loaded_modules


def load_modules_from_directory(plugin_dir: str | Path) -> Dict[str, Any]:
    """
    Auto-discover and load modules from a plugin directory.

    Scans for Python files containing DecoratedModule subclasses.

    Args:
        plugin_dir: Directory to scan for module files

    Returns:
        Dictionary of {module_name: module_instance}
    """
    plugin_dir = Path(plugin_dir)

    if not plugin_dir.exists():
        print(f"[MODULE_LOADER] Plugin directory not found: {plugin_dir}")
        return {}

    print(f"[MODULE_LOADER] Scanning plugin directory: {plugin_dir}")

    # TODO: Implement auto-discovery
    # This would scan .py files and find DecoratedModule subclasses
    # For now, return empty dict (future enhancement)

    return {}
