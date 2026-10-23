#!/usr/bin/env bash
# Start the live server with its log in ~/projects/dance_logs/live_server.log (used by start_live.ps1).
bash ~/dance_win/live/stop_server.sh
bash ~/dance_win/live/server.sh "$@" > ~/projects/dance_logs/live_server.log 2>&1
