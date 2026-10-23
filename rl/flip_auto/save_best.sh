#!/usr/bin/env bash
# save_best.sh <round dir substring> <ckpt> <name>: keep a backflip checkpoint + its eval video/table as a named policy
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*$1 | tail -1)
P=~/dance_win/policies/$3; mkdir -p $P
cp $dir/$2 $P/policy.pt
cp ~/projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz $P/reference_motion.npz
cp ~/projects/dance/dataset/backflip_3/labels_50fps.npz $P/labels_50fps.npz
cp $dir/eval/flip_peek_${2%.pt}.mp4 $P/eval.mp4 2>/dev/null
cp $dir/eval/flip_peek_${2%.pt}_steps.tsv $P/eval_steps.tsv 2>/dev/null
cp $dir/eval/flip_peek_${2%.pt}.json $P/eval.json 2>/dev/null
echo "source: $dir/$2 (knee limit 120 N.m, EDU)" > $P/SOURCE.txt
ls -la $P
