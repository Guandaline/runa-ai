# nala/athomic/base/module_loader.py
import importlib.util
from pathlib import Path
from typing import Any, Optional

from .exceptions import ModuleLoadError


def load_module_from_path(path: Path) -> Optional[Any]:
    """Dynamically loads a Python module from a file path.

    Args:
        path: The `Path` object pointing to the Python script to load.

    Returns:
        The loaded module object.

    Raises:
        ModuleLoadError: If the module specification cannot be created or loaded.
    """
    try:
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            raise ModuleLoadError(f"Could not create module spec for {path.name}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ModuleLoadError(f"Failed to load module from path: {path}") from e
