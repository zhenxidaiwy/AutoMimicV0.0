#!/usr/bin/env bash
# v6 get-up: 2500 iters -> eval -> resume +2500 (total 5000) -> eval + 2x2 demo video.
export GETUP_TASK=Dance-Recovery-G1-v6
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
bash ~/dance_win/rl/train_getup_v6.sh 2048 2500
FIRST=$(ls -d $R/*_getup_v6_n2048 | tail -1); FIRST=$(basename $FIRST)
echo "[chain_v6] first run: $FIRST $(date)"
CKPT=$(ls $R/$FIRST/model_*.pt | sort -V | tail -1) bash ~/dance_win/rl/eval_getup.sh --video
RESUME=$FIRST bash ~/dance_win/rl/train_getup_v6.sh 2048 2500
SECOND=$(ls -d $R/*_getup_v6_n2048_resume | tail -1)
CK=$(ls $SECOND/model_*.pt | sort -V | tail -1)
echo "[chain_v6] final checkpoint: $CK $(date)"
CKPT=$CK bash ~/dance_win/rl/eval_getup.sh --video
bash ~/dance_win/rl/demo_getup.sh $CK getup_v6_final "G1 get-up v6 (slow & realistic reward, iter 5000)"
mkdir -p ~/dance_win/policies/getup_v6
cp $CK ~/dance_win/policies/getup_v6/policy.pt; cp $SECOND/*.onnx $SECOND/params/*.yaml ~/dance_win/policies/getup_v6/ 2>/dev/null
echo "source: $CK (task Dance-Recovery-G1-v6)" > ~/dance_win/policies/getup_v6/SOURCE.txt
echo "[chain_v6] done $(date)"
