#This program is distributed under the MIT License.
#See the LICENSE file for details.

# pyright: reportUnknownMemberType = false
# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownArgumentType = false

from dataclasses import dataclass
from typing import List

from .proc_loader import ProcLoader

from bpy import context
from bpy.types import KeyMap, KeyMapItem

#ショートカットキーの情報
@dataclass
class Key:
    """Hold information for registering to the keymap
    """

    operator:     type           #オペレーターのクラスオブジェクト
    key:          str            #対象のキー
    key_modifier: str  = 'NONE'  #追加のキー
    trigger:      str  = 'PRESS' #実行するキーの状態(トリガー)
    #特殊キーの使用の有無
    any:          bool = False   #特殊キーをどれか
    shift:        bool = False
    ctrl:         bool = False
    alt:          bool = False
    oskey:        bool = False

#ショートカットキーを登録する
class KeymapManager:
    """Manage the keymap.
    """
    def __init__(self) -> None:
        self.__shortcut_keys: List[tuple[KeyMap, KeyMapItem]] = []

    #ショートカットキーを追加する
    def add(self, keys: List[Key] | Key,
            name: str = 'Window', space_type: str = 'EMPTY', region_type: str = 'WINDOW',
            modal: bool = False, tool: bool = False) -> List[tuple[KeyMap, KeyMapItem]]:
        """Add keymaps

        Args:
            keys (List[Key] | Key): Information of key to register.
            name (str, optional): keymap identifier. Defaults to 'Window'.
            space_type (str, optional): keymap's valid space and range. Defaults to 'EMPTY'.
            region_type (str, optional): _description_. Defaults to 'WINDOW'.
            modal (bool, optional): presence of modal modes. Defaults to False.
            tool (bool, optional): presence of tool modes. Defaults to False.

        Returns:
            List[tuple[KeyMap, KeyMapItem]]: Registered key's keymap and keymap items
        """
        if not isinstance(keys, List): keys = [keys] #リストでなければリストにする

        key_config = context.window_manager.keyconfigs.addon #キーコンフィグ

        if not key_config: return [] #キーコンフィグがなければ中止

        shortcut_keys: List[tuple[KeyMap, KeyMapItem]] = [] #今回追加したショートカットキーを入れるリスト

        #指定したロケーションでのキーマップを取得する
        keymap = key_config.keymaps.new(
            name=name, space_type=space_type, region_type=region_type, modal=modal, tool=tool
        )

        for k in keys:
            if ProcLoader.is_disabled(k.operator): continue

            #キーマップにアイテムを追加する
            keymap_item = keymap.keymap_items.new(
                k.operator.bl_idname, k.key, k.trigger,
                key_modifier=k.key_modifier, any=k.any, shift=k.shift, ctrl=k.ctrl, alt=k.alt, oskey=k.oskey
            )

            shortcut_keys.append((keymap, keymap_item))

        self.__shortcut_keys += shortcut_keys

        return shortcut_keys

    def delete(self, subject: tuple[KeyMap, KeyMapItem] | type) -> bool:
        """Delete the keymap.

        Args:
            subject (tuple[KeyMap, KeyMapItem] | type): Pair of keymap and item or operator to be deleted.

        Returns:
            bool: Whether the target for deletion existed or not.
        """
        if type(subject) == tuple:
            try:
                subject[0].keymap_items.remove(subject[1])
                self.__shortcut_keys.remove(subject)
                return True
            except ValueError:
                return False
        else:
            is_deleted = False
            for keymap, keymap_item in self.__shortcut_keys:
                if not keymap_item.idname == subject.bl_idname: continue
                keymap.keymap_items.remove(keymap_item)
                is_deleted = True
            return is_deleted

    def unregister(self) -> None:
        """Delete all keymaps registered in this class."""

        for kms in self.__shortcut_keys:
            self.delete(kms)

        self.__shortcut_keys.clear()
