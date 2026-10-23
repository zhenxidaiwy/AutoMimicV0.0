#!/usr/bin/env bash
# Delete all derived outputs of a clip so process_clips.sh redoes it (raw video untouched).
# Usage: bash reset_clip.sh <clip_id> [...]
for id in "$@"; do
  rm -rf ~/projects/dance/data/g1/$id ~/projects/dance/data/gvhmr/$id ~/projects/dance/data/clips/$id.mp4 \
         ~/projects/dance/dataset/$id ~/projects/unitree_rl_mjlab/src/assets/motions/g1/${id}.npz \
         ~/projects/unitree_rl_mjlab/src/assets/motions/g1/${id}__*.npz
  echo "reset $id"
done
