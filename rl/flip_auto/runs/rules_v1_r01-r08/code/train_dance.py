"""Train a G1 tracking policy on a dance clip with a selectable RSI strategy (wraps unitree_rl_mjlab/scripts/train.py).

Usage (unitree_rl_mjlab env):
  python train_dance.py --rsi {uniform,adaptive,phase,phase_adaptive} --labels <labels_50fps.npz> \
      [--task Unitree-G1-Tracking-No-State-Estimation] -- <TrainConfig args, e.g. --motion-file X.npz
      --env.scene.num-envs 2048 --agent.max-iterations 3000 --agent.run-name foo>
Logs go to ~/projects/dance/runs/logs/rsl_rl/<experiment>/<time>_<run-name>/
"""
import argparse
import dataclasses
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"
HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--rsi", required=True, choices=["uniform", "adaptive", "phase", "phase_adaptive"])
  ap.add_argument("--labels", default=None, help="labels_50fps.npz with rsi_weight (needed for phase*)")
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--prior-power", type=float, default=1.0)
  ap.add_argument("--prior", default=None, help="explicit rsi_weight npz (e.g. multi-motion dance-balance prior); "
                  "used with any --rsi mode")
  ap.add_argument("--ee-threshold", type=float, default=None,
                  help="override the hand/foot height-error termination threshold (m); <= 0 removes that termination "
                       "(backflip probe: 0.25 m ended 90%% of episodes within 0.3 s)")
  ap.add_argument("--effort-scale", type=float, default=1.0,
                  help="DIAGNOSTIC ONLY: multiply every actuator effort limit (is a motion torque-limited?)")
  ap.add_argument("--flip-rewards", type=float, default=0.0,
                  help="backflip technique rewards (rl/flip_rewards.py) with weights x this; needs --labels")
  ap.add_argument("--anchor-pos-threshold", type=float, default=None, help="override torso height termination (m)")
  ap.add_argument("--anchor-ori-threshold", type=float, default=None, help="override torso orientation termination")
  ap.add_argument("--flip-weights", default=None,
                  help="JSON {term: weight} overriding rl/flip_rewards.WEIGHTS (before --flip-rewards scaling)")
  ap.add_argument("--flip-terms", default=None,
                  help="JSON {termination name: {threshold params}} from rl/flip_rewards.py (backflip hard limits)")
  ap.add_argument("--tracking-scale", type=float, default=1.0,
                  help="fidelity curriculum: multiply the weights of the motion-tracking rewards")
  ap.add_argument("--tracking-std-scale", type=float, default=1.0,
                  help="fidelity curriculum: multiply the std of the motion-tracking rewards (< 1 = stricter fit)")
  ap.add_argument("--dyn-rewards", default=None,
                  help="JSON file: [{name, func, weight, params}] fix templates from the harness diagnostic library")
  ap.add_argument("--knee-limit", type=float, default=None,
                  help="real-robot knee effort limit (N.m): the open-source cfg uses 139, G1 spec sheets give 90 (base) "
                       "/ 120 (EDU); hip roll keeps its value")
  ours, rest = ap.parse_known_args()
  if rest and rest[0] == "--":
    rest = rest[1:]
  if ours.rsi.startswith("phase") and not ours.labels:
    sys.exit("--labels is required for phase RSI")

  sys.path.insert(0, str(REPO))
  sys.path.insert(0, str(HERE))
  import wandb

  # rsl_rl 5.0.1 passes wandb.Settings(start_method="thread"); wandb >= 0.2x removed that field -> drop it.
  _Settings = wandb.Settings
  wandb.Settings = lambda *a, **kw: _Settings(*a, **{k: v for k, v in kw.items() if k != "start_method"})
  import mjlab
  import mjlab.tasks  # noqa: F401  (populate registry)
  import src.tasks  # noqa: F401
  import tyro
  from phase_rsi import PhaseMotionCommandCfg

  spec = importlib.util.spec_from_file_location("ur_train", REPO / "scripts" / "train.py")
  T = importlib.util.module_from_spec(spec)
  sys.modules["ur_train"] = T  # tyro inspects the source of TrainConfig via its module
  spec.loader.exec_module(T)

  args = tyro.cli(T.TrainConfig, args=rest, default=T.TrainConfig.from_task(ours.task), config=mjlab.TYRO_FLAGS)
  old = args.env.commands["motion"]
  kw = {f.name: getattr(old, f.name) for f in dataclasses.fields(old) if f.init}
  kw["sampling_mode"] = "uniform" if ours.rsi in ("uniform", "phase") else "adaptive"
  kw["frame_weight_file"] = str(Path(ours.labels).expanduser().resolve()) if ours.rsi.startswith("phase") else None
  if ours.prior:
    kw["frame_weight_file"] = str(Path(ours.prior).expanduser().resolve())
  kw["prior_power"] = ours.prior_power
  args.env.commands["motion"] = PhaseMotionCommandCfg(**kw)
  print(f"[train_dance] rsi={ours.rsi} sampling_mode={kw['sampling_mode']} prior={kw['frame_weight_file']}")
  if ours.effort_scale != 1.0:
    art = args.env.scene.entities["robot"].articulation
    art.actuators = tuple(dataclasses.replace(c, effort_limit=c.effort_limit * ours.effort_scale) for c in art.actuators)
    print(f"[train_dance] DIAGNOSTIC effort limits x{ours.effort_scale}: {[c.effort_limit for c in art.actuators]}")
  if ours.tracking_scale != 1.0 or ours.tracking_std_scale != 1.0:
    for name in ("motion_global_root_pos", "motion_global_root_ori", "motion_body_pos", "motion_body_ori",
                 "motion_body_lin_vel", "motion_body_ang_vel"):
      t = args.env.rewards.get(name)
      if t is None:
        continue
      t.weight *= ours.tracking_scale
      if "std" in t.params:
        t.params["std"] *= ours.tracking_std_scale
    print(f"[train_dance] fidelity curriculum: tracking weights x{ours.tracking_scale}, "
          f"std x{ours.tracking_std_scale}")
  if ours.knee_limit is not None:
    from flip_rewards import set_knee_limit
    set_knee_limit(args.env.scene.entities["robot"].articulation, ours.knee_limit)
    print(f"[train_dance] knee effort limit -> {ours.knee_limit} N.m (real G1)")
  if ours.flip_rewards > 0:
    import json as _json

    import flip_rewards as _fr
    if ours.flip_weights:
      _fr.WEIGHTS.update(_json.loads(ours.flip_weights))
    from flip_rewards import add_flip_rewards
    add_flip_rewards(args.env.rewards, str(Path(ours.labels).expanduser().resolve()), ours.flip_rewards)
    if "motion_global_root_pos" in args.env.rewards:  # height only once the reference has landed (round 6 drift)
      from mjlab.managers.reward_manager import RewardTermCfg as _RT
      old = args.env.rewards["motion_global_root_pos"]
      args.env.rewards["motion_global_root_pos"] = _RT(
        func=_fr.flip_root_pos, weight=old.weight,
        params={"labels": str(Path(ours.labels).expanduser().resolve()), "std": old.params.get("std", 0.3)})
      print("[train_dance] motion_global_root_pos -> flip_root_pos (z only after the reference landing)")
    if "motion_global_root_ori" in args.env.rewards:  # tilt only (heading free) after landing (round 7 waist twist)
      old = args.env.rewards["motion_global_root_ori"]
      args.env.rewards["motion_global_root_ori"] = _RT(
        func=_fr.flip_root_ori, weight=old.weight,
        params={"labels": str(Path(ours.labels).expanduser().resolve()), "std": old.params.get("std", 0.4)})
      print("[train_dance] motion_global_root_ori -> flip_root_ori (tilt only after the reference landing)")
    if ours.dyn_rewards:
      dyn = _json.loads(Path(ours.dyn_rewards).read_text())
      _fr.add_dyn_rewards(args.env.rewards, str(Path(ours.labels).expanduser().resolve()), dyn)
      print(f"[train_dance] library fixes: {[(d['name'], d['weight']) for d in dyn]}")
    if ours.flip_terms:
      _fr.add_flip_terminations(args.env.terminations, str(Path(ours.labels).expanduser().resolve()),
                                _json.loads(ours.flip_terms))
      print(f"[train_dance] flip terminations: {_json.loads(ours.flip_terms)}")
    print(f"[train_dance] flip rewards x{ours.flip_rewards}: "
          f"{ {k: v.weight for k, v in args.env.rewards.items() if k.startswith('flip_')} }")
  for name, thr in (("anchor_pos", ours.anchor_pos_threshold), ("anchor_ori", ours.anchor_ori_threshold)):
    if thr is not None:
      args.env.terminations[name].params["threshold"] = thr
      print(f"[train_dance] {name} termination threshold -> {thr}")
  if ours.ee_threshold is not None:
    if ours.ee_threshold <= 0:
      args.env.terminations.pop("ee_body_pos", None)
    else:
      args.env.terminations["ee_body_pos"].params["threshold"] = ours.ee_threshold
    print(f"[train_dance] ee_body_pos termination: {args.env.terminations.get('ee_body_pos')}")

  run_root = Path.home() / "projects" / "dance" / "runs"
  run_root.mkdir(parents=True, exist_ok=True)
  os.chdir(run_root)  # train.py writes logs/rsl_rl/... relative to cwd
  T.launch_training(task_id=ours.task, args=args)
