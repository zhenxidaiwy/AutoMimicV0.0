#!/usr/bin/env bash
# v7b (v7 + waist limit barrier + 50% standing starts), warm-started from the latest v7 run. N iters -> eval ->
# stance check (from falls and from a standing start) -> 2x2 demo -> package to policies/getup_v7b.
# Usage: bash chain_getup_v7b.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v7b
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_getup_v7_n2048 | tail -1))
run=getup_v7b_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v7b] $(date) warm start from $WARM" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v7b] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v7b] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7b_final "G1 get-up v7b (standing template + straight waist)"
mkdir -p ~/dance_win/policies/getup_v7b
cp $CK ~/dance_win/policies/getup_v7b/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v7b/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v7b, warm start from $WARM)" > ~/dance_win/policies/getup_v7b/SOURCE.txt
echo "[v7b] done $(date)"
