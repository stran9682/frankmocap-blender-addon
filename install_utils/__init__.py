if "bpy" in locals():
    import importlib
    from . import install_scripts, utils
    importlib.reload(install_scripts)
    importlib.reload(utils)
else:
    from . import install_scripts, utils

import bpy

from .utils import *
from .install_scripts import *