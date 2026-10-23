#!/usr/bin/env bash
LOGGER=tensorboard bash ~/dance_win/rl/train_getup.sh 512 5
grep -E "Learning iteration 4/|Mean reward|Mean episode length|Traceback|Error|line [0-9]+," ~/projects/dance_logs/train_getup_n512.log | tail -6
