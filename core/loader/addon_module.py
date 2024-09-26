# This program is distributed under the MIT License.
# See the LICENSE file for details.

from __future__ import annotations

from typing import Any, List
from types import ModuleType

from dataclasses import dataclass

from importlib import import_module

@dataclass
class AddonModule:
    """Add-on module and classes."""
    module: ModuleType
    classes: List[type]

@dataclass
class Plugins:
    """All of add-on modules and classes."""
    modules: List[ModuleType]
    classes: List[type]

    @staticmethod
    def from_addon_modules(addon_modules: List[AddonModule]) -> Plugins:
        """Generates a Plugins object from a list of AddonModule objects."""
        modules = [mdl.module for mdl in addon_modules]
        classes = [mdl.classes for mdl in addon_modules]
        classes = [cls for cls_list in classes for cls in cls_list]
        return Plugins(modules, classes)

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state['modules'] = [mdl.__name__ for mdl in state['modules']]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        state['modules'] = list(map(import_module, state['modules']))
        self.__dict__.update(state)
