#!/usr/bin/env bash
pkill -f "live/server.py" && echo "stopped old server" || echo "no server running"
