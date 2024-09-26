# This program is distributed under the MIT License.
# See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false

from typing import List, Any, Dict

from inspect import signature # type: ignore
from importlib import reload, invalidate_caches

from bpy.app import translations
from bpy.utils import register_class, unregister_class # type: ignore
from bpy import types

from types import ModuleType, MethodType
from .loader.proc_loader import ProcLoader
from .keymap_manager import KeymapManager
from .properties_manager import PropertiesManager

# TODO: Improve redundant duplicate loading
# 前回のモジュールを読み込んでリロードしてからモジュールを更新しないとうまくいかない


class AddonManager:
    """This class in charge of registering and deregistering add-ons."""
    def __init__(
        self,
        file: str,
        local_symbols: dict[str, Any],
        dir_priorities: List[str] | None = None,
        exclude_dirs: List[str] | None = None,
        exclude_when_not_debugging: List[str] | None = None,
        translation_table: Dict[str, Dict[tuple[Any, Any], str]] | None = None,
        cat_name: str | None = None,
        is_debug_mode: bool = False,
        cache_path: str | None = None
    ) -> None:
        """Initialize

        Args:
            file (str): Path to the add-on's __init__.py file.
            local_symbols (dict[str, Any]): Local symbols in the add-on's __init__.py file.
            dir_priorities (List[str], optional): Order of root folders to be read. Defaults to [].
            exclude_dirs (List[str], optional): Folders not loaded. Defaults to [].
            exclude_when_not_debugging (List[str], optional): Folders not loaded when not in debug mode. Defaults to [].
            translation_table (Dict[str, Dict[tuple[Any, Any], str]] | None, optional): translation dictionary. Defaults to None.
            cat_name (str | None, optional): Specify the default category name for the panel. Defaults to None.
            is_debug_mode (bool, optional): With or without debug mode. Defaults to False.
            cache_path(str | None, optional): Specify the path where the cache file is to be saved.
        """
        from os.path import basename, dirname

        self.__addon_name = basename(dirname(file))
        self.__is_debug_mode = is_debug_mode
        self.__CACHE_PATH = cache_path
        self.__is_initialized = "__addon_enabled__" in local_symbols
        self.__load(file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging)
        self.__properties_manager = PropertiesManager(self.__addon_name)
        self.__keymap_manager = KeymapManager()
        self.__translation_table = translation_table

        self.reload(
            file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging
        )

    @property
    def keymap(self) -> KeymapManager:
        return self.__keymap_manager

    @property
    def property(self) -> PropertiesManager:
        return self.__properties_manager

    def register(self) -> None:
        """Perform registration of the add-on class and each function"""
        if self.__is_initialized:
            self.__unregister_utils()

        # for cls in [clazz for clazz in self.__classes if issubclass(clazz, types.PropertyGroup)]:
        for cls in [clazz for clazz in self.__plugins.classes if not hasattr(types, clazz.bl_idname)]: # type: ignore
            if issubclass(cls, types.PropertyGroup) and cls.is_registered: # type: ignore
                continue

            if hasattr(cls, "set_manager") and isinstance(getattr(cls, "set_manager"), MethodType):
                getattr(cls, "set_manager")(self)

            register_class(cls)

        self.__call("register")

        if self.__translation_table and self.__addon_name:
            translations.register(self.__addon_name, self.__translation_table)  # type: ignore

    def unregister(self) -> None:
        """Unregister the add-on class and each function"""
        for cls in reversed(self.__plugins.classes):
            unregister_class(cls)

        self.__unregister_utils()

    def reload(
        self,
        file: str,
        cat_name: str | None,
        dir_priorities: List[str] | None,
        exclude_dirs: List[str] | None,
        exclude_when_not_debugging: List[str] | None
    ) -> None:
        """Reload the add-on class when the 'script.reload' operator is called"""
        if not self.__is_debug_mode or not self.__is_initialized:
            return

        for mdl in self.__plugins.modules:
            reload(mdl)  # type: ignore
        invalidate_caches()
        self.__load(
            file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging
        )

    def __call(self, identifier: str) -> None:
        """Invoke the function specified by 'identifier' for all add-on modules.

        Args:
            identifier (str): The name of the function you want to call
        """
        for mdl in self.__plugins.modules:
            self.__invoke(mdl, identifier)

    def __invoke(self, mdl: ModuleType | type, identifier: str) -> None:
        """If 'mdl' module has a function named 'identifier', invoke it.

        Args:
            mdl (ModuleType | type): Module from which to call function
            identifier (str): Name of the function to call
        """
        if not hasattr(mdl, identifier):
            return

        if len(signature(getattr(mdl, identifier)).parameters) == 0:
            getattr(mdl, identifier)()
        else:
            getattr(mdl, identifier)(self)

    def __load(
        self,
        file: str,
        cat_name: str | None,
        dir_priorities: List[str] | None,
        exclude_dirs: List[str] | None,
        exclude_when_not_debugging: List[str] | None
    ) -> None:
        self.__plugins = ProcLoader(file, self.__CACHE_PATH, is_debug_mode=self.__is_debug_mode).load(dir_priorities, exclude_dirs, exclude_when_not_debugging, cat_name)

    def __unregister_utils(self) -> None:
        self.__call("unregister")

        self.__keymap_manager.unregister()
        self.__properties_manager.unregister()
        if self.__translation_table and self.__addon_name:
            translations.unregister(self.__addon_name)
