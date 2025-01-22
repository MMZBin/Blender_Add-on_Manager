# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import List, Tuple

from dataclasses import dataclass

from bpy import context
from bpy.types import KeyMap, KeyMapItem


from ..debug.logger import Logger
from ..core import utils

@dataclass
class KeyInfo:
    idname:       str | type               # 対象のキー
    type:         str | int | None         # 追加のキー
    value:        str | int | None         # 実行するキーの状態(トリガー)
    any:          bool             = False
    shift:        bool             = False
    ctrl:         bool             = False
    alt:          bool             = False
    oskey:        bool             = False
    key_modifier: str | int | None = 'NONE'
    direction:    str | int | None = 'ANY'
    repeat:       bool             = False
    head:         bool             = False


class KeyMapManager:
    """manage keymap."""
    __keymap_data: List[Tuple[KeyMap, KeyMapItem]] = []

    @classmethod
    def add(cls, keys: List[KeyInfo] | KeyInfo,
            name: str = 'Window', space_type: str = 'EMPTY', region_type: str = 'WINDOW',
            modal: bool = False, tool: bool = False) -> List[Tuple[KeyMap, KeyMapItem]]:
        """_summary_

        Args:
            keys (List[Key] | Key): Key to register.
            name (str, optional): Keymap Name. Defaults to 'Window'.
            space_type (str, optional): space type. Defaults to 'EMPTY'.
            region_type (str, optional): region type. Defaults to 'WINDOW'.
            modal (bool, optional): modal. Defaults to False.
            tool (bool, optional): tool. Defaults to False.

        Returns:
            List[tuple[KeyMap, KeyMapItem]]: Registered key information
        """
        if not isinstance(keys, List):
            keys = [keys] #リストでなければリストにする

        key_config = context.window_manager.keyconfigs.addon #キーコンフィグ

        if not key_config:
            return [] #キーコンフィグがなければ中止

        keymap_data: List[Tuple[KeyMap, KeyMapItem]] = [] #今回追加したショートカットキーを入れるリスト

        #指定したロケーションでのキーマップを取得する
        keymap = key_config.keymaps.new(
            name=name, space_type=space_type, region_type=region_type, modal=modal, tool=tool
        )

        for k in keys:
            if not isinstance(k.idname, str) and utils.is_disabled(k.idname):
                continue

            #キーマップにアイテムを追加する
            keymap_item = keymap.keymap_items.new(
                k.idname if isinstance(k.idname, str) else k.idname.bl_idname, # type: ignore
                k.type, k.value,
                key_modifier=k.key_modifier, any=k.any, shift=k.shift, ctrl=k.ctrl, alt=k.alt, oskey=k.oskey
            )

            keymap_data.append((keymap, keymap_item))

        cls.__keymap_data += keymap_data

        return keymap_data

    @classmethod
    def delete(cls, subject: Tuple[KeyMap, KeyMapItem] | type) -> bool:
        """Deletes the specified key.

        Args:
            subject (Tuple[KeyMap, KeyMapItem] | type): Key to delete

        Returns:
            bool: Whether the keymap existed or not.
        """
        if type(subject) == tuple:
            try:
                subject[0].keymap_items.remove(subject[1])
                cls.__keymap_data.remove(subject)
                return True
            except ValueError:
                return False
        else:
            is_deleted = False
            for keymap, keymap_item in cls.__keymap_data:
                if not keymap_item.idname == subject.bl_idname: # type: ignore
                    continue
                keymap.keymap_items.remove(keymap_item)
                is_deleted = True
            return is_deleted

    @classmethod
    def unregister(cls) -> None:
        """Deletes all keymap registered in this class."""
        for kms in cls.__keymap_data:
            cls.delete(kms)

        cls.__keymap_data.clear()

        Logger.LOGGER.debug("Keymaps has been unregistered.")
