#!/usr/bin/env bash
# Disk usage of the dance data folders.
du -sh ~/projects/dance/data/{raw,clips,gvhmr,g1,search} ~/projects/dance/dataset ~/projects/dance/runs 2>/dev/null
du -sh ~/dance_win/data/qa 2>/dev/null
echo "raw files: $(ls ~/projects/dance/data/raw | wc -l)"
