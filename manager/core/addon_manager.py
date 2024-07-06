#This program is distributed under the MIT License.
#See the LICENSE file for details.

from typing import List, Any, Dict
from types import ModuleType

from .proc_loader import ProcLoader
from .keymap_manager import KeymapManager
from .properties_manager import PropertiesManager

from bpy.utils import register_class, unregister_class # type: ignore
from bpy.app import translations
from bpy import types

# TODO: Improve redundant duplicate loading
'''前回のモジュールを読み込んでリロードしてからモジュールを更新しないとうまくいかない'''

class AddonManager:
    """This class in charge of registering and deregistering add-ons."""

    def __init__(self, path: str, target_dirs: List[str], local_symbols: dict[str, Any], addon_name: str | None = None,
                 translation_table: Dict[str, Dict[tuple[Any, Any], str]] | None = None, cat_name: str | None = None, is_debug_mode: bool = False) -> None:
        """Initialize

        Args:
            path (str): Path to the add-on folder or '__init__.py' file.
            target_dirs (List[str]): The name of the directory to be read.
            local_symbols (dict[str, Any]): The symbol table of the addon's file
            addon_name (str | None, optional): Add-on name. Required when using translation tables or properties. Defaults to None.
            translation_table (Dict[str, Dict[tuple[Any, Any], str]] | None, optional): Standard format translation table of Blender. Defaults to None.
            cat_name (str | None, optional): 'bl_category' attribute that is assigned by default to subclasses of 'bpy.types.Panel'. Defaults to None.
            is_debug_mode (bool, optional): Presence or absence of debug mode. Defaults to False.
        """
        self.__addon_name = addon_name
        self.__is_debug_mode = is_debug_mode
        self.__is_initialized = '__addon_enabled__' in local_symbols
        self.__load(path, target_dirs, cat_name)
        PropertiesManager.set_name(self.__addon_name)
        self.__translation_table = translation_table

        self.reload(local_symbols, path, target_dirs, cat_name)

    def register(self) -> None:
        """Perform registration of the add-on class and each function"""
        if self.__is_initialized: self.__unregister_utils()

        #for cls in [clazz for clazz in self.__classes if issubclass(clazz, types.PropertyGroup)]:
        for cls in [clazz for clazz in self.__classes if not hasattr(types, clazz.bl_idname)]: # type: ignore
            if issubclass(cls, types.PropertyGroup) and cls.is_registered: continue # type: ignore
            register_class(cls)

        self.__call('register')

        if self.__translation_table and self.__addon_name: translations.register(self.__addon_name, self.__translation_table) #type: ignore

    def unregister(self) -> None:
        """Unregister the add-on class and each function"""
        for cls in reversed(self.__classes):
            unregister_class(cls)

        self.__unregister_utils()

    def reload(self, local_symbols: dict[str, Any], path: str, target_dirs: List[str], cat_name: str | None) -> None:
        """ Reload the add-on class when the 'script.reload' operator is called"""
        from importlib import reload, invalidate_caches

        if not self.__is_debug_mode or not self.__is_initialized: return

        for mdl in self.__modules:
            reload(mdl) # type: ignore

        invalidate_caches()
        self.__load(path, target_dirs, cat_name)

    def __call(self, identifier: str) -> None:
        """Invoke the function specified by 'identifier' for all add-on modules.

        Args:
            identifier (str): The name of the function you want to call
        """
        for mdl in self.__modules:
            self.__invoke(mdl, identifier)

    def __invoke(self, mdl: ModuleType | type, identifier: str) -> None:
        """If 'mdl' module has a function named 'identifier', invoke it.

        Args:
            mdl (ModuleType | type): Module from which to call function
            identifier (str): Name of the function to call
        """
        if hasattr(mdl, identifier): getattr(mdl, identifier)()

    def __load(self, path: str, target_dirs: List[str], cat_name: str | None) -> None:
        self.__modules, self.__classes = ProcLoader(path, is_debug_mode=self.__is_debug_mode).load(target_dirs, cat_name)

    def __unregister_utils(self) -> None:
        self.__call('unregister')

        KeymapManager.unregister()
        PropertiesManager.unregister()
        if self.__translation_table and self.__addon_name: translations.unregister(self.__addon_name)