
from typing import Type, TypeVar

import bpy
from bpy.types import AddonPreferences

from ..addon_manager import AddonManager
from ..config import Config
from ..core.loader.addon_module import Modules

T = TypeVar('T')

class PreferencesManager:
    __preferences: Type[AddonPreferences] | None = None
    __type_hint: type | None = None

    @classmethod
    def init(cls, addon: 'AddonManager') -> None:
        cls.ADDON = addon

    @classmethod
    def set_addon_preferences(cls, pref: Type[AddonPreferences], type_hint: Type[T]) -> None:
        cls.__preferences = pref
        cls.__type_hint = type_hint


    @classmethod
    def get(cls) -> T:
        if cls.__preferences is None or cls.__type_hint is None:
            raise AttributeError("Addon preferences not set!")
        return bpy.context.preferences.addons[Config().manifest["name"]].preferences # type: ignore

PreferencesManager.get()
