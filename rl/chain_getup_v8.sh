#!/usr/bin/env bash
# v8 (v7f + squat transition template while rising, feet limit 0.35 m), warm-started from the final v7f model.
# Waits for the v7f chain to finish first.
# Smoke test -> N iters -> eval -> stance check (from falls and standing start) -> 2x2 demo -> policies/getup_v8.
# Usage: bash chain_getup_v8.sh [iters=2500]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v8
while pgrep -f chain_getup_v7f.sh > /dev/null; do sleep 30; done
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_getup_v7f_n2048 | tail -1))
run=getup_v8_n2048; L=~/projects/dance_logs/train_$run.log
echo "[v8] $(date) smoke test" | tee $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name v8smoke \
  --agent.logger tensorboard --agent.resume True --agent.load-run $WARM > ~/projects/dance_logs/smoke_getup_v8.log 2>&1
ok=$?; rm -rf $R/*_v8smoke
grep -E "Episode_Reward/(rise_schedule|rise_speed|feet_spread|squat_template)" ~/projects/dance_logs/smoke_getup_v8.log | tail -4 | tee -a $L
if [ $ok -ne 0 ]; then grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v8.log | tail -8; exit 1; fi
echo "[v8] $(date) warm start from $WARM" | tee -a $L
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations ${1:-2500} \
  --agent.run-name $run --agent.logger wandb --agent.wandb-project g1_dance \
  --agent.resume True --agent.load-run $WARM >> $L 2>&1
echo "[v8] train exit=$? $(date)" | tee -a $L
D=$(ls -d $R/*_$run | tail -1); CK=$(ls $D/model_*.pt | sort -V | tail -1)
echo "[v8] final checkpoint $CK"
CKPT=$CK RUN_FILTER=_$run bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK
bash ~/dance_win/rl/smooth_check.sh $CK --skip 0.1
bash ~/dance_win/rl/demo_getup.sh $CK getup_v8_final "G1 get-up v8 (lying -> squat -> stand)"
mkdir -p ~/dance_win/policies/getup_v8
cp $CK ~/dance_win/policies/getup_v8/policy.pt; cp $D/*.onnx $D/params/*.yaml ~/dance_win/policies/getup_v8/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v8, warm start from $WARM)" > ~/dance_win/policies/getup_v8/SOURCE.txt
echo "[v8] done $(date)"
