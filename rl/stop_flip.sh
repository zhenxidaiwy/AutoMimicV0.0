#!/usr/bin/env bash
# Stop the backflip round runner and its trainer/evaluator (only processes started by flip_round.sh).
pkill -f "flip_round.sh" ; pkill -f "train_dance.py.*backflip_" ; pkill -f "eval_flip.py" ; sleep 3
pgrep -af "train_dance.py|eval_flip.py" || echo "nothing running"
