#!/usr/bin/env bash
# Serial GPU work (never run two GPU jobs at once): finish slow clip, redo failed/trimmed clips, process street sub-shots,
# then postprocess clips that already have VLM annotations.
S=~/dance_win/scripts/data
bash $S/retarget_only.sh tonyfu_sss_slow
bash $S/reset_clip.sh bda_ming_gxdsm_a hoodie_sss
bash $S/process_clips.sh
bash $S/postprocess.sh tonyfu_sss_single tonyfu_sss_slow
echo BATCH3_DONE
