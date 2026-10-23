#!/usr/bin/env bash
# save_milestone.sh <run dir name> <ckpt> <name>: keep a harness checkpoint + its HD eval (video, json, steps, record)
# and the decision / analysis that produced it as a named policy (never overwrites)
src=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1
P=~/dance_win/policies/$3
[ -e "$P" ] && { echo "$P exists, not overwriting"; exit 1; }
mkdir -p $P
t=${2%.pt}
cp $src/$2 $P/policy.pt
cp ~/projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz $P/reference_motion.npz
cp ~/projects/dance/dataset/backflip_3/labels_50fps.npz $P/labels_50fps.npz
for x in mp4 json _steps.tsv _record.npz; do cp $src/eval/flip_auto_${t}${x/#_/_} $P/ 2>/dev/null; cp $src/eval/flip_auto_${t}.${x} $P/ 2>/dev/null; done
echo "source: $src/$2 (knee limit 120 N.m, G1 EDU)" > $P/SOURCE.txt
ls $P
