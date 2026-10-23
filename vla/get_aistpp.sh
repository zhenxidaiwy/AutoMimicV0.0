#!/usr/bin/env bash
# AIST++ 3D keypoints (COCO-17, 60 fps; annotations CC BY 4.0, Google LLC) as "other motion" negatives for the
# recogniser. -> ~/projects/dance/data/aistpp/keypoints3d/*.pkl (+ ignore_list.txt)
D=~/projects/dance/data/aistpp
mkdir -p $D && cd $D || exit 1
[ -f keypoints3d.zip ] || wget -q -O keypoints3d.zip https://github.com/google/aistplusplus_dataset/releases/download/v1.0/keypoints3d.zip || exit 1
[ -d keypoints3d ] || unzip -q keypoints3d.zip || exit 1
[ -f ignore_list.txt ] || wget -q -O ignore_list.txt https://raw.githubusercontent.com/google/aistplusplus_api/main/aist_plusplus/ignore_list.txt
ls keypoints3d | wc -l
du -sh keypoints3d.zip keypoints3d
