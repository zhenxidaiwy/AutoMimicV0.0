#!/usr/bin/env bash
# E1: from cartwheel_2 r04 model_4497, BPTT in the world model vs PPO in mjlab, same plain tracking objective,
# GPU used by one arm at a time. bash e1.sh bptt|ppo|eval <dir or run>
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
cd ~/dance_win/rl/wm/speedup || exit 1
S=~/projects/dance/wm_speedup
LOGS=~/projects/dance/runs/logs/rsl_rl/g1_tracking
INIT_RUN=2026-10-26_02-43-10_cw2auto_r04; INIT_CK=model_4497.pt
MO=~/projects/dance/dataset/cartwheel_2/g1_reachqp_vlm_hold_50fps.npz
case $1 in
bptt)
  python shac.py --spec $S/s2_r04 --wm ~/projects/dance/wm_runs/v1b_h1024/wm.pt --init $LOGS/$INIT_RUN/$INIT_CK \
    --motion $MO --out $S/e1_bptt --envs 4096 --H 32 --minutes ${2:-35} --export-min 5 --warmup 50 2>&1 | grep -v -i warn ;;
ppo)
  # plain mjlab tracking (no flip / library terms), same terminations / hand friction / knee limit as the harness
  python ~/dance_win/rl/train_dance.py --rsi uniform --knee-limit 120 --ee-threshold 0.6 --anchor-pos-threshold 0.6 \
    --hand-friction 0.6 -- --motion-file $MO --env.scene.num-envs 4096 --agent.max-iterations ${2:-1500} \
    --agent.algorithm.learning-rate 0.0003 --agent.run-name wmcmp_ppo --agent.logger tensorboard --agent.save-interval 100 \
    --agent.resume True --agent.load-run $INIT_RUN --agent.load-checkpoint $INIT_CK > $S/e1_ppo_train.log 2>&1 ;;
online)
  # Plan B: SuperMimic online loop from scratch (online.py), $2 = minutes, $3 = output name
  python online.py --spec $S/s2_r04 --template $LOGS/$INIT_RUN/$INIT_CK --motion $MO --out $S/${3:-b_online} \
    --minutes ${2:-60} --export-min 5 --log-every 20 ${4:+--wm-init $4} "${@:5}" 2>&1 | grep --line-buffered -E '^\{|Error|Traceback' ;;
eval)
  # every checkpoint in $2: eval_flip (harness metric, start-to-end episode) + 256-env uniform-start rollout
  for ck in $(ls $2/model_*.pt | sort -V); do
    n=$(basename $ck .pt)
    [ -f $2/eval_$n.json ] && continue
    ef=$(python ~/dance_win/rl/eval_flip.py --ckpt $ck --motion $MO --tag e1_$n --knee-limit 120 --hand-friction 0.6 \
         --size 320 240 2>&1 | grep -E '^\{' | tail -n 1)
    python record.py --ckpt $ck --motion $MO --out $2/rec_$n --envs 256 --steps 240 > /dev/null 2>&1
    python - "$2/rec_$n/real.npz" "$ef" "$2/eval_$n.json" <<'EOF'
import json, sys
import numpy as np
z = np.load(sys.argv[1]); terms = [str(t) for t in z["terms"]]
fr, done = z["frame"].astype(int), z["done"]
tele = np.zeros_like(done); tele[:-1] = fr[1:] != fr[:-1] + 1
track = z["reward"][..., :6].sum(-1)
ef = json.loads(sys.argv[2]) if sys.argv[2] else {}
out = {"track_rew_step": round(float(track.mean()), 4), "falls_per_1000": round(1000 * float((done & ~tele).mean()), 3),
       **{k: ef.get(k) for k in ("track_body_err_m", "track_joint_err", "landed_upright", "robot_rotation_deg", "hold_tilt_err_max_deg")}}
open(sys.argv[3], "w").write(json.dumps(out)); print(sys.argv[3], json.dumps(out))
EOF
  done ;;
esac
