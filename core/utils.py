# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# pyright: reportUnknownMemberType = false
# pyright: reportUnknownArgumentType = false
# pyright: reportAttributeAccessIssue = false

from bpy.types import bpy_struct
from .loader.addon_module import AddonClass

def isinstance(obj: object, class_or_tuple: type | tuple[type]) -> bool:
    """Compare the type of instance.

    Warnings:
        Since the standard "isinstance" function does not work as intended, this function uses the module name as an alternative means of comparison.
        Note that it is not guaranteed that the types are strictly equal.
    """
    if type(class_or_tuple) == tuple:
        for cls in class_or_tuple:
            if cls.__module__.endswith(obj.__module__):
                return True

        return False
    else:
        return class_or_tuple.__module__.endswith(obj.__module__)

def is_disabled(cls: type[bpy_struct]) -> bool:
    """class is disabled or not."""
    if hasattr(cls, "_addon_manager_metadata") and isinstance(cls._addon_manager_metadata, AddonClass):
        return cls._addon_manager_metadata.is_disabled # type: ignore
    return False
