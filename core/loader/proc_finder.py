# This program is distributed under the MIT License.
# See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false

# REVIEW: Lack of verification of priority-setting algorithms.

from __future__ import annotations

from typing import Iterable, List, TYPE_CHECKING
from types import ModuleType

import os
from os import walk
from os.path import dirname, basename, splitext, join
from importlib import import_module

from inspect import getmembers, ismodule, isclass

from ..utils.gen_msg import MsgType, gen_msg

from .addon_module import AddonModule, Plugins

if TYPE_CHECKING:
    from .proc_loader import ProcLoader

class ProcFinder:
    """Load add-on modules and classes."""

    def __init__(self, loader: ProcLoader) -> None:
        self.__loader = loader

    def load(
        self,
        dir_priorities: List[str] | None,
        exclude_modules: List[str] | None,
        exclude_when_not_debugging: List[str] | None,
    ) -> Plugins:
        """Load modules and add-on classes.

        Args:
            dir_priorities (List[str], optional): Specifies the order in which root-level directories are read.. Defaults to None.
            exclude_modules (List[str], optional): Specify folders not to be read. Defaults to None.
            exclude_when_not_debugging (List[str], optional): Specify folders to exclude when not in debug mode. Defaults to None.

        Returns:
            Plugins: List of modules and add-on classes.
        """

        if exclude_modules is None:
            exclude_modules = []

        exclude_modules = exclude_modules + [basename(dirname(dirname(__file__)))]
        if not self.__loader.IS_DEBUG_MODE and exclude_when_not_debugging is not None:
            exclude_modules += exclude_when_not_debugging

        exclude_modules = [
            (self.__loader.ADDON_NAME + "." + dir) for dir in exclude_modules
        ]  # 無視するモジュールをモジュールパスの形にする

        modules_path_with_pr: dict[str, int] = {}

        for root, _, files in walk(join(self.__loader.PATH, self.__loader.ADDON_NAME)):
            if basename(root).startswith("."):
                continue

            root_mdl_path = root.lstrip(self.__loader.PATH + os.sep).replace(os.sep, ".")

            dir_priority = -1

            if dir_priorities is not None:
                for i, path in enumerate(dir_priorities):
                    if root_mdl_path.startswith(path):
                        dir_priority = i

            root_mdl_path += "."

            for file in [f for f in files if f.endswith(".py")]:
                mdl_path = root_mdl_path + splitext(file)[0]

                modules_path_with_pr[mdl_path] = dir_priority

        modules_path = [
            mdl[0]
            for mdl in sorted(
                modules_path_with_pr.items(),
                key=lambda path: float("inf") if path[1] < 0 else path[1]
            )
        ]

        modules = list(map(import_module, modules_path))
        if not self.__loader.IS_DEBUG_MODE:
            modules = [mdl for mdl in modules if not mdl.__package__.endswith("debug")]  # type: ignore

        exclude_modules += self.__load_init_attr(modules)

        modules = [
            mdl
            for mdl in modules
            if mdl.__file__ and not self.__abs_to_mdl_path(mdl.__file__ + ".").startswith(tuple(exclude_modules))
        ] # 無効なモジュールを除外する

        addon_modules = self.__load_classes(modules)
        addon_modules =  sorted(
            addon_modules,
            key=lambda mdl: (float("inf")if getattr(mdl.module, "ADDON_MODULE_PRIORITY", -1) == -1 else mdl.module.ADDON_MODULE_PRIORITY)
        )

        return Plugins.from_addon_modules(addon_modules)

    def __load_init_attr(self, modules: List[ModuleType]) -> List[str]:
        disabled_modules: List[str] = []

        for init in [mdl for mdl in modules if mdl.__file__ and mdl.__file__.endswith("__init__.py")]:
            modules.remove(init)

            if init.__package__ is None:
                continue

            package_path = init.__package__ + "."

            if hasattr(init, "disable"):
                if not issubclass(type(init.disable), Iterable):
                    raise TypeError(
                        gen_msg(ProcLoader, MsgType.CRITICAL, f'Attribute "disable" of module "{init}" is not iterable.')
                    )
                for mdl in init.disable:
                    disabled_modules.append(package_path + mdl + ".")

            self.__set_module_priority(init)

        return disabled_modules

    def __abs_to_mdl_path(self, path: str) -> str:
        return path.lstrip(self.__loader.PATH).replace(os.sep, ".")

    def __load_classes(
        self, modules: List[ModuleType]
    ) -> List[AddonModule]:
        """Reads the add-on class."""
        addon_modules: List[AddonModule] = []

        for mdl in modules:
            classes = [cls[1] for cls in getmembers(mdl, isclass) if issubclass(cls[1], tuple(self.__loader.TARGET_CLASSES)) and not cls[1] in self.__loader.TARGET_CLASSES and not getattr(cls, "addon_proc_disabled", False)]
            # for cls in classes:
            #     self.__loader.add_attribute(cls)
            addon_modules.append(AddonModule(mdl, sorted(classes, key=lambda cls: float("inf") if getattr(cls, "addon_proc_priority", -1) == -1 else cls.addon_proc_priority))) # type: ignore

        return addon_modules

    def __set_module_priority(self, init_module: ModuleType) -> None:
        """Set module priority recursively."""

        priority_count: int = 0

        def set_priority(package: ModuleType) -> None:
            nonlocal priority_count

            for mdl in getmembers(package, ismodule):
                if hasattr(mdl[1], "__path__"):
                    try:
                        _set_module_priority(import_module(mdl[1].__file__.lstrip(self.__loader.PATH).replace(os.sep, ".") + "." + "__init__"))  # type: ignore
                    except ModuleNotFoundError:
                        set_priority(mdl[1])
                mdl[1].ADDON_MODULE_PRIORITY = priority_count
                priority_count += 1

        def _set_module_priority(init: ModuleType) -> None:
            nonlocal priority_count

            if getattr(init, "ADDON_INIT_LOADED", False):
                return
            init.ADDON_INIT_LOADED = True

            if not hasattr(init, "priority"):
                return
            if not issubclass(type(init.priority), Iterable):
                raise TypeError(
                    gen_msg(ProcLoader, MsgType.CRITICAL, f'Attribute "priority" of module "{init}" is not iterable.')
                )

            if init.__package__ is None:
                return
            package_path = init.__package__ + "."

            for mdl_path in init.priority:
                priority_path = package_path + mdl_path
                module = import_module(priority_path)
                # 対象がパッケージだったら__init__モジュールから優先度を設定する
                if hasattr(module, "__path__"):
                    try:
                        _set_module_priority(import_module(priority_path + "." + "__init__"))
                    except ModuleNotFoundError:
                        # __init__モジュールがなければ登録順に優先度を設定する
                        set_priority(module)
                else:
                    module.ADDON_MODULE_PRIORITY = priority_count

                priority_count += 1

        _set_module_priority(init_module)

        return
