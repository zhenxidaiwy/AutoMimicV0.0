#!/usr/bin/env bash
# Sequential install of the three envs (parallel conda creates corrupt the shared pkgs cache).
source ~/miniforge3/etc/profile.d/conda.sh
rm -f ~/miniforge3/pkgs/libsqlite-3.54.1-h0737f62_100.conda
rm -rf ~/miniforge3/pkgs/libsqlite-3.54.1-h0737f62_100
for e in unitree_rl_mjlab gmr gvhmr; do
  # remove half-created envs (no python binary)
  [ -d ~/miniforge3/envs/$e ] && [ ! -x ~/miniforge3/envs/$e/bin/python ] && rm -rf ~/miniforge3/envs/$e
done
L=~/projects/dance_logs
for s in 03_env_mjlab 04_env_gmr 05_env_gvhmr; do
  echo "=== $s $(date +%T)"
  bash ~/dance_win/scripts/setup/$s.sh > $L/$s.log 2>&1
  echo "exit=$? ; tail:"; tail -6 $L/$s.log
done
