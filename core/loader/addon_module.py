# This program is distributed under the MIT License.
# See the LICENSE file for details.

from typing import List
from types import ModuleType

from dataclasses import dataclass

@dataclass
class AddonModule:
    """Add-on modules and classes."""
    module: ModuleType
    classes: List[type]