#!/usr/bin/env bash
# Stop every training / eval / live-server process of this project and confirm the GPU is idle.
for p in train_getup.py eval_getup.py train_dance.py eval_ckpt.py live/server.py retrieve_loop.py closed_loop.py; do
  pkill -f "$p" 2>/dev/null
done
sleep 3
left=$(pgrep -fa "train_getup|eval_getup|train_dance|eval_ckpt|live/server|retrieve_loop|closed_loop")
if [ -n "$left" ]; then echo "still running:"; echo "$left"; else echo "no project processes running"; fi
nvidia-smi --query-gpu=utilization.gpu,power.draw,memory.used --format=csv,noheader
