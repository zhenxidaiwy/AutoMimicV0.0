#!/usr/bin/env bash
p=$(pgrep -f train_getup.py | head -1)
echo "pid $p  state/cpu: $(ps -o stat=,%cpu=,etime= -p $p)"
echo "log last modified: $(date -r ~/projects/dance_logs/train_getup_n2048_resume.log)   now: $(date)"
nvidia-smi --query-gpu=utilization.gpu,power.draw,memory.used --format=csv,noheader
echo "uptime: $(uptime)"
ls -la --time-style=+%H:%M ~/projects/dance/runs/logs/rsl_rl/g1_recovery/2026-10-19_12-29-06_getup_n2048_resume/model_*.pt | sort -V -k7 | tail -2
cat /proc/$p/wchan 2>/dev/null; echo
tail -c 400 ~/projects/dance_logs/train_getup_n2048_resume.log
