#!/bin/bash
pushd ../..

filedate=$(date '+%Y%m%d')

# Build 10 shape model add-on
echo "Generating $archivename"
archivename=./smplx_blender_addon_$filedate.zip
if [ -f $archivename ]; then
  echo "Removing old add-on: $archivename"
  rm $archivename
fi
zip $archivename smplx_blender_addon/*.py smplx_blender_addon/*.md smplx_blender_addon/data/*.npz smplx_blender_addon/data/*.json smplx_blender_addon/data/*.png smplx_blender_addon/data/smplx_model_20210421.blend

# Build 300 shape model add-on
echo "Generating $archivename"
archivename=./smplx_blender_addon_300_$filedate.zip
if [ -f $archivename ]; then
  echo "Removing old add-on: $archivename"
  rm $archivename
fi
zip $archivename smplx_blender_addon/*.py smplx_blender_addon/*.md smplx_blender_addon/data/*.npz smplx_blender_addon/data/*.json smplx_blender_addon/data/*.png smplx_blender_addon/data/smplx_model_300_20220615.blend

popd
