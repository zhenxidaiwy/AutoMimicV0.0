#!/usr/bin/env bash
# Rebuild the standing template (ankle-midpoint origin) and re-run the v7 smoke test + v6c baseline.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
python ~/dance_win/rl/make_stand_template.py
conda deactivate
bash ~/dance_win/rl/smoke_getup_v7.sh
