# Blender Add-on Manager

__Note: The English used in this project is based on machine translation from Japanese and may contain unnatural expressions.__

[日本語のREADMEはこちらから](/README.ja.MD)

## Overview
Blender Add-on Manager is a framework designed to support Blender add-on development using the Blender Python API.

It abstracts tasks such as registering and unregistering add-on-related classes, managing keymaps, and handling custom properties.

## Usage
Place this repository in your project folder and create modules within the `modules` folder to enable its functionality.

## Features
- Automation of registering and unregistering add-on-related classes (`Operator`, `Panel`, `PropertyGroup`, etc.)
- Abstraction of keymap registration and unregistration
- Abstraction of custom property registration, retrieval, and unregistration
- Provision of some predefined constants

### Add-on Class Management ([AddonManager](/addon_manager.py))
- Automatically retrieves and registers/unregisters modules within the `modules` folder and the classes related to add-ons defined in them (`bpy.types.bpy_struct` subclasses).
- If the file system is scanned (when `is_debug_mode = true` or `module.pkl` does not exist), logs will be displayed in the console during startup.
    - Once loading is complete, a `modules.pkl` file will be created under the [data](/data/) folder. If `is_debug_mode = false`, modules will be loaded from this cache.

- If a `register()` function or `unregister()` function exists in each module, they will be called during the add-on registration and unregistration process.
    - If these functions take arguments, the corresponding [AddonManager](/addon_manager.py) instance will be passed as an argument.
    - These functions will not be called if the module is specified in `disabled`.
        - [config.toml](/data/config.toml)
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
        - [decorators](/core/loader/decorators.py)
            - Configures information about add-on-related classes in modules.
                - `@disable` decorator
                    - Classes with this decorator are ignored during loading.
                - `@priority` decorator
                    - Classes with smaller priority numbers are loaded first.
                    - Only compared within the same module.

### Keymap Management ([KeymapManager](/features/keymap_manager.py))
- Abstracts keymap management.
- Implemented as a singleton class.
- Use the `add()` method to register keymaps and the `delete()` method to remove them.
- Keymaps are automatically removed when the add-on itself is unregistered from Blender.
- Example:
```python
def register() -> None:
    KeymapManager().add(Key(Your_Operator, "F1", "PRESS"))
```

### Custom Property Management ([PropertiesManager](/features/properties_manager.py))
- Abstracts custom property management.
- Implemented as a singleton class.
- Add `[add-on folder name]_` to the property name to avoid name conflicts.
- Use the `add()` method to register properties and the `delete()` method to remove them.
- Get a property with the `get()` method. __Note__ that it is a [Property](/features/properties_manager.py) object, not the property itself.
- Properties are automatically removed when the add-on itself is unregistered from Blender.
- Example:
```python
# Registration
def register() -> None:
    PropertiesManager().add(bpy.types.Scene, ("your_prop_name", Your_PropertyGroup))
# Usage
PropertiesManager().get(bpy.context.scene, "your_prop_name")
value = prop.get("your_prop_attribute") # Get property
prop.set("your_prop_attribute", True)   # Set property
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

