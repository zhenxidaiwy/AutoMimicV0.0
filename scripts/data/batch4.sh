#!/usr/bin/env bash
# Serial: GVHMR+retarget for new rows (latin, bda2 x2, street_b with relaxed cut threshold),
# postprocess annotated clips, then rebuild the dataset manifest.
S=~/dance_win/scripts/data
bash $S/process_clips.sh
bash $S/postprocess.sh street_sss_a street_sss_c street_sss_d street_sss_e hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b
~/miniforge3/envs/gmr/bin/python $S/build_dataset.py
echo BATCH4_DONE
