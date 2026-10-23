#!/usr/bin/env bash
# v6b reward, warm-started from the v6 fine-tune (which already stands with both feet planted). N iters -> eval ->
# 2x2 demo -> package to policies/getup_v6. Usage: bash chain_getup_v6b.sh <warm_run_dir> [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v6b
WARM=$1; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
run=getup_v6b_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v6b] $(date) warm start from $WARM" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${2:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v6b] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v6b] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/demo_getup.sh $CK getup_v6_final "G1 get-up v6b (slow & realistic reward)"
mkdir -p ~/dance_win/policies/getup_v6
cp $CK ~/dance_win/policies/getup_v6/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v6/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v6b, warm start from $WARM)" > ~/dance_win/policies/getup_v6/SOURCE.txt
echo "[v6b] done $(date)"
