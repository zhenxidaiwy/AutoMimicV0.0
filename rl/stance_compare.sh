#!/usr/bin/env bash
echo "== v6b final"
GETUP_TASK=Dance-Recovery-G1-v6b bash ~/dance_win/rl/stance_check.sh ~/dance_win/policies/getup_v6/policy.pt
echo "== v5 final"
GETUP_TASK=Dance-Recovery-G1 bash ~/dance_win/rl/stance_check.sh ~/dance_win/policies/getup_v5/policy.pt
