#!/usr/bin/env bash
# What chain / training processes are alive?
date
pgrep -fa "chain_getup|train_getup|eval_getup|demo_getup" || echo "none"
