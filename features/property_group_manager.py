# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# pyright: reportUnknownMemberType = false

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from collections import defaultdict
from dataclasses import dataclass

import bpy
from bpy.types import bpy_struct, PropertyGroup

from ..debug.logger import Logger
from ..core.utils import is_disabled
from ..exceptions import generate_exception_message

if TYPE_CHECKING:
    from ..addon_manager import AddonManager

T = TypeVar('T')

@dataclass
class PropertyInfo:
    prop_type:           Type[PropertyGroup]
    type_hint:           type | None         = None      # Type hint for the property group.
    key:                 str                 = "default" # Key to identify PropertyGroups of the same type.

    name:                str | None          = ""
    description:         str | None          = ""
    translation_context: str | None          = ""
    options:             Any | None          = 'ANIMATABLE'
    tags:                Any | None          = 'set()'
    poll:                Any | None          = None
    update:              Any | None          = None

class PropertyGroupManager:
    """Manage PropertyGroups."""
    __properties: Dict[type, List[str]] = defaultdict(lambda: [])

    @classmethod
    def init(cls, addon: AddonManager) -> None:
        cls.ADDON = addon

    @classmethod
    def generate_property_name(cls, name: str, key: str, id: int) -> str:
        """Generates property names from names and keys."""
        return '_'.join((cls.ADDON.ADDON_FOLDER_NAME, str(id), name, key))

    @classmethod
    def add(cls, target_type: Type[bpy_struct], props: PropertyInfo | List[PropertyInfo]) -> None:
        """Add PropertyGroup.

        Args:
            target_type (Type[bpy_struct]): Class to add property groups(for example: bpy.types.Scene).
            props (PropertyInfo | List[PropertyInfo]): PropertyGroup(s) to add.

        Raises:
            TypeError: Raises when a property with the same name has already been added.
        """
        for prop in props if isinstance(props, list) else [props]:
            if is_disabled(prop.prop_type):
                continue

            attr_name = cls.generate_property_name(prop.prop_type.__name__, prop.key, id(prop.type_hint if prop.type_hint is not None else prop.prop_type))

            if hasattr(target_type, attr_name):
                prop = getattr(target_type, attr_name)
                if not isinstance(prop, prop.prop_type):
                    raise TypeError(generate_exception_message(f'Property "{attr_name}" already exists in "{target_type.__name__}.'))

                continue

            setattr(target_type, attr_name, bpy.props.PointerProperty(type=prop.prop_type))

            Logger.LOGGER.debug(f'Property group "{prop.prop_type.__name__}" is registered to type "{target_type.__name__}" with name "{attr_name}".')

            cls.__properties[target_type].append(attr_name)

    @classmethod
    def get(cls, obj: object, prop_type: Type[T], key: str="default") -> T:
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

        attr_name = cls.generate_property_name(prop_type_name, key, id(prop_type))

        if hasattr(obj, attr_name):
            prop = getattr(obj, attr_name)


            if not type(prop).__name__ == prop_type_name:
                raise TypeError(generate_exception_message(f'''Property "{attr_name}" is not of type "{prop_type.__name__}.
                                                               Possible duplicate property name."'''))

            return prop # type: ignore

        raise ValueError(f'''The property "{attr_name} does not exist in "{type(obj).__name__}".
                             Please make sure that the class and key are correct.''')

    @classmethod
    def delete(cls, target_type: type, prop_type: type, key: str="default") -> bool:
        """Deletes the specified PropertyGroup.

        Args:
            target_type (Type[bpy_struct]): Class to delete property groups(for example: bpy.types.Scene).
            prop_type (Type[PropertyGroup]): Property to be deleted. If a type definition is used, specify the class for the type definition.
            key (str, optional): Key to identify PropertyGroups of the same type. Defaults to "default".

        Raises:
            AttributeError: Raises when the specified property does not exist.

        Returns:
            bool: Whether the property was actually deleted.
        """
        for prop in cls.__properties.copy().keys():
            if not prop == prop_type:
                continue

            attr_name = cls.generate_property_name(prop_type.__name__, key, id(prop_type))

            try:
                delattr(target_type, attr_name)
            except AttributeError as e:
                raise AttributeError(f'Property "{attr_name}" does not exists in "{target_type.__name__}.') from e

            try:
                cls.__properties[prop].remove(attr_name)
            except ValueError:
                pass

            Logger.LOGGER.debug(f'Property group "{prop_type.__name__}" is unregistered to type "{target_type.__name__}" with name "{attr_name}".')

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

        Logger.LOGGER.debug("Property group has been unregistered.")
