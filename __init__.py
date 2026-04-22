# Copyright 2024 Perceiving Systems, Max Planck Institute for Intelligent Systems

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "SMPL-X for Blender",
    "author": "Joachim Tesch, Max Planck Institute for Intelligent Systems",
    "version": (2026, 4, 10),
    "blender": (4, 0, 0),
    "location": "Viewport > Right panel",
    "description": "SMPL-X for Blender",
    "wiki_url": "https://smpl-x.is.tue.mpg.de/",
    "category": "SMPL-X"}

import bpy

from . import properties, operators


class SMPLX_PT_Model(bpy.types.Panel):
    bl_label = "SMPL-X Model"
    bl_category = "SMPL-X"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):

        layout = self.layout
        col = layout.column(align=True)

        row = col.row(align=True)
        col.prop(context.window_manager.smplx_tool, "smplx_version")
        col.prop(context.window_manager.smplx_tool, "smplx_gender")
        col.prop(context.window_manager.smplx_tool, "smplx_uv")
        col.operator("scene.smplx_add_gender", text="Add")

        col.separator()
        col.label(text="Texture:")
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.prop(context.window_manager.smplx_tool, "smplx_texture")
        split.operator("object.smplx_set_texture", text="Set")

class SMPLX_PT_Shape(bpy.types.Panel):
    bl_label = "Shape"
    bl_category = "SMPL-X"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.prop(context.window_manager.smplx_tool, "smplx_height")
        col.prop(context.window_manager.smplx_tool, "smplx_weight")
        col.operator("object.smplx_measurements_to_shape")
        col.separator()

        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.operator("object.smplx_random_shape")
        split.operator("object.smplx_reset_shape")
        col.separator()

        col.operator("object.smplx_snap_ground_plane")
        col.separator()

        col.operator("object.smplx_update_joint_locations")
        col.separator()
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.operator("object.smplx_random_expression_shape")
        split.operator("object.smplx_reset_expression_shape")

class SMPLX_PT_Pose(bpy.types.Panel):
    bl_label = "Pose"
    bl_category = "SMPL-X"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.prop(context.window_manager.smplx_tool, "smplx_corrective_poseshapes")
        col.separator()
        col.operator("object.smplx_set_poseshapes")

        col.separator()
        col.label(text="Hand Pose:")
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.prop(context.window_manager.smplx_tool, "smplx_handpose")
        split.operator("object.smplx_set_handpose", text="Set")

        col.separator()
        col.operator("object.smplx_write_pose")
        col.separator()
        col.operator("object.smplx_load_pose")

class SMPLX_PT_Animation(bpy.types.Panel):
    bl_label = "Animation"
    bl_category = "SMPL-X"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.smplx_add_animation")

class SMPLX_PT_Export(bpy.types.Panel):
    bl_label = "Export"
    bl_category = "SMPL-X"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("object.smplx_export_alembic")
        col.separator()

        col.operator("object.smplx_export_fbx")
        col.separator()

        col.operator("object.smplx_export_shape")
        col.separator()

#        export_button = col.operator("export_scene.obj", text="Export OBJ [m]", icon='EXPORT')
#        export_button.global_scale = 1.0
#        export_button.use_selection = True
#        col.separator()

        row = col.row(align=True)
        row.operator("ed.undo", icon='LOOP_BACK')
        row.operator("ed.redo", icon='LOOP_FORWARDS')
        col.separator()

        (year, month, day) = bl_info["version"]
        col.label(text="Version: %s-%s-%s" % (year, month, day))

classes = [
    SMPLX_PT_Model,
    SMPLX_PT_Shape,
    SMPLX_PT_Pose,
    SMPLX_PT_Animation,
    SMPLX_PT_Export
]

def register():
    properties.register()
    operators.register()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
