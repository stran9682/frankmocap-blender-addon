# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright 2026 Max Planck Institute for Intelligent Systems

if "bpy" in locals():
    # Re-entry via `System → Reload Scripts`: force submodules to re-import so
    # edits inside subpackages take effect without restarting Blender.
    import importlib
    from . import utils, preferences, properties, operators, panels
    importlib.reload(utils)
    importlib.reload(preferences)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
else:
    from . import utils, preferences, properties, operators, panels

import bpy


def register():
    preferences.register()
    properties.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()
