#!/usr/bin/env bash
# Postprocess the last 4 annotated clips, summarise foot-lock results, rebuild manifest.
S=~/dance_win/scripts/data; P=~/miniforge3/envs/gmr/bin/python
bash $S/postprocess.sh street_sss_b bda2_gxdsm_wide bda2_gxdsm_full latin_sss
$P $S/summarize_lock.py
$P $S/build_dataset.py
echo BATCH6_DONE
