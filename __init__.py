# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from .manager.addon_manager import AddonManager

addon = AddonManager()

# The AddonManager.register() and unregister() methods must be called when an add-on is registered and unregistered.

def register() -> None:
    """register the addon."""
    addon.register()


def unregister() -> None:
    """unregister the addon."""
    addon.unregister()
