import os
from math import radians
from pathlib import Path

import bpy
import numpy as np
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Quaternion, Vector

from ..frankmocap.integration.copy_and_paste import integration_copy_paste
from ..frankmocap.demo.demo_frankmocap import __filter_bbox_list
from ..frankmocap.handmocap.hand_mocap_api import HandMocap
from ..frankmocap.bodymocap.body_mocap_api import BodyMocap
from ..frankmocap.handmocap.hand_bbox_detector import HandBboxDetector
from ..utils.constants import ADDON_ROOT
from ..utils.model_spec import MODELS
from ..utils.pose import set_pose_from_rodrigues


class FMAddAnination(bpy.types.Operator, ImportHelper):
    bl_idname = "object.fm_add_animation"
    bl_label = "Add Frankmocap Animation"
    bl_description = ("Load video and produce SMPlX model")
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
            default="*.mp4",
            options={'HIDDEN'}
        )
    
    anim_format: EnumProperty(
        name="Format",
        items=(
            ("AMASS", "AMASS", ""),
            ("SMPL-X", "SMPL-X", ""),
        ),
    )

    rest_position: EnumProperty(
        name="Body rest position",
        items=(
            ("SMPL-X", "SMPL-X", "Use default SMPL-X rest position (feet below the floor)"),
            ("GROUNDED", "Grounded", "Use feet-on-floor rest position"),
        ),
    )

    hand_reference: EnumProperty(
        name="Hand pose reference",
        items=(
            ("FLAT", "Flat", "Use flat hand as hand pose reference"),
            ("RELAXED", "Relaxed", "Use relaxed hand as hand pose reference"),
        ),
    )

    keyframe_corrective_pose_weights: BoolProperty(
        name="Use keyframed corrective pose weights",
        description="Keyframe the weights of the corrective pose shapes for each frame. This increases animation load time and slows down editor real-time playback.",
        default=False
    )

    target_framerate: IntProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default=30,
        min = 1,
        max = 120
    )

    def execute(self, context): 
        import cv2
        import torch

        device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        assert torch.cuda.is_available(), "Current version only supports GPU"

        hand_bbox_detector =  HandBboxDetector('third_view', device) 

        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        extra_data_dir = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frankmocap", "extra_data"))
        smpl_dir = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frankmocap", "extra_data", "smpl"))

        default_checkpoint_body_smplx = os.path.join(
            os.path.join(extra_data_dir, "body_module", "pretrained_weights"), 
            "smplx-03-28-46060-w_spin_mlc3d_46582-2089_2020_03_28-21_56_16.pt"
        )
        body_mocap = BodyMocap(default_checkpoint_body_smplx, smpl_dir, device = device, use_smplx= True)

        default_checkpoint_hand = os.path.join(
            os.path.join(extra_data_dir, "hand_module", "pretrained_weights"), 
            "pose_shape_best.pth"
        )
        hand_mocap = HandMocap(default_checkpoint_hand, smpl_dir, device = device)

        input_data = cv2.VideoCapture(self.filepath)

        frames_data = []
        while True:
            _, img_original_bgr = input_data.read()
            if img_original_bgr is None:
                break

            body_bbox_list, _, pred_output_list = run_regress(
                img_original_bgr, 
                hand_bbox_detector,
                body_mocap, 
                hand_mocap
            )

            if len(body_bbox_list) < 1: 
                continue

            pred_output = extract_output(pred_output_list)

            frame_data =  {
                'betas': pred_output['pred_betas'][0],  # (10,)
                'global_orient': pred_output['pred_body_pose'][0][:3],  # (3,)
                'body_pose': pred_output['pred_body_pose'][0][3:66],  # (63,)
                'left_hand_pose': pred_output['pred_left_hand_pose'][0],  # (45,)
                'right_hand_pose': pred_output['pred_right_hand_pose'][0],  # (45,)
            }

            frames_data.append(frame_data)

        target_framerate = 12

        trans = np.zeros((len(frames_data), 3))

        gender = "neutral"

        mocap_framerate = 12
        
        betas = frames_data[0]['betas']

        poses = np.array([
            np.concatenate([
                frame['global_orient'],
                frame['body_pose'],
                frame['left_hand_pose'],
                frame['right_hand_pose']
            ])
            for frame in frames_data
        ]) 

        if self.hand_reference == "RELAXED":
            if self.hand_pose_relaxed is None:
                data_path = ADDON_ROOT / "data" / "smplx_handposes.npz"
                with np.load(data_path, allow_pickle=True) as data:
                    hand_poses = data["hand_poses"].item()
                    (left_hand_pose, right_hand_pose) = hand_poses["relaxed"]
                    self.hand_pose_relaxed = np.concatenate( (left_hand_pose, right_hand_pose) ).reshape(-1, 3)

        num_pose_joints = poses.shape[1] // 3
        spec = next((m for m in MODELS.values() if len(m.joint_names) == num_pose_joints), None)
        if spec is None:
            self.report({"ERROR"}, f"Unsupported joint count {num_pose_joints} in animation file")
            return {"CANCELLED"}

        if (context.active_object is not None):
            bpy.ops.object.mode_set(mode='OBJECT')

        # Add gender specific model
        context.window_manager.smplx_tool.body_model = spec.id
        context.window_manager.smplx_tool.smplx_gender = gender
        context.window_manager.smplx_tool.smplx_handpose = "flat"
        bpy.ops.scene.smplx_add_gender()

        obj = context.view_layer.objects.active
        armature = obj.parent

        # Append animation name to armature name
        armature.name = armature.name + "_" + Path(self.filepath).stem

        context.scene.render.fps = target_framerate
        context.scene.frame_start = 1

        # Set shape and update joint locations
        bpy.ops.object.mode_set(mode='OBJECT')
        for index, beta in enumerate(betas):
            key_block_name = f"Shape{index:03}"

            if key_block_name in obj.data.shape_keys.key_blocks:
                obj.data.shape_keys.key_blocks[key_block_name].value = beta
            else:
                print(f"ERROR: No key block for: {key_block_name}")

        bpy.ops.object.smplx_update_joint_locations('EXEC_DEFAULT')

        height_offset = 0
        if self.rest_position == "GROUNDED":
            bpy.ops.object.smplx_snap_ground_plane('EXEC_DEFAULT')
            height_offset = armature.location[2]

            obj["smplx_bind_pose_height_offset"] = height_offset

            # Apply location offsets to armature and skinned mesh
            bpy.context.view_layer.objects.active = armature
            armature.select_set(True)
            obj.select_set(True)
            bpy.ops.object.transform_apply(location = True, rotation=False, scale=False) # apply to selected objects
            armature.select_set(False)

            # Fix root bone location
            bpy.ops.object.mode_set(mode='EDIT')
            bone = armature.data.edit_bones["root"]
            bone.head = (0.0, 0.0, 0.0)
            bone.tail = (0.0, 0.0, 0.1)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.objects.active = obj

        # Keyframe poses
        step_size = int(mocap_framerate / target_framerate)

        num_frames = trans.shape[0]
        num_keyframes = int(num_frames / step_size)

        if self.keyframe_corrective_pose_weights:
            print(f"Adding pose keyframes with keyframed corrective pose weights: {num_keyframes}")
        else:
            print(f"Adding pose keyframes: {num_keyframes}")

        if len(bpy.data.actions) == 0:
            # Set end frame if we don't have any previous animations in the scene
            context.scene.frame_end = num_keyframes
        elif num_keyframes > context.scene.frame_end:
            context.scene.frame_end = num_keyframes

        wm = context.window_manager
        show_progress = not bpy.app.background and num_keyframes > 0
        if show_progress:
            # Percentage-based scale so the cursor's fractional-percent row
            # (2 decimal digits on Windows) always reads "00".
            wm.progress_begin(0, 100)
        try:
            for index, frame in enumerate(range(0, num_frames, step_size)):
                if (index % 100) == 0:
                    print(f"  {index}/{num_keyframes}")
                if show_progress and (index % 10) == 0:
                    wm.progress_update(index * 100 // num_keyframes)
                current_frame = index + 1
                current_pose = poses[frame].reshape(-1, 3)
                current_trans = trans[frame]
                for bone_index, bone_name in enumerate(spec.joint_names):
                    if bone_name == "pelvis":
                        # Keyframe pelvis location
                        if self.rest_position == "GROUNDED":
                            current_trans[1] = current_trans[1] - height_offset # SMPL-X local joint coordinates are Y-Up

                        armature.pose.bones[bone_name].location = Vector((current_trans[0], current_trans[1], current_trans[2]))
                        armature.pose.bones[bone_name].keyframe_insert('location', frame=current_frame)

                    # Keyframe bone rotation
                    pose_rodrigues = current_pose[bone_index]

                    if self.hand_reference == "FLAT":
                        set_pose_from_rodrigues(armature, bone_name, pose_rodrigues)
                    else:
                        # Relaxed hand pose uses different coordinate system for fingers
                        finger_names = ["index", "middle", "pinky", "ring", "thumb"]
                        if not any([x in bone_name for x in finger_names]):
                            set_pose_from_rodrigues(armature, bone_name, pose_rodrigues)
                        else:
                            # Finger rotations are relative to relaxed hand pose
                            hand_start_index = len(spec.joint_names) - 2 * spec.num_hand_joints
                            relaxed_hand_joint_index = bone_index - hand_start_index
                            pose_relaxed_rodrigues = self.hand_pose_relaxed[relaxed_hand_joint_index]
                            set_pose_from_rodrigues(armature, bone_name, pose_rodrigues, pose_relaxed_rodrigues)

                    armature.pose.bones[bone_name].keyframe_insert('rotation_quaternion', frame=current_frame)

                if self.keyframe_corrective_pose_weights:
                    # Calculate corrective poseshape weights for current pose and keyframe them.
                    # Note: This significantly increases animation load time and also reduces real-time playback speed in Blender viewport.
                    bpy.ops.object.smplx_set_poseshapes('EXEC_DEFAULT')
                    for key_block in obj.data.shape_keys.key_blocks:
                        if key_block.name.startswith("Pose"):
                            key_block.keyframe_insert("value", frame=current_frame)
        finally:
            if show_progress:
                wm.progress_end()

        if self.anim_format == "AMASS":
            # AMASS target floor is XY ground plane for SMPL-X template in OpenGL Y-up space (XZ ground plane).
            # Since SMPL-X Blender model is Z-up (and not Y-up) for rest/template pose, we need to adjust root node rotation to ensure that the resulting animated body is on Blender XY ground plane.
            bone_name = "root"
            if armature.pose.bones[bone_name].rotation_mode != 'QUATERNION':
                armature.pose.bones[bone_name].rotation_mode = 'QUATERNION'
            armature.pose.bones[bone_name].rotation_quaternion = Quaternion((1.0, 0.0, 0.0), radians(-90))
            armature.pose.bones[bone_name].keyframe_insert('rotation_quaternion', frame=1)

        print(f"  {num_keyframes}/{num_keyframes}")
        context.scene.frame_set(1)


        return {'FINISHED'}

def run_regress(
    img_original_bgr, 
    hand_bbox_detector,
    body_mocap, 
    hand_mocap
):
    _, body_bbox_list = hand_bbox_detector.detect_body_bbox(img_original_bgr.copy())

    if len(body_bbox_list) < 1: 
        return list(), list(), list()
    
    # sort the bbox using bbox size 
    # only keep on bbox if args.single_person is set
    hand_bbox_list = [None, ] * len(body_bbox_list)
    body_bbox_list, _ = __filter_bbox_list(
        body_bbox_list, hand_bbox_list, True)

    # body regression first 
    pred_body_list = body_mocap.regress(img_original_bgr, body_bbox_list)
    assert len(body_bbox_list) == len(pred_body_list)

    # get hand bbox from body
    hand_bbox_list = body_mocap.get_hand_bboxes(pred_body_list, img_original_bgr.shape[:2])
    assert len(pred_body_list) == len(hand_bbox_list)

    # hand regression
    pred_hand_list = hand_mocap.regress(
        img_original_bgr, hand_bbox_list, add_margin=True)
    assert len(hand_bbox_list) == len(pred_hand_list) 

    # integration by copy-and-paste
    integral_output_list = integration_copy_paste(
        pred_body_list, pred_hand_list, body_mocap.smpl, img_original_bgr.shape)
    
    return body_bbox_list, hand_bbox_list, integral_output_list

def extract_output(pred_output_list):

    pred_output = pred_output_list[0]
    if pred_output is None:
        return None
    else: 
        saved_pred_output = dict()
        for pred_key in pred_output:
            if pred_key.find("vertices")<0 or pred_key == 'faces' :
                saved_pred_output[pred_key] = pred_output[pred_key]
            else:
                if pred_key != 'faces':
                    saved_pred_output[pred_key] = \
                        pred_output[pred_key].astype(np.float16)
                else:
                    saved_pred_output[pred_key] = pred_output[pred_key]

        return saved_pred_output

classes = (
    FMAddAnination,
)