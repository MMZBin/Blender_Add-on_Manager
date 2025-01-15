# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# pyright: reportAttributeAccessIssue = false
# pyright: reportUnknownMemberType = false

from typing import Callable

from bpy.types import bpy_struct

from .addon_module import AddonClass
from ...exceptions import generate_exception_message

def disable(cls: type) -> type:
    """Classes with this decorator are excluded from the scan."""
    if not issubclass(cls, bpy_struct):
        raise TypeError('"disable" decorator can only be applied to Blender addon classes.')

    if not hasattr(cls, '_addon_manager_metadata'):
        cls._addon_manager_metadata = AddonClass(cls)
    if not isinstance(cls._addon_manager_metadata, AddonClass):
        raise TypeError(generate_exception_message(f'The data type of the "{cls.__name__}._addon_manager_metadata" property is not an "AddonClass".'))

    cls._addon_manager_metadata.is_disabled = True

    return cls

def priority(pr: int) -> Callable[[type], type]:
    """The smaller the number in the same module, the more priority is given to loading.

    Args:
        pr (int):Priority of this class in the module (the smaller the priority, the higher)

    Returns:
        Callable[[type], type]: Decorator body
    """
    def _priority(cls: type) -> type:
        if not issubclass(cls, bpy_struct):
            raise TypeError(generate_exception_message('"priority" decorator can only be applied to Blender classes.'))

        if not hasattr(cls, '_addon_manager_metadata'):
            cls._addon_manager_metadata = AddonClass(cls)
        if not isinstance(cls._addon_manager_metadata, AddonClass):
            raise TypeError(generate_exception_message(f'The data type of the "{cls.__name__}._addon_manager_metadata" property is not an "AddonClass".'))

        cls._addon_manager_metadata.priority = pr

        return cls

    return _priority
