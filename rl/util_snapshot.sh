#!/usr/bin/env bash
# 5 samples (1 s apart) of GPU util / power / VRAM and the training process CPU usage.
pid=$(pgrep -f "train_getup.py|train_dance.py" | head -1)
echo "nproc $(nproc) | training pid ${pid:-none}"
for i in 1 2 3 4 5; do
  g=$(nvidia-smi --query-gpu=utilization.gpu,power.draw,memory.used --format=csv,noheader)
  c=$([ -n "$pid" ] && ps -o %cpu= -p $pid || echo -)
  echo "gpu: $g | train process cpu: ${c}%"
  sleep 1
done
top -bn1 | head -5 | tail -3
