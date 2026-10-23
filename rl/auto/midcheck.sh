#!/usr/bin/env bash
# Mid-round check of the latest harness round: training curve + key terms + last harness log lines.
A=~/projects/dance_logs/auto
N=$(ls -d $A/r[0-9][0-9] | tail -1 | sed 's/.*r//')
echo "round $N"
bash ~/dance_win/rl/auto/diag_round.sh $((10#$N)) | tail -4
bash ~/dance_win/rl/auto/terms_round.sh $((10#$N)) | grep -aE "still_bonus|feet_move_stand|floor_stall|stand_up|stand_template|squat_template|Mean reward" | head -7
tail -n 2 $A/harness.log | cut -c1-160
