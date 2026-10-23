#!/usr/bin/env bash
# Harness self-test: (1) auto task trains 3 iterations with squat RSI, (2) metrics.py on the latest v7f checkpoint,
# (3) harness scoring / knob rules on that measurement (no training).
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_getup_v7f_n2048 | tail -1))
CK=$(ls $R/$WARM/model_*.pt | sort -V | tail -1)
T=~/projects/dance_logs/auto_selftest; mkdir -p $T
export GETUP_TASK=Dance-Recovery-G1-auto
echo "== (1) smoke train auto task from $WARM"
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 \
  --agent.max-iterations 3 --agent.run-name autosmoke --agent.logger tensorboard --agent.resume True \
  --agent.load-run $WARM > $T/smoke.log 2>&1
echo "exit=$?"; rm -rf $R/*_autosmoke
grep -E "Traceback|Error|line [0-9]+," $T/smoke.log | tail -6
grep -E "Episode_Reward/(squat_template|feet_spread|rise_schedule|stand_template)" $T/smoke.log | tail -4
echo "== (2) metrics on $CK"
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $T/fall.json > $T/m1.log 2>&1
echo "exit=$?"; grep -E "Traceback|Error|line [0-9]+," $T/m1.log | tail -6
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $T/stand.json --stand_start > $T/m2.log 2>&1
echo "exit=$?"; grep -E "Traceback|Error|line [0-9]+," $T/m2.log | tail -6
cat $T/fall.json $T/stand.json
echo "== (3) harness rules on that measurement"
~/miniforge3/envs/gmr/bin/python - <<EOF
import json, math, sys
sys.path.insert(0, "/home/user/dance_win/rl/auto")
import harness as h
m = json.load(open("$T/fall.json")); m.update(json.load(open("$T/stand.json")))
m["t_stand_min_pose"] = min(v["t_stand"] for v in m["per_pose"].values())
print("score", round(h.score(m), 2))
print({n: h.check(m, *s) for n, s in h.TARGETS.items()})
k, ch = h.adjust(h.AUTO_DEFAULT_KNOBS, m)
print("\n".join(ch))
EOF
