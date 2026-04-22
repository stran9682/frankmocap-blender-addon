import json

import bpy
import numpy as np
from mathutils import Vector

from ..utils.constants import (
    ADDON_ROOT,
    NUM_SMPLX_JOINTS,
    SMPLX_JOINT_NAMES,
)
from ..utils.shapekeys import smplx_ensure_valid_shapekey_slider_ranges


class SMPLXMeasurementsToShape(bpy.types.Operator):
    bl_idname = "object.smplx_measurements_to_shape"
    bl_label = "Measurements To Shape"
    bl_description = ("Calculate and set shape parameters for specified measurements")
    bl_options = {'REGISTER', 'UNDO'}

    betas_regressor = {}
    betas_regressor["female"] = None
    betas_regressor["male"] = None
    betas_regressor["neutral"] = None

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return ((context.object.type == 'MESH') and (context.object.parent.type == 'ARMATURE'))
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')

        for gender in ["female", "male", "neutral"]:
            if self.betas_regressor[gender] is None:
                regressor_path = ADDON_ROOT / "data" / f"smplx_measurements_to_betas_{gender}.json"
                with open(regressor_path) as f:
                    data = json.load(f)
                    self.betas_regressor[gender] = (np.asarray(data["A"]).reshape(-1, 2), np.asarray(data["B"]).reshape(-1, 1))

        gender = obj["smplx_gender"]
        (A, B) = self.betas_regressor[gender]

        # Calculate beta values from measurements
        height_m = context.window_manager.smplx_tool.smplx_height
        height_cm = height_m * 100.0
        weight_kg = context.window_manager.smplx_tool.smplx_weight

        v_root = pow(weight_kg, 1.0/3.0)
        measurements = np.asarray([[height_cm], [v_root]])
        betas = A @ measurements + B

        num_betas = betas.shape[0]
        for i in range(num_betas):
            name = f"Shape{i:03d}"
            key_block = obj.data.shape_keys.key_blocks[name]
            value = betas[i, 0]

            # Adjust key block min/max range to value
            if value < key_block.slider_min:
                key_block.slider_min = value
            elif value > key_block.slider_max:
                key_block.slider_max = value

            key_block.value = value

        bpy.ops.object.smplx_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}


class SMPLXRandomShape(bpy.types.Operator):
    bl_idname = "object.smplx_random_shape"
    bl_label = "Random"
    bl_description = ("Sets all shape blend shape keys to a random value")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        smplx_ensure_valid_shapekey_slider_ranges(obj)
        randomized_betas = 0
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Shape"):
                beta = np.random.normal(0.0, 1.0)
                beta = np.clip(beta, -1.0, 1.0)
                key_block.value = beta

                randomized_betas += 1
                if randomized_betas >= 16:
                    break

        bpy.ops.object.smplx_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}


class SMPLXResetShape(bpy.types.Operator):
    bl_idname = "object.smplx_reset_shape"
    bl_label = "Reset"
    bl_description = ("Resets all blend shape keys for shape")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Shape"):
                key_block.value = 0.0

        bpy.ops.object.smplx_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}


class SMPLXRandomExpressionShape(bpy.types.Operator):
    bl_idname = "object.smplx_random_expression_shape"
    bl_label = "Random Face Expression"
    bl_description = ("Sets all face expression blend shape keys to a random value")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        smplx_ensure_valid_shapekey_slider_ranges(obj)
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Exp"):
                key_block.value = np.random.uniform(-2, 2)

        return {'FINISHED'}


class SMPLXResetExpressionShape(bpy.types.Operator):
    bl_idname = "object.smplx_reset_expression_shape"
    bl_label = "Reset"
    bl_description = ("Resets all blend shape keys for face expression")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Exp"):
                key_block.value = 0.0

        return {'FINISHED'}


