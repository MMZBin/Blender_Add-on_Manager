# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from importlib import invalidate_caches, reload
from os.path import join, dirname, basename
import inspect

from bpy.utils import register_class, unregister_class # type: ignore

from .config import Config
from .features.properties_manager import PropertiesManager
from .features.keymap_manager import KeymapManager

from .core.loader.module_loader import ModuleLoader
from .core.loader.addon_module import Modules

class AddonManager:
    """Manage add-on."""
    def __init__(self) -> None:
        self.PATH_TO_ADDON          = dirname(dirname(__file__))                                  # Path to the add-ons folder    (for example: /extensions/user_default/your_addon)
        self.PATH_TO_MODULES        = join(self.PATH_TO_ADDON, "modules")                         # Path to the modules folder    (for example: /extensions/user_default/your_addon/modules)
        self.PATH_TO_SCRIPTS_FOLDER = dirname(dirname(self.PATH_TO_MODULES))                      # Path to the scripts folder    (for example: /extensions/user_default/)
        self.ADDON_FOLDER_NAME      = basename(dirname(self.PATH_TO_MODULES))                     # Add-on's folder name          (for example: your_addon)
        self.PATH_TO_DATA           = join(self.PATH_TO_ADDON, "manager", "data")                 # Path to the data folder       (for example: /extensions/user_default/your_addon/manager/data)
        self.SYS_PATH_TO_ADDON      = __name__.split('.' + self.ADDON_FOLDER_NAME, maxsplit=1)[0] # System path to add -on folder (for example: bl_ext.user_default)

        self.__modules: Modules | None = None                                     # All modules and operators

        PropertiesManager(self.ADDON_FOLDER_NAME) # 初期化のため

    def register(self) -> None:
        """Register the add-on with Blender."""
        if Config().data["is_debug_mode"]:
            self.reload()

        self.__modules = ModuleLoader(self).load()

        for cls in self.__modules.classes:
            register_class(cls)

        self.__call_modules_func("register")

    def reload(self) -> None:
        """Reload the add-on with Blender."""
        if self.__modules is None:
            return

        for mdl in self.__modules.modules:
            try:
                reload(mdl)
            except ModuleNotFoundError:
                pass

        invalidate_caches()

    def unregister(self) -> None:
        """Unregister the add-on with Blender."""
        if self.__modules is None:
            raise ValueError('The "unregister" method must be called after the "register" method.')

        for cls in reversed(self.__modules.classes):
            unregister_class(cls)

        self.__call_modules_func("unregister")
        KeymapManager().unregister()
        PropertiesManager().unregister()

    def __call_modules_func(self, identifier: str) -> None:
        """Calls a function contained in the module."""
        if self.__modules is None:
            return

        for mdl in self.__modules.modules:
            if not hasattr(mdl, identifier):
                continue
            if len(inspect.signature(getattr(mdl, identifier)).parameters) == 0:
                getattr(mdl, identifier)()
            else:
                getattr(mdl, identifier)(self)
