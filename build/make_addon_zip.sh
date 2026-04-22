#!/bin/bash
# Build distributable Blender 4.5+ extension zips for SMPL-X.
#
# Each build target ships a different combination of .blend model files, so
# we keep the per-target zip approach. For a single-target build that just
# packages the current source tree, use Blender's official builder instead:
#   blender --command extension build --source-dir smplx_blender_addon
# which validates blender_manifest.toml and produces a one-shot zip.

#BUILD_SMPLX_10=1
BUILD_SMPLX_300=1
#BUILD_SMPLX_2020=1

pushd ../..

filedate=$(date '+%Y%m%d')

# Files common to every build target.
common_files=(
  smplx_blender_addon/blender_manifest.toml
  smplx_blender_addon/__init__.py
  smplx_blender_addon/properties
  smplx_blender_addon/operators
  smplx_blender_addon/panels
  smplx_blender_addon/utils
  smplx_blender_addon/LICENSE.md
  smplx_blender_addon/README.md
  smplx_blender_addon/data/*.npz
  smplx_blender_addon/data/*.json
  smplx_blender_addon/data/*.png
)

# Patterns to exclude from every zip (no editor/build cruft).
exclude_patterns=(
  "*/__pycache__/*"
  "*.pyc"
  "*.pyo"
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

if [ -n "$BUILD_SMPLX_10" ]; then
  # Build 10 shape model add-on
  build_zip "./smplx_blender_addon_${filedate}.zip" \
    smplx_blender_addon/data/smplx_model_20210421.blend
fi

if [ -n "$BUILD_SMPLX_300" ]; then
  # Build 300 shape model add-on
  build_zip "./smplx_blender_addon_lh_${filedate}.zip" \
    smplx_blender_addon/data/smplx_model_20230302.blend \
    smplx_blender_addon/data/smplx_model_lh_20230302.blend
fi

if [ -n "$BUILD_SMPLX_2020" ]; then
  # Build SMPL-X 2020 model add-on
  build_zip "./smplx_blender_addon_2020_300_100_${filedate}.zip" \
    smplx_blender_addon/data/smplx_model_2020_300_100_20230227.blend
fi

popd
