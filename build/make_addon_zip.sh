#!/bin/bash

#BUILD_SMPLX_10=1
BUILD_SMPLX_300=1
#BUILD_SMPLX_2020=1

pushd ../..

filedate=$(date '+%Y%m%d')

if [ -n "$BUILD_SMPLX_10" ]; then
  # Build 10 shape model add-on
  archivename=./smplx_blender_addon_$filedate.zip
  echo "Generating $archivename"
  if [ -f $archivename ]; then
    echo "Removing old add-on: $archivename"
    rm $archivename
  fi
  zip $archivename smplx_blender_addon/*.py smplx_blender_addon/*.md smplx_blender_addon/data/*.npz smplx_blender_addon/data/*.json smplx_blender_addon/data/*.png smplx_blender_addon/data/smplx_model_20210421.blend
fi

if [ -n "$BUILD_SMPLX_300" ]; then
  # Build 300 shape model add-on
  archivename=./smplx_blender_addon_lh_$filedate.zip
  echo "Generating $archivename"
  if [ -f $archivename ]; then
    echo "Removing old add-on: $archivename"
    rm $archivename
  fi
  # --compression-method store
  zip $archivename smplx_blender_addon/*.py smplx_blender_addon/*.md smplx_blender_addon/data/*.npz smplx_blender_addon/data/*.json smplx_blender_addon/data/*.png smplx_blender_addon/data/smplx_model_20230302.blend smplx_blender_addon/data/smplx_model_lh_20230302.blend
fi

if [ -n "$BUILD_SMPLX_2020" ]; then
  # Build SMPL-X 2020 model add-on
  archivename=./smplx_blender_addon_2020_300_100_$filedate.zip
  echo "Generating $archivename"
  if [ -f $archivename ]; then
    echo "Removing old add-on: $archivename"
    rm $archivename
  fi
  zip $archivename smplx_blender_addon/*.py smplx_blender_addon/*.md smplx_blender_addon/data/*.npz smplx_blender_addon/data/*.json smplx_blender_addon/data/*.png smplx_blender_addon/data/smplx_model_2020_300_100_20230227.blend
fi

popd
