#!/usr/bin/env bash
# Check the one-brain tracker on both canonical clips (fall-only eval), latest or given checkpoint.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*multi_canon_v1* | tail -1)
ck=${1:-$(ls $dir/model_*.pt | sort -V | tail -1)}; [[ "$ck" = /* ]] || ck=$dir/$ck
echo "tracker $ck"
for c in bda_zhao_sss bda2_gxdsm_full; do
  python ~/dance_win/rl/eval_ckpt.py --ckpt $ck --motion ~/projects/dance/dataset/$c/g1_lock_vlm_50fps.npz 2>&1 | grep -E '^\{' | \
    python -c "import sys,json; r=json.loads(sys.stdin.read()); print('$c', 'completed' if r['completed_clip'] else f\"fell at {r['fell_at_s']}s\", 'of', round(r['clip_steps']*0.02,1), 's  body_err', r['body_pos_err_mean_m'])"
done
