#This program is distributed under the MIT License.
#See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false

#TODO: Optimize the loading process.

from collections import defaultdict
from typing import Callable, List, Dict
from types import ModuleType

import os
from os.path import dirname, basename, join, splitext, isfile
from importlib import import_module
from inspect import getmembers, isclass
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

    DEFAULT_TARGET_CLASSES: List[type] = ( # type: ignore
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
    )

    def __init__(self, path: str, target_classes: List[type] | None = None, is_debug_mode: bool = False) -> None:
        """Initialize and add addon folder to module search path

        Args:
            path (str): Path to the add-on folder
            target_classes (List[type] | None, optional): Type of class to load. Defaults to None.
            is_debug_mode (bool, optional): Presence of debug mode. Defaults to False.
        """
        root = dirname(path) if isfile(path) else path #指定されたパスがファイルであれば最後のフォルダまでのパスを取得する
        self.__dir_name = basename(root) #アドオンのフォルダ名       例:addon_folder
        self.__path = dirname(root)      #アドオンフォルダまでのパス 例:path/to/blender/script/
        self.__is_debug_mode = is_debug_mode

        self.__TARGET_CLASSES: List[type] = self.DEFAULT_TARGET_CLASSES if target_classes is None else target_classes

        #モジュールの検索パスに登録する
        if self.__path not in sys.path:
            sys.path.append(self.__path)

    @staticmethod
    def is_disabled(clazz: type) -> bool:
        """Check for the presence and value of '_addon_proc_is_disabled' attribute in the target class

        Args:
            clazz (type): Target class

        Returns:
            bool: Whether the target class is marked as disabled
        """
        return hasattr(clazz, '_addon_proc_is_disabled') and clazz._addon_proc_is_disabled == True # type: ignore

    #モジュールとクラスを取得する
    def load(self, dirs: List[str], cat_name: str | None = None) -> List[List[ModuleType] | List[type]]:
        """Load addon's modules and classes

        Args:
            dirs (List[str]): Directory to search
            cat_name (str | None, optional): Default category name applied to the panel. Defaults to None.

        Returns:
            List[List[ModuleType] | List[type]]: Loaded modules and classes(Module in column 0, class in column 1)
        """
        modules = self.load_modules(self.load_files(dirs))
        return [modules, self.load_classes(modules, cat_name)]

    #[アドオン名].[フォルダ名].[ファイル名]の形でモジュール名を取得する
    def load_files(self, dirs: List[str]) -> List[str]:
        """Get path of module to load

        Args:
            dirs (List[str]): Directory to load from

        Returns:
            List[str]: Path of retrieved module
        """
        from pathlib import Path

        addon_path = join(self.__path, self.__dir_name) #アドオンへの絶対パス

        ignore_modules: List[str] = []
        modules: List[str] = []

        for dir in dirs:
            if not self.__is_debug_mode: ignore_modules.append(f"{self.__dir_name}.{dir}.debug")

            #フォルダ内のすべての.pyファイルの絶対パスを取得する
            for file in Path(join(addon_path, dir)).glob('**/*.py'):
                path = str(file)
                mdl_path = splitext(path.lstrip(f"{self.__path}{os.sep}").replace(os.sep, '.'))[0] #モジュールパス
                if basename(path) == '__init__.py':
                    #無視リストを読み込む
                    init = import_module(mdl_path)
                    if hasattr(init, 'ignore'):
                        for mdl in init.ignore:
                            ignore_modules.append(f"{splitext(mdl_path)[0]}.{mdl}") #無視リストを__init__.pyが所属するモジュールからのパスに変換する
                    if hasattr(init, 'priority'):
                        for i, mdl in enumerate(init.priority):
                            if hasattr(mdl, 'ADDON_MODULE_PRIORITY'): raise DuplicateAttributeError(gen_msg(ProcLoader, MsgType.CRITICAL, f'The {mdl} modules must not have an attribute called "ADDON_MODULE_PRIORITY".'))
                            mdl.ADDON_MODULE_PRIORITY = i

                else:
                    modules.append(mdl_path)

        return [mdl for mdl in modules if not mdl.startswith(tuple(ignore_modules))] #無視リストにないモジュールを返す


    #モジュールをインポートする
    @staticmethod
    def load_modules(paths: List[str]) -> List[ModuleType]:
        """Load a module based on its path

        Args:
            paths (List[str]): Path to the module

        Returns:
            List[ModuleType]: Loaded module
        """
        modules: List[ModuleType] = []

        for path in paths:
            try:
                modules.append(import_module(path))
            except (ImportError, ModuleNotFoundError) as e:
                print(gen_msg(ProcLoader, MsgType.ERROR, f'Failed to load "{path}" module. \n {e}'))

        return modules

    #モジュール内のクラスを取得する
    def load_classes(self, modules: List[ModuleType], cat_name: str | None = None) -> List[type]:
        """Retrieve addon class within a module

        Args:
            modules (List[ModuleType]): Target module
            cat_name (str | None, optional): Default category name applied to the panel. Defaults to None.

        Returns:
            List[type]: Loaded classes
        """
        import numpy as np

        def sort_priority(index: int) -> Callable[..., int | float]:
            return lambda item: float('inf') if item[index] < 0 else item[index] # type: ignore

        class_priority: Dict[type, tuple[int, int]] = self.__load_addon_classes(modules)

        #モジュールの優先度をキー、クラスとクラスの優先度のリストを値とする辞書
        sorted_by_mdl: Dict[int, List[tuple[type, int]]] = defaultdict(list)

        #モジュールの優先度ごとにクラスを分類する
        for cls, pr in class_priority.items():
            mdl = sorted_by_mdl[pr[0]]

            #最後の要素と今回の要素を比較し、今回の要素のほうが優先度が高ければ前に挿入する
            if len(mdl) > 1 and mdl[-1][1] < pr[1]:
                mdl.insert(-1, (cls, pr[1]))
            else:
                mdl.append((cls, pr[1]))

        #辞書をモジュールの優先度ごとに並び替えたリストを作り、クラスを追加する
        sorted_by_cls: List[type] = []
        for clazz in [item[1] for item in sorted(sorted_by_mdl.items(), key=sort_priority(0))]:
            sorted_by_cls.extend(np.array(clazz)[:, 0])

        return self.__add_attribute(sorted_by_cls, cat_name) #足りない属性を追加して返す

    def __load_addon_classes(self, modules: List[ModuleType]) -> Dict[type, tuple[int, int]]:
        class_priority: Dict[type, tuple[int, int]] = {}

        for mdl in modules:
            mdl_priority: int = 0
            if hasattr(mdl, 'ADDON_MODULE_PRIORITY') and type(getattr(mdl, 'ADDON_MODULE_PRIORITY')) == int:
                mdl_priority = getattr(mdl, 'ADDON_MODULE_PRIORITY')
            else:
                mdl_priority = -1

            for clazz in getmembers(mdl, isclass):
                clazz = clazz[1]
                #対象のクラスがアドオンのクラスかつ無効でない場合追加する
                if not any(issubclass(clazz, c) and  clazz != c for c in self.__TARGET_CLASSES): continue # type: ignore
                if self.is_disabled(clazz): continue

                #優先順位とクラスを辞書に追加する
                if hasattr(clazz, '_addon_proc_priority'): class_priority[clazz] = (mdl_priority, clazz._addon_proc_priority)
                else: class_priority[clazz] = (mdl_priority, -1)

        return class_priority

    def __add_attribute(self, classes: List[type], cat_name: str | None) -> List[type]:
        """Add necessary attributes to the add-on

        Args:
            classes (List[tuple[type, int]]): Target class
            cat_name (str | None): Default category name applied to the panel

        Returns:
            List[type]: Class with added elements
        """
        for cls in classes:
            if not hasattr(cls, 'bl_idname'): cls.bl_idname = cls.__name__
            if cat_name and issubclass(cls, types.Panel) and not hasattr(cls, 'bl_category'): cls.bl_category = cat_name # type: ignore

        return classes
