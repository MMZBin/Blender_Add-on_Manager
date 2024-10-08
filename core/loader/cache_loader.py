# This program is distributed under the MIT License.
# See the LICENSE file for details.

# pyright: reportUnknownVariableType = false
# pyright: reportUnknownArgumentType = false

from __future__ import annotations

from typing import TYPE_CHECKING

from os.path import exists

import pickle

from ..utils.gen_msg import MsgType, gen_msg

from .addon_module import Plugins

if TYPE_CHECKING:
    from .proc_loader import ProcLoader

class CacheLoader:
    def __init__(self, loader: ProcLoader) -> None:
        """Load add-on classes and modules from cache."""
        self.__loader = loader

    def load(self) -> Plugins:
        """Load add-on classes and modules from cache."""
        path = self.__loader.CACHE_PATH

        if not exists(path):
            raise FileNotFoundError(
                gen_msg(
                    CacheLoader,
                    MsgType.CRITICAL,
                    f"Cache file is not in {path}. \nMake sure the path is correct or create a cache file with debug mode enabled."
                )
            )

        with open(path, "rb") as cache:
            plugins = pickle.load(cache)

        return plugins
