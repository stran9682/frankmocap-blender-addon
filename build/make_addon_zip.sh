#!/bin/bash
# Build distributable Blender 4.5+ extension zips for SMPL-X.
#

BUILD_SMPLX_300=1

pushd ../..

filedate=$(date '+%Y%m%d')
version=$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' smplx_blender_addon/blender_manifest.toml)

# Files common to every build target.
common_files=(
  smplx_blender_addon/blender_manifest.toml
  smplx_blender_addon/__init__.py
  smplx_blender_addon/handlers
  smplx_blender_addon/operators
  smplx_blender_addon/panels
  smplx_blender_addon/preferences
  smplx_blender_addon/properties
  smplx_blender_addon/utils
  smplx_blender_addon/LICENSE.md
  smplx_blender_addon/README.md
  smplx_blender_addon/data/*.npz
  smplx_blender_addon/data/*.json
  smplx_blender_addon/data/*.png
)

# Patterns to exclude from every zip (no editor/build cruft, no DLC data files).
exclude_patterns=(
  "*/__pycache__/*"
  "*.pyc"
  "*.pyo"
  "smplx_blender_addon/data/smplh*"
  "smplx_blender_addon/data/smplx_betas_to_joints_female_300.json"
  "smplx_blender_addon/data/smplx_betas_to_joints_male_300.json"
  "smplx_blender_addon/data/smplx_betas_to_joints_neutral_300.json"
)

build_zip() {
  local archive="$1"
  shift  # remaining args = extra (per-target) files
  echo "Generating $archive"
  if [ -f "$archive" ]; then
    echo "Removing old add-on: $archive"
    rm "$archive"
  fi
  zip -r "$archive" "${common_files[@]}" "$@" -x "${exclude_patterns[@]}"
}

if [ -n "$BUILD_SMPLX_300" ]; then
  # Build 300 shape model add-on
  output_filepath="./smplx_blender_addon-${version}-${filedate}.zip"
  build_zip "${output_filepath}" \
    smplx_blender_addon/data/smplx_model_lh_20230302.blend

  echo "Generated: ${output_filepath}"
fi

popd
