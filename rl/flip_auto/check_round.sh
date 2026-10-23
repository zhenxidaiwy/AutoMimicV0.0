#!/usr/bin/env bash
# check_round.sh <round>: settings actually used by a round's training run
L=~/projects/dance_logs/train_flipauto_r$(printf %02d $1).log
grep '=== round' ~/projects/dance_logs/flip_auto.log | tail -n 1 | cut -c 1-120
grep -E 'fidelity|flip terminations' $L | cut -c 1-250
grep -oE "'flip_(leg_sym|tuck|feet_together|spin)': [0-9.]+" $L | head -4
grep 'Learning iteration' $L | tail -n 1
