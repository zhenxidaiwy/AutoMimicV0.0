#!/usr/bin/env bash
# The first get-up run finished training (model_2499 saved) but is stuck uploading console logs to W&B.
# Stop it so chain_getup.sh can continue; then upload the finished run's local W&B data in the background.
pkill -INT -f "train_getup.py.*run-name getup_n2048 " ; sleep 15
pkill -f "train_getup.py.*run-name getup_n2048 " 2>/dev/null
sleep 2; pgrep -fa "train_getup.py" | cut -c1-120 || true
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/projects/dance/runs
nohup wandb sync --include-online wandb/run-20261019_112845-mgo4irfo > ~/projects/dance_logs/wandb_sync_mgo4irfo.log 2>&1 &
echo "wandb sync started (log: ~/projects/dance_logs/wandb_sync_mgo4irfo.log)"
