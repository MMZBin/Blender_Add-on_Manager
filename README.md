This library uses English that has been machine-translated from Japanese.

__[日本語のreadmeはこちら](README.ja.md)__

# __This script is under development and subject to destructive changes.__

# Blender_Add-on_Manager
Script to dynamically register and unregister files that make up Blender add-ons.
It can automatically perform tedious tasks such as registering, deregistering, deactivating, prioritizing, and registering shortcut keys for classes.
It has been tested with Blender 4.1.

The base classes to be loaded are written in the `TARGET_CLASSES` class variable in the `ProcLoader` class in [`/manager/core/proc_loader.py`](/manager/core/proc_loader.py).

We have tried to cover the basic classes, but please let us know if any classes are missing or superfluous.

You can also specify arbitrary classes.

## Quick Start
1. place `manager` folder in the add-ons folder
2. create an instance of the `AddonManager` class in the `__init__.py` file
3. wrap the `register()` and `unregister()` methods of the `AddonManager` instance in a global function with the same name
4. place the file containing the operator you want to use in the specified folder

### Sample Code

`__init__.py`
```python
from .manager.core.register_addon import AddonManager #Import the AddonManager class

#Info of addon
bl_info = {
    "name": 'Addon_name',.
    "author": 'your_name', 'version': (1, 0, 0)
    "blender": (4, 1, 0), 'location': "View3D
    "category": 'General'
}

addon = AddonManager(__file__, locals()) #Create an instance of the AddonManager class

#Wrap the 'register()' and 'unregister()' methods
def register(): addon.register()
def unregister(): addon.unregister()
```
`operators/foo.py`
```python
"""Script to display a notification when the F1 key is pressed."""

from bpy.types import Operator

#Import "Key" data class
from . .manager.core.keymap_manager import Key

class FOO_OT_Sample(Operator):.
    bl_idname = "foo.sample_operator"
    bl_label = "Test Operator"
    bl_description = "Test."

    def execute(self, context):.
        self.report({'INFO'}, "FOO_OT_Sample!!!!!!!!!!!!!!")

        return {"FINISHED"}

def register(manager):
    manager.keymap.add(Key(FOO_OT_Sample, 'F1')) #set 'FOO_OT_Sample' operator to run when the F1 key is pressed
```


## Function
- Registers and unregisters classes for all add-ons in the add-ons folder, including subdirectories.
    - Folders starting with `.` or `manager` folders, and folders specified in the constructor of the AddonManager class are ignored.
- A list named `disable` is defined in `__init__.py` in each directory, and the module name is written to ignore that module.
    - The path of the module is relative to the directory where the `__init__.py` file in which the listing is defined resides.
        - Example (for `__init__.py` files in `operators` folder): `disable = ['your_operator']`
- Define a list named `priority` in `__init__.py` in each directory, and write the module names so that the modules are loaded in that order.
        - Example (for `__init__.py` file in `operators` folder): `priority = ['your_operator', 'your_operator2']`
    - If not specified, the reading order is not guaranteed.
- Certain classes can be ignored by using the `disable` decorator.
    - Example: `@disable`.
- The `priority` decorator can be used to control the loading order of specific classes.
    - The lower the value above `0`, the higher the priority.
    - Example: `@priority(42)`
- The `KeymapManager` class can be used to register shortcut keys.
    - Deletion of keymaps is automatic.
    - Example: `manager.keymap.add(Key(FOO_OT_YourOperator, 'A'))`
- The `PropertiesManager` class can be used to register, reference and unregister property groups. (The `addon_name` argument of the `AddonManager` class is required in the initial configuration.)
    - Deleting a property is automatic.
    - Examples
        - Registering a property: `manager.property.add(Scene, [("your_properties", YourPropertyGroupClass)])`
        - Referencing properties:
        ```python
            prop = manager.property.get(bpy.context.scene, "your_properties") #Get properties
            value = prop.get('your_attribute') #Get the attributes of a property
            prop.set('your_attribute', 'Hello, world!') #set the value of the property
        ```
- The `bl_idname` can be omitted; if it is omitted, the class name is automatically assigned. (If you have a class name conflict, set it explicitly.)
- For classes inheriting from `bpy.types.Panel`, you can omit the `bl_category` attribute by setting any name in the constructor of `AddonManager`. (If you set it explicitly, it will take precedence.)
- Some features for debugging are also included.
    - Some debugging features can be enabled by the `is_debug_mode` argument of the `AddonManager` class.
        - If disabled, modules in the `debug` directory will be ignored if it exists directly under each directory.
        - When enabled, modules in the `debug` directory will be loaded, and modules will be reloaded when `script.reload` is executed.

- If each module to be loaded has a register() or unregister() function, it will be called when the add-on is registered or unregistered.
    - When these functions take arguments, the corresponding `AddonManager` instance is passed.
- If the addon class has a class method named `set_manager()`, the corresponding `AddonManager` instance is passed when the class is registered with Blender.
    - Example:
        ```python
            class AddonClass(bpy.types.Operator):.
                @classmethod
                def set_manager(manager):.
                    self.__manager = manager
        ```
- You can use Blender standard format translation dictionaries to support multiple languages.
- Several constants are provided in `constants.py`, such as operator return values and mode names, to reduce typing time and typos.
- The `DrawText` class can be used to simplify the drawing of text. (undocumented)