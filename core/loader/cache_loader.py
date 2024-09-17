# This program is distributed under the MIT License.
# See the LICENSE file for details.

# pyright: reportUnknownVariableType = false
# pyright: reportUnknownArgumentType = false

from __future__ import annotations

from typing import List, TYPE_CHECKING

from os.path import exists
from importlib import import_module

import json

from ..utils.gen_msg import MsgType, gen_msg

from .addon_module import AddonModule

if TYPE_CHECKING:
    from .proc_loader import ProcLoader

class CacheLoader:
    def __init__(self, loader: ProcLoader) -> None:
        """Load add-on classes and modules from cache."""
        self.__loader = loader

    def load(self, path: str) -> List[AddonModule]:
        """Load add-on classes and modules from cache."""
        if not exists(path):
            raise FileNotFoundError(
                gen_msg(
                    CacheLoader,
                    MsgType.CRITICAL,
                    "The cache for the add-on's module has not yet been created.\nPlease temporarily enable debug mode for the add-on and restart.",
                )
            )

        module_and_classes: List[AddonModule] = []
        with open(path, "r", encoding="utf-8") as cache:
            cache = json.load(cache)

            for entry in cache:
                module_name = entry["module"]
                class_names = entry["classes"]

                module = import_module(module_name)
                classes = [self.__loader.add_attribute(getattr(module, cls_name)) for cls_name in class_names]

                module_and_classes.append(AddonModule(module, classes))

        return module_and_classes
