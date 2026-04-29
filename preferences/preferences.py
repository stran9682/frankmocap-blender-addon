import bpy

from ..utils.model_spec import MODELS, is_variant_installed

_VARIANT_LABELS = {
    "locked_head": "Locked Head (no head bun)",
    "v1.1": "v1.1 (head bun)",
    "default": "",
}


class SMPLX_AP_Preferences(bpy.types.AddonPreferences):
    # Strip trailing ".preferences" so bl_idname matches the addon's
    # top-level package, not this submodule.
    bl_idname = __package__.rsplit(".", 1)[0]

    def draw(self, context):
        layout = self.layout
        layout.label(text="Installed SMPL-family body models:")

        col = layout.column(align=True)

        header = col.split(factor=0.5, align=True)
        header.label(text="BODY MODEL")
        header.label(text="STATUS")

        for spec in MODELS.values():
            for variant_key in spec.blend_files:
                variant_label = _VARIANT_LABELS.get(variant_key, variant_key)
                display_name = f"{spec.display_name} {variant_label}".strip()
                row = col.split(factor=0.5, align=True)
                row.label(text=display_name)
                status = "Installed" if is_variant_installed(spec, variant_key) else "Not installed"
                row.label(text=status)


classes = (SMPLX_AP_Preferences,)
