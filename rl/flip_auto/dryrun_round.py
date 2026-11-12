"""Dry run of round K of the current task (AUTOMIMIC_TASK) before launching it: knobs = state knobs + defaults +
decisions/rKK.json knobs merged exactly like harness.apply_decision (nothing is written to state / library), then
the reference audit (harness guard) and a 2-iteration training with the SAME train_dance flags at 128 envs.
Usage (unitree_rl_mjlab env): python dryrun_round.py K"""
import copy
import json
import subprocess
import sys

import harness as h
import library as libm
from taskcfg import CLIP, DECISIONS, DL, STATE

K = int(sys.argv[1])
st = json.loads(STATE.read_text()) if STATE.exists() else {"rounds": [], "knobs": copy.deepcopy(h.DEFAULT)}
for key in ("weights", "prior", "terms", "tracking"):
  st["knobs"][key] = {**h.DEFAULT[key], **st["knobs"].get(key, {})}
d = json.loads((DECISIONS / f"r{K:02d}.json").read_text())
for path, val in d.get("knobs", {}).items():
  node = st["knobs"]
  keys = path.split(".")
  for key in keys[:-1]:
    node = node.setdefault(key, {})
  node[keys[-1]] = copy.deepcopy(val)
k = st["knobs"]
print("knobs:", json.dumps(k))
audit = h.ref_audit(k)
print("reference audit:", json.dumps(audit))
waived = {w["check"] if isinstance(w, dict) else w for w in d.get("waive", [])}
bad = [t for t, n in ((audit or {}).get("fires") or {}).items() if n > 0 and f"ref_term:{t}" not in waived]
print("guard:", "REFUSE " + str(bad) if bad else "pass")
motion, labels = h.ref_paths(k)
prior = DL / "dryrun_prior.npz"
h.write_prior(k["prior"], prior, labels)
dyn = DL / "dryrun_dyn.json"
dyn.write_text(json.dumps(libm.active_fixes(libm.load(), CLIP) + k.get("extra_dyn", [])))
cmd = (f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; "
       f"export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off; "
       f"python {h.RL}/train_dance.py --rsi phase --labels {labels} --prior {prior} "
       f"--flip-rewards {k['flip_rewards']} --flip-weights '{json.dumps(k['weights'])}' "
       f"--flip-terms '{json.dumps(k.get('terms', {}))}' --dyn-rewards {dyn} "
       f"--tracking-scale {k.get('tracking', {}).get('scale', 1.0)} "
       f"--tracking-std-scale {k.get('tracking', {}).get('std_scale', 1.0)} "
       f"--knee-limit {k['knee_limit']} --ee-threshold {k['ee_threshold']} --delay-ms {k.get('delay_ms', 0)} "
       f"--hand-friction {k.get('hand_friction', 0)} "
       f"--anchor-pos-threshold {k['anchor_pos_threshold']} -- --motion-file {motion} "
       f"--env.scene.num-envs 128 --agent.max-iterations 2 --agent.run-name dryrun_{CLIP} --agent.logger tensorboard "
       f"2>&1 | grep -E 'train_dance|Traceback|Error|Learning iteration 1/|Episode_Termination' | cut -c 1-400; "
       f"rm -rf {h.LOGS}/*_dryrun_{CLIP}")
print(f"motion {motion}\nlabels {labels}\ninit: {d.get('init')}")
subprocess.run(["bash", "-c", cmd])
