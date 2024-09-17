# This program is distributed under the MIT License.
# See the LICENSE file for details.

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false

"""
    モジュールの階層の深さと優先度を元にソートする
    1.最も浅い__init__.pyで定義された優先度とその__init__.pyファイルの深さを記録する
    2.クラスをモジュール内の優先度順にソート
    3.モジュールを優先度順にソート
    4.モジュールを深さ順にソート
"""

# パッケージの優先度とモジュールの優先度を分ける

from typing import Callable, List, Tuple, Dict

from os.path import dirname, basename, isfile, join
import sys

import json

from bpy import types

from ..exceptions import DuplicateAttributeError

from .addon_module import AddonModule
from .proc_finder import ProcFinder
from .cache_loader import CacheLoader

def disable(cls: type) -> type:
    """Disables the add-on class."""
    if hasattr(cls, "addon_proc_is_disabled"):
        raise DuplicateAttributeError(
            "The 'addon_proc_is_disabled' attribute is used in the 'disable' decorator."
        )
    cls.addon_proc_is_disabled = True
    return cls

def priority(pr: int) -> Callable[[type], type]:
    """Specifies the order in which classes are loaded."""
    def _priority(cls: type) -> type:
        """closure"""
        if hasattr(cls, "addon_proc_priority"):
            raise DuplicateAttributeError(
                "The 'addon_proc_priority' attribute is used in the 'priority' decorator."
            )
        cls.addon_proc_priority = pr
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
        types.RenderSettings, types.Scene, types.Object, types.Mesh, types.Curve, types.MetaBall, types.Text, types.Sound, types.WindowManager, types.Screen, types.Brush, types.DynamicPaintSurface,
        types.DynamicPaintBrushSettings, types.DynamicPaintCanvasSettings, types.ParticleSettings, types.ClothSettings, types.PointCache, types.KeyingSet, types.KeyingSetPath, types.TransformOrientation,
        types.ViewLayer, types.ToolSettings, types.GPencilLayer, types.GPencilFrame, types.GPencilStroke, types.CompositorNode, types.ShaderNode, types.TextureNode,types.NodeLink, types.Material,
        types.World, types.Armature, types.Camera, types.Lattice, types.Texture, types.Histogram, types.Scopes, types.Constraint, types.Modifier, types.RenderLayer, types.RenderPass, types.Image,
        types.MovieClip, types.Mask, types.MaskLayer, types.MovieTrackingSettings, types.MovieTrackingObject, types.MovieTrackingMarker, types.MovieTrackingTrack, types.MovieTrackingPlaneMarker,
        types.MovieTrackingPlaneTrack, types.MovieTrackingStabilization, types.MovieTrackingReconstruction, types.MovieTrackingCamera, types.MovieTrackingDopesheet, types.FCurve, types.Action,
        types.TimelineMarker, types.Area, types.RegionView3D, types.SpaceView3D, types.SpaceImageEditor, types.SpaceUVEditor, types.SpaceTextEditor, types.SpaceGraphEditor, types.SpaceNLA,
        types.SpaceFileBrowser, types.SpaceProperties, types.SpaceInfo, types.SpaceOutliner, types.SpaceSequenceEditor, types.SpaceClipEditor, types.SpaceNodeEditor, types.SpaceConsole,
        types.SpacePreferences, types.Event, types.Timer, types.AnimData, types.NlaStrip, types.NlaTrack, types.FModifier, types.FCurveSample, types.FCurveModifiers, types.CompositorNodeTree,
        types.ShaderNodeTree, types.TextureNodeTree, types.GeometryNodeTree, types.OperatorMacro
    ]

    def __init__(
        self,
        path: str,
        target_classes: Tuple[type] | None = None,
        is_debug_mode: bool = False,
    ) -> None:
        """Initialize and add addon folder to module search path

        Args:
            path (str): Path to the add-on folder
            target_classes (List[type] | None, optional): Type of class to load. Defaults to None.
            is_debug_mode (bool, optional): Presence of debug mode. Defaults to False.
        """
        root = (
            dirname(path) if isfile(path) else path
        )  # 指定されたパスがファイルであれば最後のフォルダまでのパスを取得する
        self.ADDON_NAME = basename(root)  # アドオンのフォルダ名       例:addon_folder
        self.PATH = dirname(
            root
        )  # アドオンフォルダまでのパス 例:path/to/blender/script/
        self.CACHE_PATH = join(self.PATH, self.ADDON_NAME, "addon_modules.json")
        self.IS_DEBUG_MODE = is_debug_mode

        self.TARGET_CLASSES: List[type] = (
            self.DEFAULT_TARGET_CLASSES if target_classes is None else target_classes
        )

        self.__cat_name: str | None = None

        # モジュールの検索パスに登録する
        if self.PATH not in sys.path:
            sys.path.append(self.PATH)

    @staticmethod
    def is_disabled(clazz: type) -> bool:
        """Check for the presence and value of 'addon_proc_is_disabled' attribute in the target class."""
        return hasattr(clazz, "addon_proc_is_disabled") and clazz.addon_proc_is_disabled is True  # type: ignore

    def load(
        self,
        dir_priorities: List[str] | None = None,
        exclude_modules: List[str] | None = None,
        exclude_when_not_debugging: List[str] | None = None,
        cat_name: str | None = None,
    ) -> List[AddonModule]:
        """Load modules and add-on classes.

        Args:
            dir_priorities (List[str], optional): Specifies the order in which root-level directories are read.. Defaults to [].
            exclude_modules (List[str], optional): Specify folders not to be read. Defaults to [].
            exclude_when_not_debugging (List[str], optional): Specify folders to exclude when not in debug mode. Defaults to [].
            cat_name (str | None, optional): Specify the default category name for the panel. Defaults to None.

        Returns:
            List[AddonModule]: List of modules and add-on classes.
        """

        self.__cat_name = cat_name

        if self.IS_DEBUG_MODE:
            modules_and_classes = ProcFinder(self).load(
                dir_priorities, exclude_modules, exclude_when_not_debugging
            )

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
        if not hasattr(cls, "bl_idname"):
            cls.bl_idname = cls.__name__
        if (
            self.__cat_name is not None
            and issubclass(cls, types.Panel)
            and not hasattr(cls, "bl_category")
        ):
            cls.bl_category = self.__cat_name

        return cls

    def __write_cache(
        self, modules_and_classes: List[AddonModule]
    ) -> None:
        json_data: List[Dict[str, str | List[str]]] = []
        for addon_module in modules_and_classes:
            json_data.append(
                {
                    "module": addon_module.module.__name__,
                    "classes": [cls.__name__ for cls in addon_module.classes]
                }
            )

        with open(self.CACHE_PATH, "w", encoding="utf-8") as cache:
            json.dump(json_data, cache, indent=4)
