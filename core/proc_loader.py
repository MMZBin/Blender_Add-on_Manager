#This program is distributed under the MIT License.
#See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false

#TODO: Optimize the loading process.

'''
    モジュールの階層の深さと優先度を元にソートする
    1.最も浅い__init__.pyで定義された優先度とその__init__.pyファイルの深さを記録する
    2.クラスをモジュール内の優先度順にソート
    3.モジュールを優先度順にソート
    4.モジュールを深さ順にソート
'''

#パッケージの優先度とモジュールの優先度を分ける

from typing import Callable, Iterable, List, Tuple, Dict
from types import ModuleType

import os
from os.path import dirname, basename, splitext, isfile
from importlib import import_module
import sys

from .utils.gen_msg import MsgType, gen_msg
from .exceptions import DuplicateAttributeError

from bpy import types

#このデコレータが付いている場合、そのクラスは無視されます。
def disable(cls: type) -> type:
    if hasattr(cls, '_addon_proc_is_disabled'): raise DuplicateAttributeError("The '_addon_proc_is_disabled' attribute is used in the 'disable' decorator.")
    cls._addon_proc_is_disabled = True
    return cls

#このデコレータで読み込みの優先順位を付けられます。付けられなかった場合は最後になります。
def priority(pr: int) -> Callable[[type], type]:
    def _priority(cls: type) -> type:
        if (hasattr(cls, '_addon_proc_priority')): raise DuplicateAttributeError("The '_addon_proc_priority' attribute is used in the 'priority' decorator.")
        cls._addon_proc_priority = pr
        return cls
    return _priority

class ProcLoader:
    """Loads modules and addon classes.

    Attributes:
        DEFAULT_TARGET_CLASSES (List[type]): Default classes for loading

    Raises:
        NotADirectoryError: Throws if the add-on module path is not a folder.
    """

    DEFAULT_TARGET_CLASSES: List[type] = [
        types.Operator, types.Panel, types.Menu, types.Header, types.UIList, types.PropertyGroup, types.AddonPreferences, types.RenderEngine, types.Node, types.NodeSocket,
        types.NodeTree, types.Gizmo, types.GizmoGroup, types.Macro, types.OperatorFileListElement, types.OperatorProperties, types.Space, types.Region, types.KeyMap, types.KeyMapItem,
        types.RenderSettings, types.Scene, types.Object, types.Mesh, types.Curve, types.MetaBall, types.Text, types.Sound, types.WindowManager, types.Screen,
        types.Brush, types.DynamicPaintSurface, types.DynamicPaintBrushSettings, types.DynamicPaintCanvasSettings, types.ParticleSettings, types.ClothSettings, types.PointCache, types.KeyingSet, types.KeyingSetPath, types.TransformOrientation,
        types.ViewLayer, types.ToolSettings, types.GPencilLayer, types.GPencilFrame, types.GPencilStroke, types.CompositorNode, types.ShaderNode, types.TextureNode, types.NodeLink, types.Material,
        types.World, types.Armature, types.Camera, types.Lattice, types.Texture, types.Histogram, types.Scopes, types.Constraint, types.Modifier, types.RenderLayer,
        types.RenderPass, types.Image, types.MovieClip, types.Mask, types.MaskLayer, types.MovieTrackingSettings, types.MovieTrackingObject, types.MovieTrackingMarker, types.MovieTrackingTrack,
        types.MovieTrackingPlaneMarker, types.MovieTrackingPlaneTrack, types.MovieTrackingStabilization, types.MovieTrackingReconstruction, types.MovieTrackingCamera, types.MovieTrackingDopesheet, types.FCurve, types.Action, types.TimelineMarker, types.Area, types.RegionView3D,
        types.SpaceView3D, types.SpaceImageEditor, types.SpaceUVEditor, types.SpaceTextEditor, types.SpaceGraphEditor, types.SpaceNLA, types.SpaceFileBrowser, types.SpaceProperties, types.SpaceInfo, types.SpaceOutliner,
        types.SpaceSequenceEditor, types.SpaceClipEditor, types.SpaceNodeEditor, types.SpaceConsole, types.SpacePreferences, types.Event, types.Timer, types.AnimData, types.NlaStrip, types.NlaTrack, types.FModifier,
        types.FCurveSample, types.FCurveModifiers, types.CompositorNodeTree, types.ShaderNodeTree, types.TextureNodeTree, types.GeometryNodeTree, types.OperatorMacro
    ]

    def __init__(self, path: str, target_classes: Tuple[type] | None = None, is_debug_mode: bool = False) -> None:
        """Initialize and add addon folder to module search path

        Args:
            path (str): Path to the add-on folder
            target_classes (List[type] | None, optional): Type of class to load. Defaults to None.
            is_debug_mode (bool, optional): Presence of debug mode. Defaults to False.
        """
        from os.path import join

        root = dirname(path) if isfile(path) else path #指定されたパスがファイルであれば最後のフォルダまでのパスを取得する
        self.ADDON_NAME = basename(root) #アドオンのフォルダ名       例:addon_folder
        self.PATH = dirname(root)      #アドオンフォルダまでのパス 例:path/to/blender/script/
        self.CACHE_PATH = join(self.PATH, self.ADDON_NAME, "addon_modules.json")
        self.IS_DEBUG_MODE = is_debug_mode

        self.TARGET_CLASSES: List[type] = self.DEFAULT_TARGET_CLASSES if target_classes is None else target_classes

        self.__cat_name: str | None = None

        #モジュールの検索パスに登録する
        if self.PATH not in sys.path:
            sys.path.append(self.PATH)

    @staticmethod
    def is_disabled(clazz: type) -> bool:
        """Check for the presence and value of '_addon_proc_is_disabled' attribute in the target class."""
        return hasattr(clazz, '_addon_proc_is_disabled') and clazz._addon_proc_is_disabled == True # type: ignore

    def load(self, dir_priorities: List[str]=[], exclude_modules: List[str]=[], exclude_when_not_debugging: List[str]=[], cat_name: str | None = None) -> List[tuple[ModuleType, List[type]]]:
        """Load modules and add-on classes.

        Args:
            dir_priorities (List[str], optional): Specifies the order in which root-level directories are read.. Defaults to [].
            exclude_modules (List[str], optional): Specify folders not to be read. Defaults to [].
            exclude_when_not_debugging (List[str], optional): Specify folders to exclude when not in debug mode. Defaults to [].
            cat_name (str | None, optional): Specify the default category name for the panel. Defaults to None.

        Returns:
            List[tuple[ModuleType, List[type]]]: List of modules and add-on classes.
        """

        self.__cat_name = cat_name

        if self.IS_DEBUG_MODE:
            modules_and_classes = ProcFinder(self).load(dir_priorities, exclude_modules, exclude_when_not_debugging)

            self.__write_cache(modules_and_classes)

            return modules_and_classes
        else:
            return CacheLoader(self).load(self.CACHE_PATH)

    def add_attribute(self, cls: type) -> type:
        """Add necessary attributes to the add-on.

        Args:
            classes (type): Target class

        Returns:
            type: Class with added elements
        """
        if not hasattr(cls, 'bl_idname'): cls.bl_idname = cls.__name__
        if self.__cat_name is not None and issubclass(cls, types.Panel) and not hasattr(cls, 'bl_category'): cls.bl_category = self.__cat_name

        return cls

    def __write_cache(self, modules_and_classes: List[tuple[ModuleType, List[type]]]) -> None:
        import json

        json_data: List[Dict[str, str | List[str]]] = []
        for module, classes in modules_and_classes:
            json_data.append({
                'module':  module.__name__,
                'classes': [cls.__name__ for cls in classes]
            })

        with open(self.CACHE_PATH, "w", encoding="utf-8") as cache:
            json.dump(json_data, cache, indent=4)