class SMPLXSnapGroundPlane(bpy.types.Operator):
    bl_idname = "object.smplx_snap_ground_plane"
    bl_label = "Snap To Ground Plane"
    bl_description = ("Snaps mesh to the XY ground plane")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh or armature is active object
            return ((context.object.type == 'MESH') or (context.object.type == 'ARMATURE'))
        except: return False

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        obj = bpy.context.object
        if obj.type == 'ARMATURE':
            armature = obj
            obj = bpy.context.object.children[0]
        else:
            armature = obj.parent

        # Get vertices with applied skin modifier in object coordinates
        depsgraph = context.evaluated_depsgraph_get()
        object_eval = obj.evaluated_get(depsgraph)
        mesh_from_eval = object_eval.to_mesh()

        # Get vertices in world coordinates
        matrix_world = obj.matrix_world
        vertices_world = [matrix_world @ vertex.co for vertex in mesh_from_eval.vertices]
        z_min = (min(vertices_world, key=lambda item: item.z)).z
        object_eval.to_mesh_clear() # Remove temporary mesh

        # Adjust height of armature so that lowest vertex is on ground plane.
        # Do not apply new armature location transform so that we are later able to show loaded poses at their desired height.
        armature.location.z = armature.location.z - z_min

        return {'FINISHED'}


class SMPLXUpdateJointLocations(bpy.types.Operator):
    bl_idname = "object.smplx_update_joint_locations"
    bl_label = "Update Joint Locations"
    bl_description = ("Update joint locations after shape changes")
    bl_options = {'REGISTER', 'UNDO'}

    j_regressor = {}
    j_regressor["female"] = { "10": None, "300": None, "300_lh": None }
    j_regressor["male"] = { "10": None, "300": None, "300_lh": None }
    j_regressor["neutral"] = { "10": None, "300": None, "300_lh": None }

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return ((context.object.type == 'MESH') and (context.object.parent.type == 'ARMATURE'))
        except: return False

    def load_regressor(self, gender, betas):
        prefix = ""
        if betas == "10":
            suffix = ""
        elif betas == "300":
            suffix = "_300"
        elif betas == "300_lh":
            suffix = "_300"
            prefix = "lh_"
        else:
            print(f"ERROR: No betas-to-joints regressor for desired beta shapes [{betas}]")
            return (None, None)

        regressor_path = ADDON_ROOT / "data" / f"smplx_betas_to_joints_{prefix}{gender}{suffix}.json"
        with open(regressor_path) as f:
            data = json.load(f)
            return (np.asarray(data["betasJ_regr"]), np.asarray(data["template_J"]))

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')

        # Get beta shapes
        betas = []
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Shape"):
                betas.append(key_block.value)
        num_betas = len(betas)
        betas = np.array(betas)

        # Cache regressor files on first call
        for target_betas in ["10", "300", "300_lh"]:
            for gender in ["female", "male", "neutral"]:
                if self.j_regressor[gender][target_betas] is None:
                    self.j_regressor[gender][target_betas] = self.load_regressor(gender, target_betas)

        key = f"{num_betas}"
        if obj["smplx_version"] == "locked_head":
            key += "_lh"
        gender = obj["smplx_gender"]
        (betas_to_joints, template_j) = self.j_regressor[gender][key]
        joint_locations = betas_to_joints @ betas + template_j

        # Set new bone joint locations
        armature = obj.parent
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        for index in range(NUM_SMPLX_JOINTS):
            bone = armature.data.edit_bones[SMPLX_JOINT_NAMES[index]]
            bone.head = (0.0, 0.0, 0.0)
            bone.tail = (0.0, 0.0, 0.1)

            # Convert SMPL-X joint locations to Blender joint locations
            joint_location_smplx = joint_locations[index]
            bone_start = Vector( (joint_location_smplx[0], -joint_location_smplx[2], joint_location_smplx[1]) )
            bone.translate(bone_start)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = obj

        return {'FINISHED'}


classes = (
    SMPLXMeasurementsToShape,
    SMPLXRandomShape,
    SMPLXResetShape,
    SMPLXRandomExpressionShape,
    SMPLXResetExpressionShape,
    SMPLXSnapGroundPlane,
    SMPLXUpdateJointLocations,
)
