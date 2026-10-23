#!/usr/bin/env bash
# Read-only probe of tools needed for the dance pipeline.
source ~/miniforge3/etc/profile.d/conda.sh
echo "## conda envs"; conda env list
echo "## tools"
for t in git ffmpeg yt-dlp uv gcc g++ cmake nvcc; do printf "%-8s " "$t"; command -v $t || echo "MISSING"; done
ffmpeg -version 2>/dev/null | head -1
echo "## apt libs"
dpkg -l | grep -E "libyaml-cpp-dev|libboost-all-dev|libeigen3-dev|libspdlog-dev|libfmt-dev|libegl1|libosmesa" | awk '{print $2, $3}'
echo "## dirs"; ls ~/projects
echo "## cuda libs"; ls /usr/lib/wsl/lib | head -20
