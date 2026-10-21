"""Emitter base class and the auto-discovering target registry."""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod


class Emitter(ABC):
    """One harness target. `render` maps repo-relative path to file text."""

    target: str = ""

    @abstractmethod
    def render(self, sources) -> dict[str, str]:
        """Return repo-relative path -> file text."""


def registry() -> dict[str, Emitter]:
    """Instantiate every Emitter subclass found in a module of harness.targets."""
    from harness import targets

    found: dict[str, Emitter] = {}
    for info in sorted(pkgutil.iter_modules(targets.__path__), key=lambda i: i.name):
        mod = importlib.import_module(f"{targets.__name__}.{info.name}")
        for obj in vars(mod).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, Emitter)
                and obj is not Emitter
                and obj.__module__ == mod.__name__
                and obj.target
            ):
                found[obj.target] = obj()
    return found
