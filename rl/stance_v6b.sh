#!/usr/bin/env bash
GETUP_TASK=Dance-Recovery-G1-v6b bash ~/dance_win/rl/stance_check.sh ~/dance_win/policies/getup_v6/policy.pt | grep -E "^joint|torso"
