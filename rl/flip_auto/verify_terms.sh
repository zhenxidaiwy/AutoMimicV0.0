#!/usr/bin/env bash
# verify_terms.sh K: check that round K's training loaded what the decision asked for
L=~/projects/dance_logs/train_flipauto_r$(printf %02d $1).log
tail -n 2 ~/projects/dance_logs/flip_auto.log | cut -c 1-200
grep -E "root_ori ->|flip terminations" $L | cut -c 1-250
grep -o "library fixes: .*" $L | grep -oE "'(lib|agent)_[a-z0-9_]+', [0-9.]+" | tr '\n' ' '; echo
grep -oE "'flip_(stay_down|stand_still|stand_quiet)': [0-9.]+" $L | head -3 | tr '\n' ' '; echo
grep 'Learning iteration' $L | tail -n 1
