#!/usr/bin/env bash
# Run as root: wsl -d Ubuntu-22.04 -u root -- bash /home/user/dance_win/scripts/setup/01_apt_root.sh
# ffmpeg: video cutting / GVHMR IO. The rest: unitree_rl_mjlab C++ sim2sim deploy (libyaml-cpp, boost, eigen, spdlog, fmt).
set -e
export DEBIAN_FRONTEND=noninteractive
for i in 1 2 3; do apt-get update -q && break; sleep 5; done
apt-get install -y -q ffmpeg libyaml-cpp-dev libboost-all-dev libeigen3-dev libspdlog-dev libfmt-dev
ffmpeg -version | head -1
