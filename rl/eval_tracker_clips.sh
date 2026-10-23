#!/usr/bin/env bash
# Oracle check of a (generalist) tracker on several clips: feed each clip's ground-truth reference, fall-only eval.
# Usage: bash eval_tracker_clips.sh <run-substring> [ckpt] -- prints one line per clip
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$1 | tail -1)
ck=${2:-$(ls $dir/model_*.pt | sort -V | tail -1)}; [[ "$ck" = /* ]] || ck=$dir/$ck
echo "tracker $ck"
for c in bda_zhao_sss tonyfu_sss_fast street_sss_b bda2_gxdsm_full gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b; do
  r=$(python ~/dance_win/rl/eval_ckpt.py --ckpt $ck --motion ~/projects/dance/dataset/$c/g1_lock_vlm_50fps.npz 2>&1 | grep -E '^\{')
  echo "$c $r" | python -c "
import sys, json
line = sys.stdin.read(); c, j = line.split(' ', 1); r = json.loads(j)
split = 'TRAIN' if c in ('bda_zhao_sss','tonyfu_sss_fast','street_sss_b','bda2_gxdsm_full') else 'HELD-OUT'
print(f\"{split:<9}{c:<18} {'completed' if r['completed_clip'] else 'fell at %.2fs' % r['fell_at_s']:<14} of {r['clip_steps']*0.02:.1f}s  body_err {r['body_pos_err_mean_m']:.3f}  ee_viol {r['ee_z_violation_frac']}\")"
  mv $dir/eval/$(basename ${ck%.pt}).mp4 $dir/eval/oracle_$c.mp4 2>/dev/null
done
