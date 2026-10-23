#!/usr/bin/env bash
# Stop the backflip training chain and its trainer (only processes started by train_backflip.sh).
pkill -f "train_backflip.sh" ; pkill -f "train_dance.py.*backflip_" ; sleep 3
pgrep -af "train_dance.py" || echo "no trainer running"