class ProcFinder:
    """Load add-on modules and classes."""

    def __init__(self, loader: ProcLoader) -> None:
        self.__loader = loader

    def load(self, dir_priorities: List[str]=[], exclude_modules: List[str]=[], exclude_when_not_debugging: List[str]=[]) -> List[tuple[ModuleType, List[type]]]:
        """Load modules and add-on classes.

        Args:
            dir_priorities (List[str], optional): Specifies the order in which root-level directories are read.. Defaults to [].
            exclude_modules (List[str], optional): Specify folders not to be read. Defaults to [].
            exclude_when_not_debugging (List[str], optional): Specify folders to exclude when not in debug mode. Defaults to [].

        Returns:
            List[tuple[ModuleType, List[type]]]: List of modules and add-on classes.
        """
        from os import walk
        from os.path import join

        exclude_modules += [basename(dirname(dirname(__file__)))]
        if not self.__loader.IS_DEBUG_MODE: exclude_modules += exclude_when_not_debugging

        exclude_modules = [(self.__loader.ADDON_NAME + '.' + dir) for dir in exclude_modules] # 無視するモジュールをモジュールパスの形にする

        modules_path_with_pr: dict[str, int] = {}

        for root, _, files in walk(join(self.__loader.PATH, self.__loader.ADDON_NAME)):
            if basename(root).startswith('.'): continue

            root_mdl_path = root.lstrip(self.__loader.PATH + os.sep).replace(os.sep, '.')

            priority = -1

            for i, path in enumerate(dir_priorities):
                if root_mdl_path.startswith(path):
                    priority = i

            root_mdl_path += '.'

            for file in [f for f in files if f.endswith('.py')]:
                mdl_path = root_mdl_path + splitext(file)[0]

                modules_path_with_pr[mdl_path] = priority

        modules_path = [mdl[0] for mdl in sorted(modules_path_with_pr.items(), key=lambda path: float('inf') if path[1] < 0 else path[1])]

        modules = list(map(import_module, modules_path))
        if not self.__loader.IS_DEBUG_MODE:
            modules = [mdl for mdl in modules if not mdl.__package__.endswith('debug')] # type: ignore

        exclude_modules += self.__load_init_attr(modules)

        modules = [mdl for mdl in modules if mdl.__file__ and not self.__abs_to_mdl_path(mdl.__file__ + '.').startswith(tuple(exclude_modules))] #無効なモジュールを除外する

        modules_and_classes = self.__load_classes(modules)

        return sorted(modules_and_classes, key=lambda mdl: float('inf') if getattr(mdl[0], 'ADDON_MODULE_PRIORITY', -1) == -1 else mdl[0].ADDON_MODULE_PRIORITY)

    def __load_init_attr(self, modules: List[ModuleType]) -> List[str]:
        disabled_modules: List[str] = []

        for init in [mdl for mdl in modules if mdl.__file__ and mdl.__file__.endswith('__init__.py')]:
            modules.remove(init)

            if init.__package__ is None: continue

            package_path = init.__package__ + '.'

            if hasattr(init, 'disable'):
                if not issubclass(type(init.disable), Iterable): raise TypeError(gen_msg(ProcLoader, MsgType.CRITICAL, f'Attribute "disable" of module "{init}" is not iterable.'))
                for mdl in init.disable:
                    disabled_modules.append(package_path + mdl + '.')

            self.__set_module_priority(init)

        return disabled_modules

    def __abs_to_mdl_path(self, path: str) -> str:
        return path.lstrip(self.__loader.PATH).replace(os.sep, '.')


    def __load_classes(self, modules: List[ModuleType]) -> List[tuple[ModuleType, List[type]]]:
        """Reads the add-on class."""
        from inspect import getmembers, isclass

        modules_and_classes: List[tuple[ModuleType, List[type]]] = []

        for mdl in modules:
            classes = [cls[1] for cls in getmembers(mdl, isclass) if issubclass(cls[1], tuple(self.__loader.TARGET_CLASSES)) and not cls[1] in self.__loader.TARGET_CLASSES and not getattr(cls, '_addon_proc_disabled', False)]
            for cls in classes:
                self.__loader.add_attribute(cls)
            modules_and_classes.append((mdl, sorted(classes, key=lambda cls: float('inf') if getattr(cls, '_addon_proc_priority', -1) == -1 else cls._addon_proc_priority))) # type: ignore

        return modules_and_classes

    def __set_module_priority(self, init_module: ModuleType) -> None:
        """Set module priority recursively."""
        from inspect import getmembers, ismodule
        priority_count: int = 0

        def set_priority(package: ModuleType) -> None:
            nonlocal priority_count

            for mdl in getmembers(package, ismodule):
                if hasattr(mdl[1], '__path__'):
                    try:
                        _set_module_priority(import_module(mdl[1].__file__.lstrip(self.__loader.PATH).replace(os.sep, '.') + '.' + '__init__')) # type: ignore
                    except ModuleNotFoundError:
                        set_priority(mdl[1])
                mdl[1].ADDON_MODULE_PRIORITY = priority_count
                priority_count += 1

        def _set_module_priority(init: ModuleType) -> None:
            nonlocal priority_count

            if getattr(init, 'ADDON_INIT_LOADED', False): return
            init.ADDON_INIT_LOADED = True

            if not hasattr(init, 'priority'): return
            if not issubclass(type(init.priority), Iterable): raise TypeError(gen_msg(ProcLoader, MsgType.CRITICAL, f'Attribute "priority" of module "{init}" is not iterable.'))

            if init.__package__ is None: return
            package_path = init.__package__ + '.'

            for mdl_path in init.priority:
                priority_path = package_path + mdl_path
                module = import_module(priority_path)
                #対象がパッケージだったら__init__モジュールから優先度を設定する
                if hasattr(module, '__path__'):
                    try:
                        _set_module_priority(import_module(priority_path + '.' + '__init__'))
                    except ModuleNotFoundError:
                        #__init__モジュールがなければ登録順に優先度を設定する
                        set_priority(module)
                else:
                    module.ADDON_MODULE_PRIORITY = priority_count

                priority_count += 1

        _set_module_priority(init_module)

        return

#pyright: reportUnknownVariableType = false
#pyright: reportUnknownArgumentType = false

class CacheLoader:
    def __init__(self, loader: ProcLoader) -> None:
        self.__loader = loader

    def load(self, path: str) -> List[Tuple[ModuleType, List[type]]]:
        import json
        from os.path import exists

        if not exists(path):
            raise FileNotFoundError(gen_msg(CacheLoader, MsgType.CRITICAL, "The cache for the add-on's module has not yet been created.\nPlease temporarily enable debug mode for the add-on and restart."))

        module_and_classes: List[tuple[ModuleType, List[type]]] = []
        with open(path, "r", encoding="utf-8") as cache:
            cache = json.load(cache)

            for entry in cache:
                module_name = entry['module']
                class_names = entry['classes']

                module = import_module(module_name)
                classes = [self.__loader.add_attribute(getattr(module, cls_name)) for cls_name in class_names]

                module_and_classes.append((module, classes))

        return module_and_classes
