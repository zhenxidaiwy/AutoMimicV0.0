#!/usr/bin/env bash
which rsvg-convert inkscape
for e in unitree_rl_mjlab gmr gvhmr; do
  ~/miniforge3/envs/$e/bin/python -c "import cairosvg" 2>/dev/null && echo "cairosvg in $e"
done
fc-list | grep -iE "helvetica|arial|dejavu sans|liberation sans" | head -3
