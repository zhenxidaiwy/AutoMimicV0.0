#!/usr/bin/env bash
# Clone the three upstream repos into ~/projects and print their pinned commits.
cd ~/projects
for r in unitreerobotics/unitree_rl_mjlab zju3dv/GVHMR YanjieZe/GMR; do
  n=$(basename "$r")
  [ -d "$n" ] || git clone -q "https://github.com/$r.git" "$n"
  echo "$n $(git -C "$n" log -1 --format='%h %cd' --date=short)"
done
