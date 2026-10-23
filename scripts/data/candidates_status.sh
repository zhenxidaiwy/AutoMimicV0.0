#!/usr/bin/env bash
# candidates_status.sh: mp4 count per motion folder + failed downloads by platform
cd ~/projects/dance/raw/candidates_2026-10-23 || exit 1
for d in */; do printf '%-36s %s\n' "$d" "$(ls "$d" | grep -c '\.mp4$')"; done
echo "failed: bilibili $(grep -c bilibili failed.txt 2>/dev/null) youtube $(grep -c youtube failed.txt 2>/dev/null)"
echo "total mp4: $(find . -name '*.mp4' | wc -l)"
