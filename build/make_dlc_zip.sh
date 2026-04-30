#!/bin/bash
# Build distributable DLC data zips for SMPL-X v1.1 and SMPL+H.
#
# These are pure data drop-ins (no manifest, no code) intended to be extracted
# into <extensions>/user_default/ on top of the main addon install.
#

set -e

pushd ../..

filedate=$(date '+%Y%m%d')
version=$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' smplx_blender_addon/blender_manifest.toml)

build_dlc_zip() {
  local model="$1"
  local license_src="$2"
  shift 2  # remaining args = data files to bundle (relative paths from cwd)

  # Verify every named file (license + data) exists; abort if any are missing.
  local missing=0
  for f in "$license_src" "$@"; do
    if ! compgen -G "$f" > /dev/null; then
      echo "ERROR: DLC source not found: $f" >&2
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "ERROR: Aborting build for DLC '${model}' due to missing files." >&2
    return 1
  fi

  # Stage the license inside data/ so it ships at smplx_blender_addon/data/<basename>
  # and lands next to the model files when the user extracts the zip.
  local license_dst="smplx_blender_addon/data/$(basename "$license_src")"
  cp "$license_src" "$license_dst"

  local archive="./smplx_blender_addon_dlc_${model}-${version}-${filedate}.zip"
  echo "Generating $archive"
  if [ -f "$archive" ]; then
    echo "Removing old DLC: $archive"
    rm "$archive"
  fi
  zip -r "$archive" "$license_dst" "$@"
  echo "  Removing: $license_dst"
  rm -f "$license_dst"
  echo "Generated: $archive"
}

# SMPL-X v1.1 DLC
build_dlc_zip "smplx1.1" \
  smplx_blender_addon/build/LICENSE-DLC-SMPLX.md \
  smplx_blender_addon/data/smplx_betas_to_joints_female_300.json \
  smplx_blender_addon/data/smplx_betas_to_joints_male_300.json \
  smplx_blender_addon/data/smplx_betas_to_joints_neutral_300.json \
  smplx_blender_addon/data/smplx_model_20230302.blend

# SMPL+H DLC
build_dlc_zip "smplh" \
  smplx_blender_addon/build/LICENSE-DLC-SMPLH.md \
  smplx_blender_addon/data/smplh*

popd
