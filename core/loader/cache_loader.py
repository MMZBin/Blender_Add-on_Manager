# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from __future__ import annotations
import pickle
from typing import TYPE_CHECKING

from os.path import join

from .addon_module import Modules


if TYPE_CHECKING:
    from .module_loader import ModuleLoader

class CacheLoader:
    """Load modules and addon classes from cache."""
    def __init__(self, loader: ModuleLoader) -> None:
        self.__loader = loader

    def load(self) -> Modules | None:
        """Load modules and addon classes. Returns None if the cache does not exist."""
        try:
            with open(join(self.__loader.ADDON.PATH_TO_DATA, "modules.pkl"), "rb") as file:
                modules = pickle.load(file)
        except FileNotFoundError:
            return None

        return modules
