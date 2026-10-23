#!/usr/bin/env bash
# v7 (standing template + standing starts), warm-started from v6c (model_9850). N iters -> eval -> stance check
# -> 2x2 demo -> package to policies/getup_v7.  Usage: bash chain_getup_v7.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v7
WARM=2026-10-19_18-35-45_getup_v6c_n2048; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
run=getup_v7_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v7] $(date) warm start from $WARM" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v7] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v7] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7_final "G1 get-up v7 (canonical standing template)"
mkdir -p ~/dance_win/policies/getup_v7
cp $CK ~/dance_win/policies/getup_v7/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v7/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v7, warm start from $WARM)" > ~/dance_win/policies/getup_v7/SOURCE.txt
echo "[v7] done $(date)"
