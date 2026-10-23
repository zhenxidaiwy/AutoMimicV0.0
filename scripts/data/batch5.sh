#!/usr/bin/env bash
# Serial: redo trimmed clips (cut-free now), finish gxdsm_a heuristic lock, annotation prep for street_b.
S=~/dance_win/scripts/data
bash $S/reset_clip.sh latin_sss bda2_gxdsm_wide bda2_gxdsm_full
bash $S/process_clips.sh
~/miniforge3/envs/gmr/bin/python $S/foot_lock.py bda_ming_gxdsm_a --contacts heuristic
bash $S/to_npz.sh -v lock_heuristic bda_ming_gxdsm_a
bash $S/annot_prep_many.sh 2 street_sss_b
bash $S/annot_prep_many.sh 3 bda2_gxdsm_wide bda2_gxdsm_full
bash $S/annot_prep_many.sh 4 latin_sss
echo BATCH5_DONE
