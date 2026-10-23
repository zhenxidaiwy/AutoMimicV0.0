#!/usr/bin/env bash
# Re-run only ground_fix (vlm + heuristic) and their npz conversions. Usage: bash ground_only.sh <clip_id> [...]
P=~/miniforge3/envs/gmr/bin/python; S=~/dance_win/scripts/data
for id in "$@"; do
  for c in vlm heuristic; do
    $P $S/ground_fix.py $id --contacts $c | $P -c "
import json,sys; r=json.loads(sys.stdin.read())
print(r['clip'], r['contacts'], 'before', r['before'], '| after', r['after'], '| clamped', r['frames_clamped_by_no_penetration'], '| agree', r['heuristic_vs_vlm_contact_agreement'])"
    bash $S/to_npz.sh -v ground_$c $id
  done
done
