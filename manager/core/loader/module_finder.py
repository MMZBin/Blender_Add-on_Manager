# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false
# pyright: reportUnknownArgumentType = false

from __future__ import annotations

from importlib import import_module
import inspect
from typing import TYPE_CHECKING, List

from pathlib import Path

from bpy.types import bpy_struct

from.addon_module import AddonClass, Module, Modules
from ... import utils

if TYPE_CHECKING:
    from manager.core.loader.cache_loader import ModuleLoader

class ModuleFinder:
    """Scan modules and addon classes from the file system."""
    def __init__(self, loader: ModuleLoader) -> None:
        self.__loader = loader

    def load(self, disabled: List[str], priorities: List[str], exclude_patterns: List[str]) -> Modules:
        """Scan modules and addon classes."""
        exclude_patterns += ('__pycache__', '__init__')

        for i, path in enumerate(disabled):
            if not path.endswith('.'):
                path += '.'

            disabled[i] = self.__loader.ADDON.SYS_PATH_TO_ADDON + '.' + self.__loader.ADDON.ADDON_FOLDER_NAME + '.' + 'modules.' + path
        for i, path in enumerate(priorities):
            if not path.endswith('.'):
                path += '.'

            priorities[i] = self.__loader.ADDON.SYS_PATH_TO_ADDON + '.' + self.__loader.ADDON.ADDON_FOLDER_NAME + '.' + 'modules.' + path

        modules: List[Module] = []

        for path in Path(self.__loader.ADDON.PATH_TO_MODULES).rglob("*.py"):
            file = str(path)
            if not file.endswith('.py'):
                continue
            module_path: str = self.__loader.path_to_module_path(file)

            if any(path in module_path for path in exclude_patterns):
                continue

            module: Module = Module(import_module(module_path))

            module.is_disabled = module_path.startswith(tuple(disabled))

            modules.append(module)

        def sort_by_priority(module: Module) -> int | float:
            # prioritiesリストの中で最初にモジュールパスの先頭と一致したインデックスを返す
            # 例: priorities=[module.a.b] module.module.__name__=module.a.b.c <- 引っかかる
            for i, pr in enumerate(priorities):
                if not module.module.__name__.startswith(pr):
                    continue

                return i

            return float('inf') # なければ無限(最大)

        modules.sort(key=sort_by_priority)

        # 各モジュールに含まれるオペレーターを取得する
        for mdl in modules:
            mdl.classes = self.find_classes_from_modules(mdl)
            mdl.classes.sort(key=lambda op: op.priority)

        self.__print_log(modules, disabled, priorities)


        return Modules.from_list_of_modules(modules)

    def __print_log(self, modules: List[Module], disabled: List[str], priorities: List[str]) -> None:
        """Outputs the reading result."""
        utils.print_with_indent(0, utils.generate_addon_message(f"information on loading {self.__loader.ADDON.ADDON_FOLDER_NAME} :"))

        # print disabled modules
        utils.print_with_indent(1, f"disabled modules : {'[N/A]' if len(disabled) == 0 else ''}")
        for mdl in disabled:
            utils.print_with_indent(2, mdl.split('modules.')[1].rstrip('.'))
        print('\n')

        # print modules priority
        utils.print_with_indent(1, f"load order       : {'[N/A]' if len(priorities) == 0 else ''}")
        for mdl in priorities:
            utils.print_with_indent(2, mdl.split('modules.')[1].rstrip('.'))
        print('\n')

        # print loaded modules
        utils.print_with_indent(1, "loaded modules   :")
        for mdl in modules:
            utils.print_with_indent(2, f"{'[disabled]' if mdl.is_disabled else ''} {mdl.module.__name__.split('modules.')[1]}")

            if mdl.classes is None or len(mdl.classes) == 0:
                utils.print_with_indent(3, "classes  : [N/A]")
                continue

            utils.print_with_indent(3, "classes  :")
            for cls in mdl.classes:
                utils.print_with_indent(4, f"{'[disabled]' if mdl.is_disabled else ''} {cls.cls.__name__.split('modules.')[0]}")

        print(f"{'=' * 50}")

    @staticmethod
    def find_classes_from_modules(module: Module) -> List[AddonClass]:
        """Retrieve all addon classes in the module."""
        classes: List[AddonClass] = []

        for _, cls in inspect.getmembers(module.module, inspect.isclass):
            # クラスがこのモジュール内で定義されたものではないかアドオンの機能ではない場合除外する
            if cls.__module__ != module.module.__name__ or not issubclass(cls, bpy_struct):
                continue

            if hasattr(cls, '_addon_manager_metadata') and utils.isinstance(cls._addon_manager_metadata, AddonClass):
                classes.append(cls._addon_manager_metadata)
                continue

            classes.append(AddonClass(cls))

        return classes
