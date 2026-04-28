"""Per-model metadata registry for SMPL-X and SMPL+H.

A ModelSpec describes one body model's feature set, file paths, and joint
topology. Operators and panels read MODELS or call get_active_model_spec()
instead of bare constants so that adding another model is a registry change
rather than a code change.
"""

from dataclasses import dataclass

_SMPLX_JOINT_NAMES: tuple[str, ...] = (
    "pelvis", "left_hip", "right_hip", "spine1", "left_knee", "right_knee",
    "spine2", "left_ankle", "right_ankle", "spine3", "left_foot", "right_foot",
    "neck", "left_collar", "right_collar", "head", "left_shoulder",
    "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "jaw", "left_eye_smplhf", "right_eye_smplhf",
    "left_index1", "left_index2", "left_index3",
    "left_middle1", "left_middle2", "left_middle3",
    "left_pinky1", "left_pinky2", "left_pinky3",
    "left_ring1", "left_ring2", "left_ring3",
    "left_thumb1", "left_thumb2", "left_thumb3",
    "right_index1", "right_index2", "right_index3",
    "right_middle1", "right_middle2", "right_middle3",
    "right_pinky1", "right_pinky2", "right_pinky3",
    "right_ring1", "right_ring2", "right_ring3",
    "right_thumb1", "right_thumb2", "right_thumb3",
)

# SMPL+H armature: 22 body joints (incl. pelvis) + 30 hand joints. No jaw or eye joints.
_SMPLH_JOINT_NAMES: tuple[str, ...] = (
    "pelvis", "left_hip", "right_hip", "spine1", "left_knee", "right_knee",
    "spine2", "left_ankle", "right_ankle", "spine3", "left_foot", "right_foot",
    "neck", "left_collar", "right_collar", "head", "left_shoulder",
    "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_index1", "left_index2", "left_index3",
    "left_middle1", "left_middle2", "left_middle3",
    "left_pinky1", "left_pinky2", "left_pinky3",
    "left_ring1", "left_ring2", "left_ring3",
    "left_thumb1", "left_thumb2", "left_thumb3",
    "right_index1", "right_index2", "right_index3",
    "right_middle1", "right_middle2", "right_middle3",
    "right_pinky1", "right_pinky2", "right_pinky3",
    "right_ring1", "right_ring2", "right_ring3",
    "right_thumb1", "right_thumb2", "right_thumb3",
)

SMPLX_TEXTURE_ITEMS = (
    ("NONE", "None", ""),
    ("smplx_texture_f_2023.png", "Female (UV 2023)", ""),
    ("smplx_texture_m_2023.png", "Male (UV 2023)", ""),
    ("smplx_texture_f_alb.png", "Female (UV 2021)", ""),
    ("smplx_texture_m_alb.png", "Male (UV 2021)", ""),
    ("smplx_texture_rainbow.png", "Rainbow (UV 2021)", ""),
    ("UV_GRID", "UV Grid", ""),
    ("COLOR_GRID", "Color Grid", ""),
)

SMPLH_TEXTURE_ITEMS = (
    ("NONE", "None", ""),
    ("UV_GRID", "Grid", ""),
    ("COLOR_GRID", "Checker", ""),
)


SMPLX_GENDER_ITEMS = (
    ("female", "Female", ""),
    ("male", "Male", ""),
    ("neutral", "Neutral", ""),
)

SMPLH_GENDER_ITEMS = (
    ("female", "Female", ""),
    ("male", "Male", ""),
)


@dataclass(frozen=True)
class ModelSpec:
    id: str
    display_name: str
    mesh_name_template: str
    joint_names: tuple[str, ...]
    num_body_joints: int
    num_hand_joints: int
    handposes_file: str
    regressor_template: str | None

    has_expressions: bool
    has_measurements_to_betas: bool
    has_uv_variants: bool
    has_textures: bool
    texture_items: tuple[tuple[str, str, str], ...]
    gender_items: tuple[tuple[str, str, str], ...]
    has_corrective_poseshapes: bool

    blend_files: dict[str, str]


MODELS: dict[str, ModelSpec] = {
    "smplx": ModelSpec(
        id="smplx",
        display_name="SMPL-X",
        mesh_name_template="SMPLX-mesh-{gender}",
        joint_names=_SMPLX_JOINT_NAMES,
        num_body_joints=21,
        num_hand_joints=15,
        handposes_file="smplx_handposes.npz",
        regressor_template="smplx_betas_to_joints_{gender}{suffix}.json",
        has_expressions=True,
        has_measurements_to_betas=True,
        has_uv_variants=True,
        has_textures=True,
        texture_items=SMPLX_TEXTURE_ITEMS,
        gender_items=SMPLX_GENDER_ITEMS,
        has_corrective_poseshapes=True,
        blend_files={
            "locked_head": "smplx_model_lh_20230302.blend",
            "v1_1": "smplx_model_20230302.blend",
        },
    ),
    "smplh": ModelSpec(
        id="smplh",
        display_name="SMPL+H",
        mesh_name_template="SMPLH-mesh-{gender}",
        joint_names=_SMPLH_JOINT_NAMES,
        num_body_joints=21,
        num_hand_joints=15,
        handposes_file="smplx_handposes.npz",
        regressor_template=None,
        has_expressions=False,
        has_measurements_to_betas=False,
        has_uv_variants=False,
        has_textures=True,
        texture_items=SMPLH_TEXTURE_ITEMS,
        gender_items=SMPLH_GENDER_ITEMS,
        has_corrective_poseshapes=True,
        blend_files={"default": "smplh_model_20260428.blend"},
    ),
}


def get_active_model_spec(context) -> ModelSpec | None:
    """Resolve the active mesh/armature to its ModelSpec.

    Walks an armature to its child mesh; reads ``obj["model_type"]``;
    falls back to ``"smplx"`` when only the legacy ``smplx_gender`` custom
    property is present. Returns None if no addon mesh can be identified.
    """
    obj = getattr(context, "object", None) or getattr(context, "active_object", None)
    if obj is None:
        return None

    if obj.type == "ARMATURE":
        mesh = next((c for c in obj.children if c.type == "MESH"), None)
        if mesh is None:
            return None
    elif obj.type == "MESH":
        mesh = obj
    else:
        return None

    model_type = mesh.get("model_type")
    if model_type is not None:
        return MODELS.get(model_type)

    if "smplx_gender" in mesh:
        return MODELS.get("smplx")

    return None
