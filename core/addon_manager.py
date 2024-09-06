#This program is distributed under the MIT License.
#See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false

from types import MethodType
from .proc_loader import ProcLoader
from .keymap_manager import KeymapManager
from .properties_manager import PropertiesManager

from bpy.app import translations

# TODO: Improve redundant duplicate loading
'''前回のモジュールを読み込んでリロードしてからモジュールを更新しないとうまくいかない'''

class AddonManager:
    """This class in charge of registering and deregistering add-ons."""
    from typing import List, Any, Dict
    from types import ModuleType, MethodType

    def __init__(self, file: str, local_symbols: dict[str, Any],
                 dir_priorities: List[str]=[], exclude_dirs: List[str] = [], exclude_when_not_debugging: List[str]=[],
                 translation_table: Dict[str, Dict[tuple[Any, Any], str]] | None = None, cat_name: str | None = None,
                 is_debug_mode: bool = False) -> None:
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
        """
        from os.path import basename, dirname

        self.__addon_name = basename(dirname(file))
        self.__is_debug_mode = is_debug_mode
        self.__is_initialized = '__addon_enabled__' in local_symbols
        self.__load(file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging)
        self.__properties_manager = PropertiesManager(self.__addon_name)
        self.__keymap_manager = KeymapManager()
        self.__translation_table = translation_table

        self.reload(file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging)

    @property
    def keymap(self) -> KeymapManager: return self.__keymap_manager
    @property
    def property(self) -> PropertiesManager: return self.__properties_manager


    def register(self) -> None:
        """Perform registration of the add-on class and each function"""
        from bpy.utils import register_class
        from bpy import types

        if self.__is_initialized: self.__unregister_utils()

        #for cls in [clazz for clazz in self.__classes if issubclass(clazz, types.PropertyGroup)]:
        for cls in [clazz for clazz in self.__classes if not hasattr(types, clazz.bl_idname)]: # type: ignore
            if issubclass(cls, types.PropertyGroup) and cls.is_registered: continue # type: ignore

            if hasattr(cls, 'set_manager') and isinstance(getattr(cls, 'set_manager'), MethodType): getattr(cls, 'set_manager')(self)

            register_class(cls)

        self.__call('register')

        if self.__translation_table and self.__addon_name: translations.register(self.__addon_name, self.__translation_table) #type: ignore

    def unregister(self) -> None:
        """Unregister the add-on class and each function"""
        from bpy.utils import unregister_class # type: ignore

        for cls in reversed(self.__classes):
            unregister_class(cls)

        self.__unregister_utils()

    def reload(self, file: str, cat_name: str | None, dir_priorities: List[str], exclude_dirs: List[str], exclude_when_not_debugging: List[str]) -> None:
        """ Reload the add-on class when the 'script.reload' operator is called"""
        from importlib import reload, invalidate_caches

        if not self.__is_debug_mode or not self.__is_initialized: return

        for mdl in self.__modules:
            reload(mdl) # type: ignore
        invalidate_caches()
        self.__load(file, cat_name, dir_priorities, exclude_dirs, exclude_when_not_debugging)

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
        from inspect import signature

        if not hasattr(mdl, identifier): return

        if len(signature(getattr(mdl, identifier)).parameters) == 0:
            getattr(mdl, identifier)()
        else:
            getattr(mdl, identifier)(self)

    def __load(self, file: str, cat_name: str | None, dir_priorities: List[str], exclude_dirs: List[str], exclude_when_not_debugging: List[str]) -> None:
        modules = ProcLoader(file, is_debug_mode=self.__is_debug_mode).load(dir_priorities, exclude_dirs, exclude_when_not_debugging, cat_name)
        self.__modules = [mdl[0] for mdl in modules]
        self.__classes = [cls for cls_list in [mdl[1] for mdl in modules] for cls in cls_list]

    def __unregister_utils(self) -> None:
        self.__call('unregister')

        self.__keymap_manager.unregister()
        self.__properties_manager.unregister()
        if self.__translation_table and self.__addon_name: translations.unregister(self.__addon_name)
