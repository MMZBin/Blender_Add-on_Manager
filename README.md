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

### Add-on Class Management ([AddonManager](/manager/addon_manager.py))
- Automatically retrieves and registers/unregisters modules within the `modules` folder and the classes related to add-ons defined in them (`bpy.types.bpy_struct` subclasses).
- If the file system is scanned (when `is_debug_mode = true` or `module.pkl` does not exist), logs will be displayed in the console during startup.
    - [config.toml](/manager/data/config.toml)
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
    - [decorators](/manager/core/loader/decorators.py)
        - Configures information about add-on-related classes in modules.
            - `@disable` decorator
                - Classes with this decorator are ignored during loading.
            - `@priority` decorator
                - Classes with smaller priority numbers are loaded first.
                - Only compared within the same module.

### Keymap Management ([KeymapManager](/manager/features/keymap_manager.py))
- Abstracts keymap management.
- Implemented as a singleton class.
- Use the `add()` method to register keymaps and the `delete()` method to remove them.
- Keymaps are automatically removed when the add-on itself is unregistered from Blender.
- Example:
```python
def register() -> None:
    KeymapManager().add(Key(Your_Operator, "F1", "PRESS"))
```

## License

This program is licensed under the MIT License.
See the [LICENSE](./LICENSE) file for more details.

