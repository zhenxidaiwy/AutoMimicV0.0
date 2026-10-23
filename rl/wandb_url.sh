#!/usr/bin/env bash
# Print the W&B run URL and any wandb errors from a training log. Usage: bash wandb_url.sh <run>
L=~/projects/dance_logs/train_$1.log
grep -oE "https://[^ ]*/runs/[A-Za-z0-9]+" $L | tail -1
grep -E "wandb: (ERROR|WARNING)|Traceback|Error" $L | head -5
grep -E "Learning iteration" $L | tail -1
