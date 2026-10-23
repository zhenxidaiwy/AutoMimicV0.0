#!/usr/bin/env bash
# Usage: bash run_bg.sh <script.sh> [args...]  -> runs detached with nohup, log in ~/projects/dance_logs/<name>.log
mkdir -p ~/projects/dance_logs
sed -i 's/\r$//' "$1"
name=$(basename "$1" .sh)
nohup bash "$@" > ~/projects/dance_logs/"$name".log 2>&1 &
echo "started $name pid=$! log=~/projects/dance_logs/$name.log"
