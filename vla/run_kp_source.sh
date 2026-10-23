#!/usr/bin/env bash
# Offline closed loop with the one-brain tracker: ViTPose vs YOLO keypoints on held-out clips (isolates the keypoint
# source from the live-pipeline plumbing). Usage: bash run_kp_source.sh <watch_run> [tag]
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*multi_canon_v1* | tail -1)
ck=$(ls $dir/model_*.pt | sort -V | tail -1)
w=${1:-ret_lead0_s0}; tag=${2:-_canon}
for clip in gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b; do
  for kp in vit yolo; do
    bash ~/dance_win/vla/retrieve_loop.sh $clip $w $ck --kp $kp --tag $tag | python -c "
import sys, json
r = json.loads(sys.stdin.read())
print(f\"{r['clip']:<18} kp={r['kp']:<4} {'done' if r['completed'] else 'fell %.2fs' % r['fell_at_s']:<10} sss_frac={r['dance_pred_frac_sss']:.2f} sync={r['phase_sync']:.2f} flashes {r['flash_onsets_matched']}/{r['flash_onsets_human']} track_err={r['track_err_mean']:.3f}\")"
  done
done
