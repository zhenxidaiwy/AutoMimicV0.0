#!/usr/bin/env bash
# Show cut positions for aborted clips and the tail of the failing npz / foot_lock logs.
for id in latin_sss bda2_gxdsm_wide bda2_gxdsm_full; do head -1 ~/projects/dance_logs/clip_$id.log; done
echo "--- npz log"; tail -4 ~/projects/dance_logs/npz_bda_ming_gxdsm_a__lock_heuristic.log
echo "--- lock_heuristic exists?"; ls -la ~/projects/dance/data/g1/bda_ming_gxdsm_a/ | grep -E "lock|ground"
