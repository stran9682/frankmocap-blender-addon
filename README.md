# SMPL-X Blender Add-on

This add-on allows you to add [SMPL-X](https://smpl-x.is.tue.mpg.de) skinned meshes to your current Blender scene. Each imported SMPL-X mesh consists of a shape specific rig, as well as shape keys (blend shapes) for shape, expression and pose correctives.

+ Requirements: Blender 2.80+, tested with 3.1.0
+ Additional dependencies: None
+ Used SMPL-X model: SMPL-X v1.1 with 10 shape components, 10 expression components

# Features
+ Add female/male/neutral specific SMPL-X mesh to current scene
+ Set sample albedo texture
+ Set body shape from height and weight measurements
+ Randomize/reset shape
+ Update joint locations
+ Position feet on ground plane (z=0)
+ Randomize/reset face expression shape
+ Enable/disable corrective poseshapes
+ Change hand pose (flat, relaxed)
+ Write current pose in SMPL-X theta notation to console
+ Load pose from .pkl file
    + Format: Full body pose with 55 joints in Rodrigues notation
    + Over 3000 sample poses are available at https://agora.is.tuebingen.mpg.de/
        + Sign In > Download > Ground Truth Fittings > SMPL-X fits
+ Create animated body from animation .npz file (AMASS or SMPL-X)
+ Alembic (.abc) export of animated body as animated vertex geometry cache
    + Keyframed pose correctives are always baked into the vertices on export
    + Alembic animation can be imported into other third-party tools
        + Unreal Engine
            + Alembic Import settings: Geometry Cache, Scale (100, -100, 100), Rotation (90, 0, 0)
    + We recommend latest Blender 3 release for up-to-date Alembic format support
+ FBX export
    + Export to Unity or Unreal Engine
        + Imported FBX will import in Unity/Unreal without rotations and without scaling
    + Shape key export options: 
        + Body shape and posecorrectives
        + Body shape without posecorrectives
        + None (bakes current body shape into mesh)

## Installation
1. Register at https://smpl-x.is.tue.mpg.de and download the SMPL-X for Blender add-on. The ZIP release file will include the required SMPL-X model which is not included in the code repository.
2. Blender>Edit>Preferences>Add-ons>Install
3. Select downloaded SMPL-X for Blender add-on ZIP file (`smplx_blender_addon-YYYYMMDD.zip`) and install
4. Enable SMPL-X for Blender add-on
5. Enable sidebar in 3D Viewport>View>Sidebar
6. SMPL-X tool will show up in sidebar

## Usage
+ [Short overview video](https://www.youtube.com/watch?v=DY2k29Jef94)
+ [CVPR 2021 tutorial video](https://www.youtube.com/watch?v=m8i00zG6mZI&t=107s)

## Notes
+ The add-on GUI (gender, texture, hand pose) does not reflect the state of the currently selected SMPL-X model if you work with multiple models in one scene.
+ To maintain editor responsiveness the add-on does not automatically recalculate joint locations when you change the shape manually via Blender shape keys. Use the `Update Joint Locations` button to update the joint locations after manual shape key change.
+ To maintain editor responsiveness, the add-on does not automatically recalculate the corrective pose shape keys when you change the armature pose. Use the `Update Pose Shapes` button to update the joint locations after pose changes.

## License
+ Generated body mesh data using this add-on:
    + Licensed under SMPL-X Model License
        + https://smpl-x.is.tue.mpg.de/modellicense

+ See LICENSE.md for further license information including commercial licensing

+ Attribution for publications: 
    + You agree to cite the most recent paper describing the model as specified on the SMPL-X website: https://smpl-x.is.tue.mpg.de

## Acknowledgements
+ We thank [Meshcapade](https://meshcapade.com/) for providing the SMPL-X female/male sample textures (`smplx_texture_f_alb.png`, `smplx_texture_m_alb.png`) under [Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/) license.

+ Sergey Prokudin (rainbow texture data)

+ Vassilis Choutas (betas-to-joints regressor)

+ Lea Müller and Vassilis Choutas (measurements-to-betas regressor)

## Changelog
+ 20210505: Initial release
+ 20210525: Replaced vertices-to-joints regressor with beta-to-joints regressor. Added rainbow texture (CC BY-NC 4.0).
+ 20210611: Added option to set shape from height and weight values for female and male models
+ 20210629: Added option to create animated body from AMASS SMPL-X animation file
+ 20220117: Added option to set height+weight for neutral SMPL-X model
+ 20220218: Added option to set animation target framerate. Lower values will speed up import time.
+ 20220311:
  + Fix pelvis location offset when importing AMASS animations
  + Added option to set animation import format (AMASS, SMPL-X)
  + Adjust Blender Timeline end frame when adding first animation
  + Use 30fps as new default target framerate
  + Added Alembic export button
+ 20220315:
  + Speed up animation import time
+ 20220326:
  + Added Unreal FBX export. Shape keys bake options can now be found in export dialog settings.
  + Fix unwanted duplicated animation sequence in FBX export
+ 20220623:
  + Add option to import animation onto grounded rest pose armature
  + Disable animation keyframe simplification for FBX export so that FBX animations match Alembic animations
  + Add support for 300 beta shape model

## Contact
+ smplx-blender@tue.mpg.de
