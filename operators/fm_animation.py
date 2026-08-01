import bpy
import numpy as np
from bpy_extras.io_utils import ImportHelper
from ..frankmocap.integration.copy_and_paste import integration_copy_paste
from ..frankmocap.demo.demo_frankmocap import __filter_bbox_list
from ..frankmocap.handmocap.hand_mocap_api import HandMocap
from ..frankmocap.bodymocap.body_mocap_api import BodyMocap
from ..frankmocap.handmocap.hand_bbox_detector import HandBboxDetector
from collections import OrderedDict

class FMAddAnination(bpy.types.Operator, ImportHelper):

    def execute(self, context): 
        import cv2
        import torch

        device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        assert torch.cuda.is_available(), "Current version only supports GPU"

        hand_bbox_detector =  HandBboxDetector('third_view', device) 

        default_checkpoint_body_smplx ='./extra_data/body_module/pretrained_weights/smplx-03-28-46060-w_spin_mlc3d_46582-2089_2020_03_28-21_56_16.pt'
        body_mocap = BodyMocap(default_checkpoint_body_smplx, './extra_data/smpl/', device = device, use_smplx= True)

        default_checkpoint_hand = "./extra_data/hand_module/pretrained_weights/pose_shape_best.pth"
        hand_mocap = HandMocap(default_checkpoint_hand, './extra_data/smpl/', device = device)

        input_data = cv2.VideoCapture(self.filepath)

        video_frame = 0
        while True:
            _, img_original_bgr = input_data.read()

            body_bbox_list, hand_bbox_list, pred_output_list = run_regress(
                img_original_bgr, 
                body_bbox_list, hand_bbox_list, hand_bbox_detector,
                body_mocap, hand_mocap)

            if len(body_bbox_list) < 1: 
                print(f"No body deteced, frame: {video_frame}")
                continue

            saved_data = output_to_pkl(len(hand_bbox_list), pred_output_list)

            # Append to np array

            
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