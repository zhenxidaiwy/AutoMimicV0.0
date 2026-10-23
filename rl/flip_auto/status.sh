#!/usr/bin/env bash
# Harness status: current round, iteration, recent training reward terms.
grep '=== round' ~/projects/dance_logs/flip_auto.log | tail -n 2 | cut -c 1-60
f=$(ls -t ~/projects/dance_logs/train_flipauto_r*.log | head -1)
echo "$f"
grep 'Learning iteration' "$f" | tail -n 1
for t in "Mean episode length" flip_pushoff flip_spin flip_airborne flip_plane_axis flip_leg_sym flip_land; do
  grep -E "$t" "$f" | tail -n 1 | sed 's/^ *//'
done
