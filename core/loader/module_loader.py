# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from __future__ import annotations

from typing import TYPE_CHECKING, List
from types import ModuleType

from importlib import import_module
from modulefinder import ModuleFinder
import os
from os.path import join, splitext
import pickle

from .addon_module import Modules

from ...config import Config

from .module_finder import ModuleFinder
from .cache_loader import CacheLoader

if TYPE_CHECKING:
    from manager.addon_manager import AddonManager

class ModuleLoader:
    """Retrieve modules and classes."""
    def __init__(self, addon: AddonManager) -> None:
        self.ADDON = addon
        #self.__is_system_path_added = self.__add_addon_to_system_path()

    def load(self) -> Modules:
        """Retrieve modules and addon classes."""
        if Config().data["is_debug_mode"]:
            return self.__find_modules()
        else:
            modules = CacheLoader(self).load()
            if modules is None:
                return self.__find_modules()
            else:
                return modules

    def path_to_module_path(self, path: str) -> str:
        """Convert absolute paths to module paths."""
        return self.ADDON.SYS_PATH_TO_ADDON + splitext(path.replace(self.ADDON.PATH_TO_SCRIPTS_FOLDER, ''))[0].replace(os.sep, '.')

    def path_to_module(self, path: str) -> ModuleType:
        """Obtains a ModuleType object from the module path."""
        return import_module(self.path_to_module_path(path))

    def __find_modules(self) -> Modules:
        """Scan modules and addon classes from the file system."""
        disabled:         List[str] = Config().data.get("disabled", [])
        priorities:       List[str] = Config().data.get("priorities", [])
        exclude_patterns: List[str] = Config().data.get("exclude_patterns", [])

        modules = ModuleFinder(self).load(disabled, priorities, exclude_patterns)

        self.__write_modules_data(modules)

        return modules

    def __write_modules_data(self, modules: Modules) -> None:
        """Cache module and addon class information in a file."""
        with open(join(self.ADDON.PATH_TO_DATA, "modules.pkl"), "wb") as file:
            pickle.dump(modules, file)
