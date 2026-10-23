#!/usr/bin/env bash
# Wait until chain_getup.sh's resume has really started (resume log loads a checkpoint of the given first run), max 30 min.
first=$1
for i in $(seq 1 180); do
  grep -q "Loading model checkpoint.*$first" ~/projects/dance_logs/train_getup_n2048_resume.log 2>/dev/null && break
  sleep 10
done
grep -m1 "Loading model checkpoint" ~/projects/dance_logs/train_getup_n2048_resume.log
grep -E "Learning iteration" ~/projects/dance_logs/train_getup_n2048_resume.log | tail -1
