# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Dict, List, Self

from bpy.types import bpy_struct

def ispackage(module_type: ModuleType) -> bool:
    return hasattr(module_type, '__path__')

@dataclass
class AddonClass:
    """BPY class"""
    cls: type[bpy_struct]

    is_disabled: bool = False
    priority: int | float = float('inf')

@dataclass
class Module:
    """List of module and the classes they contain"""
    module: ModuleType
    classes: List[AddonClass] | None = None

    is_disabled: bool              = False
    priority: int | float          = float('inf')

@dataclass
class Modules:
    """List of all modules and classes included in the add-on"""
    modules: List[ModuleType]
    classes: List[type[bpy_struct]]

    @classmethod
    def from_list_of_modules(cls, addon_modules: List[Module]) -> Self:
        """Generates a Modules object from a list of Module objects."""
        modules: List[ModuleType] = []
        classes: List[type[bpy_struct]] = []

        for mdl in addon_modules:
            if mdl.is_disabled:
                continue

            if mdl.classes is None:
                continue

            modules.append(mdl.module)

            classes.extend([op.cls for op in mdl.classes if not op.is_disabled])

        return cls(modules, classes)


    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        state['modules'] = [mdl.__name__ for mdl in state['modules']]
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        state['modules'] = list(map(import_module, state['modules']))
        self.__dict__.update(state)
