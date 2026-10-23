#!/usr/bin/env bash
# Package the get-up policy used by the live follow-dance demo (harness round 8, selected checkpoint).
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
D=$(ls -d $R/*_auto_r08 | tail -1); P=~/dance_win/policies/getup_auto_r08; mkdir -p $P
cp $D/model_24998.pt $P/policy.pt
cp ~/projects/dance_logs/auto/r08/knobs.json $P/knobs.json
cp ~/projects/dance_logs/auto/r08/metrics.json $P/metrics.json 2>/dev/null
cp ~/dance_win/videos/getup/auto_r08.mp4 $P/demo.mp4
echo "source: $D/model_24998.pt (task Dance-Recovery-G1-auto, harness round 8; user: 'auto_r08 is good enough')" > $P/SOURCE.txt
ls -la $P
