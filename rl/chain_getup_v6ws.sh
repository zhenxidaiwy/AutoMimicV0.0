#!/usr/bin/env bash
# v6 reward, warm-started from the v5 policy that already stands up (from-scratch v6 got stuck sitting: smoothness
# penalties dominated exploration). 2500 iters fine-tuning -> eval -> 2x2 demo -> package.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v6
V5=2026-10-19_12-29-06_getup_n2048_resume   # v5 final (model_4998)
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
run=getup_v6ws_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v6ws] $(date) warm start from $V5" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $V5 >> $L 2>&1
echo "[v6ws] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v6ws] final checkpoint $CK"
CKPT=$CK bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/demo_getup.sh $CK getup_v6_final "G1 get-up v6 (slow & realistic, warm-started from v5)"
mkdir -p ~/dance_win/policies/getup_v6
cp $CK ~/dance_win/policies/getup_v6/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v6/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v6, warm start from $V5)" > ~/dance_win/policies/getup_v6/SOURCE.txt
echo "[v6ws] done $(date)"
