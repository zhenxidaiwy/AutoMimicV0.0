#!/usr/bin/env bash
# 闪身步 amplitude with the specialist tracker (policies/sss_bda_v1 = the model_1000 the user liked) vs canon_v1:
# (1) oracle: canonical clip played continuously, (2) live follow on gym_sss (snap playback), + timing analysis.
O=~/projects/dance_logs/follow_analysis; mkdir -p $O
SP="0=$HOME/dance_win/policies/sss_bda_v1/policy.pt,1=$HOME/dance_win/policies/gxdsm_full_v1/policy.pt"
bash ~/dance_win/live/server.sh --bench gym_sss --bench_seconds 14 --playback oracle --dance_ckpts "$SP" \
  --rec $O/oracle_spec.npz 2>&1 | grep -E "tracker:|done:|Error|Traceback|line [0-9]+," | cut -c1-160
bash ~/dance_win/live/server.sh --bench gym_sss --bench_seconds 18 --playback snap --dance_ckpts "$SP" \
  --rec $O/gym_sss_spec.npz 2>&1 | grep -E "done:|Error|Traceback|line [0-9]+," | cut -c1-160
~/miniforge3/envs/gmr/bin/python ~/dance_win/live/spread_stats.py oracle oracle_spec gym_sss_snap gym_sss_spec
cd ~/dance_win/live && ~/miniforge3/envs/gmr/bin/python analyze_follow.py $O/gym_sss_spec.npz gym_sss | grep -E "model prediction|robot reference|median"
