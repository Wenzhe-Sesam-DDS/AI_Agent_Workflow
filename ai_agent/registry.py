"""
Auto-discovery utilities — scan a package for subclasses of a base class.

This lets users drop a new tool/skill/agent file into the right folder
without editing any __init__.py registry.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TypeVar

T = TypeVar("T")


def discover_subclasses(package_name: str, base_cls: type[T]) -> list[T]:
    """Import every module under ``package_name`` and instantiate every
    concrete subclass of ``base_cls`` found.

    Skips the base class itself and any class whose name starts with ``_``.
    """
    package = importlib.import_module(package_name)
    instances: list[T] = []
    seen: set[type] = set()

    for _finder, modname, _ispkg in pkgutil.iter_modules(package.__path__):
        if modname.startswith("_") or modname == "base_" + base_cls.__name__.lower().replace("base", ""):
            continue
        module = importlib.import_module(f"{package_name}.{modname}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, base_cls)
                and attr is not base_cls
                and attr not in seen
            ):
                seen.add(attr)
                try:
                    instances.append(attr())
                except TypeError:
                    # Class requires constructor args — skip auto-instantiation.
                    continue
    return instances
