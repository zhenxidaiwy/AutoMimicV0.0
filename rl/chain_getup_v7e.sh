#!/usr/bin/env bash
# v7e (v7d + true supine reset / no floor ejection + joint speed cap, stronger joint_acc and action_rate),
# warm-started from the latest v7d model.
# Smoke test -> N iters -> eval -> stance check (from falls and standing start) -> 2x2 demo -> policies/getup_v7e.
# Usage: bash chain_getup_v7e.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v7e
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_getup_v7d_n2048 | tail -1))
run=getup_v7e_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v7e] $(date) smoke test" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name v7esmoke \
  --agent.logger tensorboard --agent.resume True --agent.load-run $WARM > ~/projects/dance_logs/smoke_getup_v7e.log 2>&1
ok=$?; rm -rf $R/*_v7esmoke
grep -E "Episode_Reward/(rise_schedule|rise_speed|joint_speed_cap|stand_template)" ~/projects/dance_logs/smoke_getup_v7e.log | tail -4 | tee -a $L
if [ $ok -ne 0 ]; then grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v7e.log | tail -8; exit 1; fi
echo "[v7e] $(date) warm start from $WARM" | tee -a $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v7e] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v7e] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK
bash ~/dance_win/rl/smooth_check.sh $CK --skip 0.1
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7e_final "G1 get-up v7e (smooth 2-3.5 s get-up)"
mkdir -p ~/dance_win/policies/getup_v7e
cp $CK ~/dance_win/policies/getup_v7e/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v7e/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v7e, warm start from $WARM)" > ~/dance_win/policies/getup_v7e/SOURCE.txt
echo "[v7e] done $(date)"
