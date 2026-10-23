#!/usr/bin/env bash
date
pgrep -fa "chain_getup|train_getup.py|eval_getup.py" | cut -c1-150
echo "== first-run log tail:"; grep -E "Learning iteration|exit=" ~/projects/dance_logs/train_getup_n2048.log | tail -2
echo "== resume log head/tail:"; head -1 ~/projects/dance_logs/train_getup_n2048_resume.log
grep -E "Loading model checkpoint" ~/projects/dance_logs/train_getup_n2048_resume.log | tail -1
grep -E "Learning iteration|exit=" ~/projects/dance_logs/train_getup_n2048_resume.log | tail -1
ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*
