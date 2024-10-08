#This program is distributed under the MIT License.
#See the LICENSE file for details.

from typing import List, Any

from .loader.proc_loader import ProcLoader

from bpy.props import PointerProperty # type: ignore
from bpy import types

class Property:
    def __init__(self, prop_type: type, prop: type, name: str, context: object | None = None) -> None:
        self.__prop_type = prop_type
        self.context = context
        self.__prop = PointerProperty(type=prop)
        self.__name = name

        setattr(self.__prop_type, self.__name, self.__prop)

    @property
    def prop_type(self) -> type: return self.__prop_type
    @property
    def prop(self) -> types.PointerProperty: return self.__prop
    @property
    def name(self) -> str: return self.__name

    def get(self, attr: str) -> Any:
        if not hasattr(self.context, self.__name): return attr
        return getattr(getattr(self.context, self.__name), attr)

    def set(self, attr: str, value: Any) -> None:
        if not hasattr(self.context, self.__name): return
        setattr(getattr(self.context, self.__name), attr, value)


class PropertiesManager:
    """Manages Blender's properties.

    Raises:
        ContextError: Thrown if this class's state is invalid.
    """
    def __init__(self, name: str) -> None:
        self.__properties: List[Property] = ([])
        self.__name: str = name

    def add(self, prop_type: type, properties: List[tuple[str, type]] | tuple[str, type]) -> List[Property]:
        """Registers a property in Blender.

        Args:
            prop_type (type): Class to register property.
            properties (List[tuple[str, type]] | tuple[str, type]): Tuple or list of tuple of property name and operator

        Raises:
            ValueError: Thrown when there is a property name conflict.

        Returns:
            List[Property]: Registered property name (with prefix)
        """
        #if not issubclass(prop_type, PropertyGroup): raise ValueError('The property class must inherit from "bpy.types.PropertyGroup".')
        if not isinstance(properties, List): properties = [properties] #リストでなければリストにする

        register_props: List[Property] = []
        for name, op in properties:
            if ProcLoader.is_disabled(op): continue

            name_with_prefix = f"{self.__name}_{name}"
            #例外をスローするとリロード機能が動作しない
            if hasattr(prop_type, name_with_prefix): # raise ValueError(f'The property name "{name_with_prefix}" already exists in "{str(prop_type)}".')
                continue

            register_props.append(Property(prop_type, op, name_with_prefix))

        self.__properties += register_props

        return register_props

    def get(self, context: object, attr: str, is_mangling: bool = True) -> Property:
        """Retrieves a property.

        Args:
            context (object): Object to get property from.
            attr (str): Property name. (Prefix optional)
            is_mangling (bool, optional): Whether to add if no prefix.. Defaults to True.

        Raises:
            ValueError: Throws if specified property doesn't exist.

        Returns:
            Property: Property object
        """
        register_name = ""
        if is_mangling and not attr.startswith(self.__name): register_name = f"{self.__name}_{attr}" #修正モードかつ接頭辞がなければ追加する
        else: register_name = attr

        #if hasattr(context, register_name): return getattr(context, register_name)

        for prop in self.__properties.copy():
            if register_name != prop.name or type(context) != prop.prop_type: continue
            prop.context = context #コンテキストを登録する
            return prop

        raise ValueError(f'Property "{attr}" does not exist in {context}.') #属性がないとき

    def delete(self, prop_name: str) -> bool:
        """Deletes the specified property.

        Args:
            prop_name (str): Property name (required if prefix exists).

        Returns:
            bool: Whether the property was registered in this class.
        """
        properties = self.__properties.copy() #ループ内でそのオブジェクトの要素数を変更できないのでコピーを作る
        for prop in properties:
            if  prop_name != prop.name: continue
            delattr(prop.prop_type, prop.name) #プロパティを削除

            try: self.__properties.remove(prop)
            except ValueError: pass

            return True

        return False

    def unregister(self) -> None:
        """Deletes all registered properties."""
        for prop in self.__properties:
            delattr(prop.prop_type, prop.name)

        self.__properties.clear()
