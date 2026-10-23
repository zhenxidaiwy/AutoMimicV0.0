#!/usr/bin/env bash
# Copy a trained checkpoint + onnx + reference motion + eval video into videoLA/policies/<name>/ (small, self-contained).
# Usage: bash package_policy.sh <run-substring> <model_XXXX> <name>
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$1 | tail -1)
out=~/dance_win/policies/$3; mkdir -p $out
cp $dir/$2.pt $out/policy.pt
cp $dir/*.onnx $out/ 2>/dev/null
cp $dir/params/env.yaml $dir/params/agent.yaml $out/ 2>/dev/null
clip=$(basename $dir | sed -E 's/^[0-9_-]+_//; s/_lock_vlm.*//')
cp ~/projects/dance/dataset/$clip/g1_lock_vlm_50fps.npz $out/reference_motion.npz
cp $dir/eval/$2.mp4 $out/replay_$2.mp4 && cp $dir/eval/$2.json $out/eval_$2.json
echo "train_run_dir: $dir" > $out/SOURCE.txt
ls -la $out
