#!/usr/bin/env bash
# Re-run selected closed loops with rendering, then compose side-by-side demo videos.
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*multi_train_v1_adaptive_n4096 | tail -1)
ck=$(ls $dir/model_*.pt | sort -V | tail -1)
CL=~/dance_win/vla/closed_loop.sh; P=~/miniforge3/envs/gmr/bin/python; D=~/dance_win/vla/demo_video.py
# pick a v1_aux seed that completed gym_sss, and one that completed bda_ming_gxdsm_a
best() { for s in 0 1 2; do f=~/projects/dance/vla/closed_loop/${1}_model_${2}_s${s}_lat5.json
  grep -q '"completed": true' $f 2>/dev/null && { echo ${2}_s$s; return; }; done; echo ${2}_s0; }
g=$(best gym_sss v1_aux); m=$(best bda_ming_gxdsm_a v1_aux); sh=shadow_s0
echo "using gym:$g ming:$m shadow:$sh"
bash $CL gym_sss $g $ck --latency 5 --video --tag _vid
bash $CL gym_sss $sh $ck --latency 5 --video --tag _vid
bash $CL bda_ming_gxdsm_a $m $ck --latency 5 --video --tag _vid
$P $D gym_sss_model_${g}_lat5_vid --title "Ours: watches an UNSEEN performer (real video keypoints) -> G1 follows Shan Shen Bu"
$P $D gym_sss_model_${sh}_lat5_vid --title "Baseline: frame-wise shadowing of the same video"
$P $D bda_ming_gxdsm_a_model_${m}_lat5_vid --title "Ours: unseen performer, Gou Xiong Duo Suo Mao"
echo MAKE_DEMOS_DONE
