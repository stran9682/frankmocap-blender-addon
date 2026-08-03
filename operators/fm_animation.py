import os

import bpy
import numpy as np
from bpy_extras.io_utils import ImportHelper
from ..frankmocap.integration.copy_and_paste import integration_copy_paste
from ..frankmocap.demo.demo_frankmocap import __filter_bbox_list
from ..frankmocap.handmocap.hand_mocap_api import HandMocap
from ..frankmocap.bodymocap.body_mocap_api import BodyMocap
from ..frankmocap.handmocap.hand_bbox_detector import HandBboxDetector

class FMAddAnination(bpy.types.Operator, ImportHelper):
    bl_idname = "object.fm_add_animation"
    bl_label = "Add Frankmocap Animation"
    bl_description = ("Load video and produce SMPlX model")
    bl_options = {'REGISTER', 'UNDO'}

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

            body_bbox_list, hand_bbox_list, pred_output_list = run_regress(
                img_original_bgr, 
                hand_bbox_detector,
                body_mocap, 
                hand_mocap
            )

            if len(body_bbox_list) < 1: 
                continue

            pred_output = output_to_pkl(len(hand_bbox_list), pred_output_list)

            # Append to np array
            frame = {
                'betas': pred_output['pred_betas'][0],  # (10,)
                'global_orient': pred_output['pred_body_pose'][0][:3],  # (3,)
                'body_pose': pred_output['pred_body_pose'][0][3:66],  # (63,)
                'left_hand_pose': pred_output['pred_left_hand_pose'][0],  # (45,)
                'right_hand_pose': pred_output['pred_right_hand_pose'][0],  # (45,)
            }

            frames_data.append(frame)

        poses = np.array([
            np.concatenate([
                frame['global_orient'],
                frame['body_pose'],
                frame['left_hand_pose'],
                frame['right_hand_pose']
            ])
            for frame in frames_data
        ])

        betas = frames_data[0]['betas']

        # Pass to blender


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

def output_to_pkl(
    num_subject, 
    pred_output_list
):
    saved_data = list()
    
    for s_id in range(num_subject):
        # predict params
        pred_output = pred_output_list[s_id]
        if pred_output is None:
            saved_pred_output = None
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

        saved_data.append(saved_pred_output) 

    return saved_data 

classes = (
    FMAddAnination,
)