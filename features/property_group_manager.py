# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# pyright: reportUnknownMemberType = false

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Self, Type, Any, TypeVar

from collections import defaultdict

from bpy import props
from bpy.types import bpy_struct, PropertyGroup

from ..core.utils import is_disabled
from ..exceptions import generate_exception_message

if TYPE_CHECKING:
    from ..addon_manager import AddonManager

T = TypeVar('T')

PropertyGroupWithTypeHint = tuple[Type[PropertyGroup], Type[T]]

class PropertyGroupManager:
    """Manage PropertyGroups."""
    __instance: Self | None = None
    __is_initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, addon: AddonManager | None=None) -> None:
        if self.__class__.__is_initialized:
            return
        self.__class__.__is_initialized = True

        if addon is None:
            raise TypeError(generate_exception_message("When initializing the PropertiesManager instance, you need to specify Addon."))

        self.ADDON: AddonManager = addon

        self.__properties: Dict[type, List[str]] = defaultdict(lambda: [])

    def generate_property_name(self, name: str, key: str="default") -> str:
        """Generates property names from names and keys."""
        return '_'.join((self.ADDON.ADDON_FOLDER_NAME, name, key))

    def add(self, target_type: Type[bpy_struct], prop_type: Type[PropertyGroup], key: str="default") -> bool:
        """Add PropertyGroup.

        Args:
            target_type (Type[bpy_struct]): Class to add property groups(for example: bpy.types.Scene).
            prop_type (Type[PropertyGroup]): PropertyGroup to be added.
            key (str, optional): Key to identify PropertyGroups of the same type. Defaults to "default".

        Raises:
            TypeError: Raises when a property with the same name has already been added.

        Returns:
            bool: Returns "False" if the class is disabled or already registered.
        """
        if is_disabled(target_type):
            return False

        attr_name = self.generate_property_name(prop_type.__name__, key)

        if hasattr(target_type, attr_name):
            prop = getattr(target_type, attr_name)
            if not isinstance(prop, prop_type):
                raise TypeError(generate_exception_message(f'Property "{attr_name}" already exists in "{target_type.__name__}.'))

            return False

        setattr(target_type, attr_name, props.PointerProperty(type=prop_type))

        self.__properties[target_type].append(attr_name)

        return True

    def get(self, obj: object, prop_type: Type[T], key: str="default") -> T:
        """Gets the PropertyGroup.

        Args:
            obj (object): Object to get property(for example: bpy.context.scene)
            prop_type (Type[T]): PropertyGroup to get (if "Type" is at the end, it is treated as a type definition)
            key (str, optional): Key to identify PropertyGroups of the same type. Defaults to "default".

        Raises:
            TypeError: Raises when the property type is different from that specified.
            ValueError: Raises when the property with the specified name does not exist.

        Returns:
            T: PropertyGroup Type.
        """
        prop_type_name = prop_type.__name__.removesuffix("Type")

        attr_name = self.generate_property_name(prop_type_name, key)

        if hasattr(obj, attr_name):
            prop = getattr(obj, attr_name)


            if not type(prop).__name__ == prop_type_name:
                raise TypeError(generate_exception_message(f'''Property "{attr_name}" is not of type "{prop_type.__name__}.
                                                               Possible duplicate property name."'''))

            return prop # type: ignore

        raise ValueError(f'''The property "{attr_name} does not exist in "{type(obj).__name__}".
                             Please make sure that the class and key are correct.''')

    def delete(self, prop_type: Type[PropertyGroup], key: str="default") -> bool:
        """Deletes the specified PropertyGroup.

        Args:
            prop_type (Type[PropertyGroup]): Property to be deleted.
            key (str, optional): Key to identify PropertyGroups of the same type. Defaults to "default".

        Raises:
            AttributeError: Raises when the specified property does not exist.

        Returns:
            bool: Whether the property was actually deleted.
        """
        for prop in self.__properties.copy().keys():
            if not prop == prop_type:
                continue

            attr_name = self.generate_property_name(prop_type.__name__, key)

            try:
                delattr(prop, attr_name)
            except AttributeError as e:
                raise AttributeError(f'Property "{attr_name}" does not exists in "{prop_type.__name__}.') from e

            try:
                self.__properties[prop].remove(attr_name)
            except ValueError:
                pass

            return True

        return False

    def unregister(self) -> None:
        """Delete all PropertyGroups."""
        for prop, attr_names in self.__properties.items():
            for name in attr_names:
                try:
                    delattr(prop, name)
                except ValueError:
                    pass

        self.__properties.clear()
