"""Probe (dev helper for native_getup.py): checkpoint keys, model sensors, rl cfg, obs terms of the get-up env.
Usage (unitree_rl_mjlab env, WSL): python probe_getup.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(HERE.parent / "rl"))
os.environ.setdefault("GETUP_TASK", "Dance-Recovery-G1-auto")
os.environ.setdefault("GETUP_KNOBS", str(HERE.parent / "policies" / "getup_auto_r08" / "knobs.json"))

import mujoco
import torch

ck = torch.load(HERE.parent / "policies" / "getup_auto_r08" / "policy.pt", weights_only=False, map_location="cpu")
print("ckpt keys:", list(ck.keys()))
for k, v in ck.items():
  if isinstance(v, dict):
    for kk, vv in v.items():
      print("  ", k, kk, tuple(vv.shape) if torch.is_tensor(vv) else type(vv))

m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "getup.mjb"))
print("sensors:", [(m.sensor(i).name, int(m.sensor_type[i]), int(m.sensor_objtype[i]), int(m.sensor_objid[i]),
                    int(m.sensor_dim[i]), int(m.sensor_adr[i])) for i in range(m.nsensor)])
print("sites:", [m.site(i).name for i in range(m.nsite)])
print("opt:", m.opt)
print("ngeom", m.ngeom, "nbody", m.nbody, "njnt", m.njnt)
print("jnt0", m.joint(0).name, m.jnt_type[0])
print("act trnid:", m.actuator_trnid[:, 0].tolist())
print("ctrlrange", m.actuator_ctrlrange[:3].tolist(), "ctrllimited", m.actuator_ctrllimited.tolist())
print("forcelimited", m.actuator_forcelimited.tolist())
print("dyntype", m.actuator_dyntype.tolist(), "gaintype", m.actuator_gaintype.tolist(), "biastype", m.actuator_biastype.tolist())
print("qpos0", m.qpos0.tolist())

import mjlab.tasks  # noqa: F401
import getup  # noqa: F401
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
cfg = load_env_cfg("Dance-Recovery-G1-auto", play=True)
print("events:", {k: (v.mode, getattr(v.func, "__name__", str(v.func))) for k, v in cfg.events.items()})
print("actor terms:", {k: (getattr(v.func, "__name__", str(v.func)), v.params, v.scale, v.clip, v.noise,
                           getattr(v, "history_length", None)) for k, v in cfg.observations["actor"].terms.items()})
print("actor group:", {k: getattr(cfg.observations["actor"], k) for k in vars(cfg.observations["actor"]) if k != "terms"})
print("commands:", cfg.commands["twist"])
rl = load_rl_cfg("Dance-Recovery-G1-auto")
print("rl clip_actions:", rl.clip_actions, "actor:", rl.actor)
print("sim:", cfg.sim)
