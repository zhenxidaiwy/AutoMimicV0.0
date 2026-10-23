#!/usr/bin/env bash
# check_decision.sh K: compile the harness, parse decisions/rKK.json and check the protocol files of round K-1
cd ~/dance_win/rl/flip_auto || exit 1
K=$(printf %02d $1); P=$(printf %02d $(( $1 - 1 )))
python3 -m py_compile harness.py && echo "harness compiles"
python3 -c "import json; d = json.load(open('decisions/r$K.json')); print('decision ok, reviewed', d.get('reviewed_sheets'))"
ls analysis/r${P}_quant.md analysis/r${P}_llm.md
ls ~/dance_win/videos/backflip/auto/r$P/ | grep sheet
