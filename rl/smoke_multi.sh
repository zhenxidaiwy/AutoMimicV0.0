#!/usr/bin/env bash
# Short multi-motion smoke run (tensorboard), then show the key lines.
LOGGER=tensorboard bash ~/dance_win/rl/train_multi.sh train_v1 adaptive 512 15
grep -E "MultiMotion|PhaseRSI|Learning iteration 1[45]/|Mean episode length|Traceback|Error" \
  ~/projects/dance_logs/train_multi_train_v1_adaptive_n512.log | tail -8
