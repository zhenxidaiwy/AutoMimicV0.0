"""Where the time of one SuperMimic policy update goes: per imagined step, the model step, FK + jvp velocities, reward,
termination, observation; then the backward pass. Usage: python profile_update.py --spec <dir> --wm <wm.pt>
  --init <model.pt> --motion <clip.npz> --buffer <real.npz> [--n 4096] [--H 32]"""
import argparse
import json
import time
from pathlib import Path

import torch

import imagine as im
import shac_paper as sp


def main(a):
  dev = "cuda"
  if a.tf32:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
  if a.cuboi:
    import cuboi_wm
    model = cuboi_wm.load(a.cuboi, dev)
  else:
    model, _ = im.wm.load(a.wm, dev)
  for p in model.parameters():
    p.requires_grad_(False)
  env = im.ImaginedTracking(model, Path(a.spec) / "spec.json", a.motion, [1.0, 1.0, 0.6], dev)
  buf = sp.Buffer([a.buffer], env.ref.T, dev)
  pol = im.Policy(a.init, dev)
  gen = torch.Generator(device=dev).manual_seed(0)
  # the batched FK (kin) must equal the per-body FK + jvp (kin_jvp)
  st = buf.sample(env, 4096, gen)
  ka, kb = env.kin(st), env.kin_jvp(st)
  print(json.dumps({"kin_vs_jvp_max_abs": {k: float((ka[k] - kb[k]).abs().max()) for k in ("P", "R", "V", "W")},
                    "V_scale": float(kb["V"].abs().max()), "W_scale": float(kb["W"].abs().max())}), flush=True)
  if a.compile:
    env.fk.with_vel = torch.compile(env.fk.with_vel)
    env.reward_terms = torch.compile(env.reward_terms)
  if a.compile_model:
    model.step = torch.compile(model.step)
  tm = {k: 0.0 for k in ("policy", "model", "kin", "reward", "term", "obs", "backward")}

  def tick():
    torch.cuda.synchronize()
    return time.time()

  for rep in range(4):
    if rep == 1:  # the first repetition includes compilation
      t_first = sum(tm.values())
      tm = {k: 0.0 for k in tm}
    st = buf.sample(env, a.n, gen)
    o = env.obs(st)
    J = 0.0
    for _ in range(a.H):
      t = tick(); act = pol(o)
      t1 = tick(); tm["policy"] += t1 - t
      hist = torch.cat([act[None], st["hist"][:-1]])
      s1, dr = model.step(st["s"], act, env.xi.expand(a.n, 3))
      c, sn = torch.cos(st["yaw"]), torch.sin(st["yaw"])
      xy = st["xy"] + torch.stack([c * dr[:, 1] - sn * dr[:, 2], sn * dr[:, 1] + c * dr[:, 2]], -1)
      new = {"s": s1, "xy": xy, "yaw": st["yaw"] + dr[:, 0], "t": (st["t"] + 1).clamp(max=env.ref.T - 1),
             "last": act, "hist": hist, "delay": st["delay"]}
      t2 = tick(); tm["model"] += t2 - t1
      k = env.kin(new)
      t3 = tick(); tm["kin"] += t3 - t2
      rr = env.reward_terms(new, act, st["last"], k)
      t4 = tick(); tm["reward"] += t4 - t3
      d = sp.soft_done(env, new, k, 0.1)
      t5 = tick(); tm["term"] += t5 - t4
      o = env.obs(new, k)
      t6 = tick(); tm["obs"] += t6 - t5
      J = J + sum(rr.values()) * (1 - d)
      st = new
    t = tick(); (-J.mean()).backward(); tm["backward"] += tick() - t
    pol.mlp.zero_grad(set_to_none=True)
  tot = sum(tm.values())
  print(json.dumps({"n": a.n, "H": a.H, "model": "cuboi" if a.cuboi else "wm", "tf32": a.tf32,
                    "compile_model": a.compile_model, "compile": a.compile, "s_first": round(t_first, 1), "s_per_update": round(tot / 3, 3),
                    "share": {k: round(v / tot, 3) for k, v in tm.items()}}), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  for k in ("spec", "wm", "init", "motion", "buffer"):
    ap.add_argument(f"--{k}", required=True)
  ap.add_argument("--n", type=int, default=4096)
  ap.add_argument("--H", type=int, default=32)
  ap.add_argument("--compile", action="store_true")
  ap.add_argument("--compile-model", action="store_true")
  ap.add_argument("--tf32", action="store_true")
  ap.add_argument("--cuboi", default="", help="use the CuboiLeo e8 checkpoint (cuboi_wm.py) instead of --wm")
  main(ap.parse_args())
