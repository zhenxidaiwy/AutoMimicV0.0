#!/usr/bin/env bash
# v7d (v7c + no payoff for rushing: schedule-capped stand-up reward, time-gated standing terms; target 2-3.5 s),
# warm-started from the final v7c model.
# Smoke test -> N iters -> eval -> stance check (from falls and standing start) -> 2x2 demo -> policies/getup_v7d.
# Usage: bash chain_getup_v7d.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v7d
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_getup_v7c_n2048 | tail -1))
run=getup_v7d_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v7d] $(date) smoke test" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name v7dsmoke \
  --agent.logger tensorboard --agent.resume True --agent.load-run $WARM > ~/projects/dance_logs/smoke_getup_v7d.log 2>&1
ok=$?; rm -rf $R/*_v7dsmoke
grep -E "Episode_Reward/(rise_schedule|rise_speed|waist_limit|stand_template)" ~/projects/dance_logs/smoke_getup_v7d.log | tail -4 | tee -a $L
if [ $ok -ne 0 ]; then grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v7d.log | tail -8; exit 1; fi
echo "[v7d] $(date) warm start from $WARM" | tee -a $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v7d] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v7d] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7d_final "G1 get-up v7d (2-3.5 s get-up + standing template)"
mkdir -p ~/dance_win/policies/getup_v7d
cp $CK ~/dance_win/policies/getup_v7d/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v7d/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v7d, warm start from $WARM)" > ~/dance_win/policies/getup_v7d/SOURCE.txt
echo "[v7d] done $(date)"
