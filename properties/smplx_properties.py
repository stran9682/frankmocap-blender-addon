import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty


def update_corrective_poseshapes(self, context):
    if self.smplx_corrective_poseshapes:
        bpy.ops.object.smplx_set_poseshapes('EXEC_DEFAULT')
    else:
        bpy.ops.object.smplx_reset_poseshapes('EXEC_DEFAULT')


class PG_SMPLXProperties(PropertyGroup):

    smplx_version: EnumProperty(
        name = "Version",
        description = "SMPL-X version",
        items = [ ("locked_head", "Locked Head", "Locked head model with removed head bun"), ("v1.1", "v1.1", "") ]
    )

    smplx_gender: EnumProperty(
        name = "Model",
        description = "SMPL-X model",
        items = [ ("female", "Female", ""), ("male", "Male", ""), ("neutral", "Neutral", "")]
    )

    smplx_uv: EnumProperty(
        name = "UV",
        description = "SMPL-X UV version",
        items = [ ("UV_2023", "2023", "Latest UV layout with two eyeball regions"), ("UV_2021", "2021", "Original Blender add-on UV layout") ]
    )

    smplx_texture: EnumProperty(
        name = "",
        description = "SMPL-X model texture",
        items = [ ("NONE", "None", ""), ("smplx_texture_f_2023.png", "Female (UV 2023)", ""), ("smplx_texture_m_2023.png", "Male (UV 2023)", ""), ("smplx_texture_f_alb.png", "Female (UV 2021)", ""), ("smplx_texture_m_alb.png", "Male (UV 2021)", ""), ("smplx_texture_rainbow.png", "Rainbow (UV 2021)", ""), ("UV_GRID", "UV Grid", ""), ("COLOR_GRID", "Color Grid", "") ]
    )

    smplx_corrective_poseshapes: BoolProperty(
        name = "Corrective Pose Shapes",
        description = "Enable/disable corrective pose shapes of SMPL-X model",
        update = update_corrective_poseshapes,
        default = True
    )

    smplx_handpose: EnumProperty(
        name = "",
        description = "SMPL-X hand pose",
        items = [ ("relaxed", "Relaxed", ""), ("flat", "Flat", "") ]
    )

    smplx_height: FloatProperty(name="Target Height [m]", default=1.70, min=1.4, max=2.2)

    smplx_weight: FloatProperty(name="Target Weight [kg]", default=60, min=40, max=110)
