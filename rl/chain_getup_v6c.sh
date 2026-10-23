#!/usr/bin/env bash
# v6c reward, warm-started from v6b final. N iters -> eval -> stance check -> 2x2 demo -> package to policies/getup_v6c.
# Usage: bash chain_getup_v6c.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v6c
WARM=2026-10-19_17-15-09_getup_v6b_n2048; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
run=getup_v6c_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v6c] $(date) warm start from $WARM" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v6c] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v6c] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/demo_getup.sh $CK getup_v6c_final "G1 get-up v6c (upright torso, straight waist, normal stance)"
mkdir -p ~/dance_win/policies/getup_v6c
cp $CK ~/dance_win/policies/getup_v6c/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v6c/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v6c, warm start from $WARM)" > ~/dance_win/policies/getup_v6c/SOURCE.txt
echo "[v6c] done $(date)"
