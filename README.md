# Blender Add-on Manager

__Note: The English used in this project is based on machine translation from Japanese and may contain unnatural expressions.__

[日本語のREADMEはこちらから](/README-ja.md)

## Overview
Blender Add-on Manager is a framework designed to support Blender add-on development using the Blender Python API.

It abstracts tasks such as registering and unregistering add-on-related classes, managing keymaps, and handling properties.

## Usage
Place this repository in your project folder and create modules within the `modules` folder to enable its functionality.

## Features
- Automation of registering and unregistering add-on-related classes (`Operator`, `Panel`, `PropertyGroup`, etc.)
- Abstraction of keymap registration and unregistration
- Abstraction of property group registration, retrieval, unregistration, and type definition provision.
- Provision of some predefined constants

### Add-on Class Management ([AddonManager](/addon_manager.py))
- Automatically retrieves and registers/unregisters modules within the `modules` folder and the classes related to add-ons defined in them (`bpy.types.bpy_struct` subclasses).
    - However, subclasses of `bpy.types.WorkSpaceTool` are excluded, so please register them manually.
- Create a `data` folder directly under the manager's folder to store settings and cache.
- If the file system is scanned (when `is_debug_mode = true` or `module.pkl` does not exist), logs will be displayed in the console during startup.
    - Once loading is complete, a `modules.pkl` file will be created under the `data` folder. If `is_debug_mode = false`, modules will be loaded from this cache.
    - __Unless there is a special reason, it is better to set `is_debug_mode = false` and not include `modules.pkl` when releasing your add-ons.__

- If a `register()` function or `unregister()` function exists in each module, they will be called during the add-on registration and unregistration process.
    - If these functions take arguments, the corresponding [AddonManager](/addon_manager.py) instance will be passed as an argument.
    - These functions will not be called if the module is specified in `disabled`.
- `config.toml`
    - Stores settings related to loading.
        - `is_debug_mode` (boolean)
            - Specifies whether to enable debug mode.
                - `true`: Always scans the file system.
                - `false`: Scans the file system only if `modules.pkl` does not exist; otherwise, loads from cache.
        - `disabled` (list of strings) (optional)
            - Specifies modules to disable.
            - The specified modules and their submodules will be ignored.
            - Example:
                ```toml
                disabled = [
                    "spam.ham" # Ignores modules under /modules/spam/ham.
                ]
                ```
        - `priorities` (list of strings) (optional)
            - Specifies the loading order of modules.
            - Example:
                ```toml
                # Registers spam first, followed by eggs in Blender.
                priorities = [
                    "spam",
                    "eggs"
                ]
                ```
        - `exclude_patterns`(list of string)(optional)
            - The strings specified in this field are ignored.
            - Example:
            ```toml
                exclude_patterns = [
                    "__" # Modules with "__" in the path will be ignored.
                ]
            ```
- [decorators](/core/loader/decorators.py)
    - Configures information about add-on-related classes in modules.
        - `@disable` decorator
            - Classes with this decorator are ignored during loading.
        - `@priority` decorator
            - Classes with smaller priority numbers are loaded first.
            - Only compared within the same module.

### Keymap Management ([KeymapManager](/features/keymap_manager.py))
- Abstracts keymap management.
- Static class.
- Use the `add()` method to register keymaps and the `delete()` method to remove them.
- Keymaps are automatically removed when the add-on itself is unregistered from Blender.
- Example:
```python
def register() -> None:
    KeymapManager.add(Key(Your_Operator, "F1", "PRESS"))
```

### Property group Management ([PropertyGroupManager](/features/property_group_manager.py))
- Abstracts the management of property groups.
- Static class.
- Properties are registered based on their type and key, and attached to Blender in the form of `[addon_folder_name]_[property_class]_[ID(PropertyGroup or type hint class)]_[key]`.
- Use the `add()` method to register properties and the `delete()` method to remove them.
- Retrieve properties using the `get()` method.
- property groups are automatically removed when the add-on itself is unregistered from Blender.
- By setting type definitions for each property, you can utilize type hinting, but if there are mismatches between the field names or types of the property and its type definition, the type hint may not work correctly.
    - In practice, it simply assigns the property type object to the type definition type, ignoring warnings.
- Example:
```python
# Example of defining a property group

# The property body
class Your_PropertyGroup(bpy.types.PropertyGroup):
    bool_prop: bpy.props.BoolProperty(name="Your bool prop")
    int_prop:  bpy.props.IntProperty(name="Your int prop")

# Type definition (append "Type" to the name of the property body class) (optional)
# This class is used only for type annotations and does not affect the actual data.
class Your_PropertyGroupType:
    bool_prop: bool
    int_prop: int

# Registration
def register() -> None:
    PropertyGroupManager.add(bpy.types.Scene, Your_PropertyGroup, Your_PropertyGroupType)
    # PropertyGroupManager.add(bpy.types.Scene, Your_PropertyGroup, Your_PropertyGroupType, "custom_key") # By specifying a key, you can register multiple properties of the same type.

# Usage
prop  = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroupType) # Retrieves the property of the specified type and key(If a type definition is used, it must be accessed using that class to work.).
# prop = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroupType, "custom_key")
# prop = PropertyGroupManager.get(bpy.context.scene, Your_PropertyGroup) # If you do not use type definitions, specify the type of the property body.

value = prop.bool_prop # Retrieve a property
prop.int_prop = 100    # Set a property
```

### Constants ([constants](/constants.py))
- Includes constants for values such as return codes for the `execute()` method of operators and object types.

## Samples
Example of folder structure:
```
your_addon/
├── manager/
│   ├── core
│   │   └── ...omitted...
│   ├── features
│   │   └── ...omitted...
│   └── ...omitted...
├── modules/
│   └── [Place your modules here]
├── __init__.py
└── blender_manifest.toml
```
Example of `__init__.py`:
```python
from .manager.addon_manager import AddonManager

addon = AddonManager()

# The AddonManager.register() and unregister() methods must be called when an add-on is registered and unregistered.

def register() -> None:
    addon.register()


def unregister() -> None:
    addon.unregister()

```
Example of module (panel):

`/modules/sample_panel.py`
```python
from bpy.types import Panel, Context

class SamplePanel(Panel):
    bl_label = "Sample operator"
    bl_idname = "VIEW3D_PT_sample_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'sample'

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.label(text="This is sample panel.")

# These functions are not required.

def register() -> None:
    print("sample_panel.py is now registered.")

def unregister() -> None:
    print("sample_panel.py is now unregistered.")

```

## Notes
- When importing modules, using the editor's auto-completion (in the form `from manager. ...`) may result in runtime errors.
    - If you encounter an error, try switching to relative imports (e.g., `from ...manager import ...`).

## License

This program is licensed under the MIT License.
See the [LICENSE](./LICENSE) file for more details.

