#!/usr/bin/env bash
# After GVHMR+retarget and a VLM events.json exist:
#   expand labels -> ground fix (vlm, heuristic) -> foot lock (vlm, heuristic) -> 50 fps npz for every variant.
# Recommended training reference: g1_lock_vlm_50fps.npz
# Usage: bash postprocess.sh <clip_id> [...]
P=~/miniforge3/envs/gmr/bin/python; S=~/dance_win/scripts/data
for id in "$@"; do
  [ -f ~/dance_win/data/annotations/$id.events.json ] || { echo "no events.json for $id"; continue; }
  $P $S/write_annotation.py $id
  for c in vlm heuristic; do
    $P $S/ground_fix.py $id --contacts $c > /dev/null
    $P $S/foot_lock.py $id --contacts $c
  done
  bash $S/to_npz.sh $id
  for v in ground_vlm ground_heuristic lock_vlm lock_heuristic; do bash $S/to_npz.sh -v $v $id; done
done
