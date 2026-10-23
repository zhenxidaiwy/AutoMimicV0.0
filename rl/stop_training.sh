#!/usr/bin/env bash
# Stop any running dance training (keeps its log dir and saved checkpoints).
pkill -INT -f train_dance.py; sleep 5; pkill -f train_dance.py
sleep 2; ps -eo pid,args | grep train_dance | grep -v grep || echo "no training running"
nvidia-smi --query-gpu=memory.used --format=csv,noheader
