# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import Any, List, Self, Tuple

from bpy.types import PropertyGroup
from bpy.props import PointerProperty # type: ignore
from bpy import types
from ..exceptions import generate_exception_message
from ..core import utils

class Property:
    """Holds information on properties."""
    def __init__(self, prop_type: type, prop: type, name: str, context: object | None = None) -> None:
        self.__prop_type = prop_type
        self.context = context
        self.__prop = PointerProperty(type=prop)
        self.__name = name

        setattr(self.__prop_type, self.__name, self.__prop)
    @property
    def prop_type(self) -> type:
        """Returns the type for which the property is registered."""
        return self.__prop_type
    @property
    def prop(self) -> types.PointerProperty:
        """property (PointerProperty)."""
        return self.__prop
    @property
    def name(self) -> str:
        """Returns the property name."""
        return self.__name

    def get(self, attr: str) -> Any | None:
        """Gets the value of the property. Returns None if the property does not exist."""
        if not hasattr(self.context, self.__name):
            return None

        return getattr(getattr(self.context, self.__name), attr)

    def set(self, attr: str, value: Any) -> bool:
        """Sets the value of the property. Returns True on success, False on failure."""
        if not hasattr(self.context, self.__name):
            return False

        setattr(getattr(self.context, self.__name), attr, value)

        return True

class PropertiesManager:
    """manage properties."""
    __instance: Self | None = None
    __is_initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, addon_name: str | None=None) -> None:
        if self.__class__.__is_initialized:
            return
        self.__class__.__is_initialized = True

        if addon_name is None:
            raise TypeError(generate_exception_message("When initializing the PropertiesManager instance, you need to specify Addon_name."))

        self.__properties: List[Property] = []
        self.ADDON_NAME: str = addon_name

    def add(self, prop_type: type, properties: List[Tuple[str, type[PropertyGroup]]] | Tuple[str, type[PropertyGroup]]) -> List[Property]:
        """Add a property.

        Args:
            prop_type (type): Destination class to which the property will be added (e.g. bpy.types.Scene).
            properties (List[Tuple[str, type]] | Tuple[str, type]): Tuple of property name and property class.

        Returns:
            List[Property]: List of properties added.
        """
        if not isinstance(properties, List):
            properties = [properties]

        registered_props: List[Property] = []

        for name, op in properties:
            if utils.is_disabled(op):
                continue

            name_with_prefix = f"{self.ADDON_NAME}_{name}"

            if hasattr(prop_type, name_with_prefix):
                continue

            registered_props.append(Property(prop_type, op, name_with_prefix))

        self.__properties += registered_props

        return registered_props

    def get(self, context: object, prop_name: str) -> Property | None:
        """Gets the properties of a specific object.

        Args:
            context (object): Target object(e.g. bpy.context.scene)
            prop_name (str): The name of the attribute (must be registered in this class).

        Returns:
            Property | None: Acquired property (None if none exists).
        """
        prop_name = f"{self.ADDON_NAME}_{prop_name}"

        for prop in self.__properties.copy():
            if prop_name != prop.name or not isinstance(context, prop.prop_type):
                continue

            prop.context = context

            return prop

        return None
        #raise ValueError(f'Property "{prop_name}" does not exist in {context}.') #属性がないとき

    def delete(self, prop_name: str) -> bool:
        """Deletes the specified property.

        Args:
            prop_name (str): The name of the attribute (must be registered in this class).

        Returns:
            bool: Whether the property existed or not.
        """
        if not prop_name.startswith(self.ADDON_NAME):
            prop_name = f"{self.ADDON_NAME}_{prop_name}"

        for prop in self.__properties.copy():
            if prop_name != prop.name:
                continue

            delattr(prop.prop_type, prop.name)

            try:
                self.__properties.remove(prop)
            except ValueError:
                pass

            return True

        return False

    def unregister(self) -> None:
        """Deletes all properties registered in this class."""
        for prop in self.__properties:
            delattr(prop.prop_type, prop.name)

        self.__properties.clear()
