import bpy

from ..utils.constants import (
    ADDON_ROOT,
    SMPLX_MODELFILE_300,
    SMPLX_MODELFILE_LH,
)

_BODY_MODELS = (
    ("SMPL-X Locked Head (no head bun)", SMPLX_MODELFILE_LH),
    ("SMPL-X v1.1 (head bun)", SMPLX_MODELFILE_300),
)


class SMPLX_AP_Preferences(bpy.types.AddonPreferences):
    # Strip trailing ".preferences" so bl_idname matches the addon's
    # top-level package, not this submodule.
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        layout.label(text="Installed SMPL-family body models:")

        data_dir = ADDON_ROOT / "data"
        col = layout.column(align=True)

        header = col.split(factor=0.5, align=True)
        header.label(text="BODY MODEL")
        header.label(text="STATUS")

        for display_name, filename in _BODY_MODELS:
            row = col.split(factor=0.5, align=True)
            row.label(text=display_name)
            status = "Installed" if (data_dir / filename).is_file() else "Not installed"
            row.label(text=status)


classes = (SMPLX_AP_Preferences,)
