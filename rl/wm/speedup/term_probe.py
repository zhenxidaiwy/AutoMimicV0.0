"""Why do imagined rollouts end? Per termination condition, imagined (from RSI and from real states) vs real mjlab.
Usage: python term_probe.py <record dir> <wm.pt> [--H 32]"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

import imagine as im
from check import real_states


def conds(env, st, k):
  t, r, th = st["t"], env.ref, env.thr
  za = (r.bp[t, env.a_ref, 2] - k["P"][:, env.a_fk, 2]).abs() > th["anchor_pos"]
  zo = (r.bR[t, env.a_ref][:, 2, 2] - k["R"][:, env.a_fk][:, 2, 2]).abs() > th["anchor_ori"]
  ze = ((r.bp[t][:, env.ref_track][:, env.ee, 2] - k["P"][:, env.fk_track][:, env.ee, 2]).abs() > th["ee_body_pos"]).any(-1)
  return {"anchor_pos": za, "anchor_ori": zo, "ee_body_pos": ze}


def roll(env, pol, st, H):
  hit = {n: torch.zeros(len(st["t"]), dtype=torch.bool, device=env.dev) for n in ("anchor_pos", "anchor_ori", "ee_body_pos")}
  first_t = torch.full((len(st["t"]),), -1, device=env.dev)
  alive = torch.ones(len(st["t"]), dtype=torch.bool, device=env.dev)
  o = env.obs(st)
  for h in range(H):
    st, _, term, k = env.step(st, pol(o))
    o = env.obs(st, k)
    c = conds(env, st, k)
    for n in hit:
      hit[n] |= c[n] & alive
    first_t = torch.where(term & alive, st["t"], first_t)
    alive &= ~term
  return {"ended": round(1 - alive.float().mean().item(), 3), **{n: round(v.float().mean().item(), 3) for n, v in hit.items()}}, first_t


def main(a):
  dev = "cuda"
  d = Path(a.dir)
  spec = json.loads((d / "spec.json").read_text())
  model, _ = im.wm.load(a.wm, dev)
  model.eval()
  env = im.ImaginedTracking(model, d / "spec.json", spec["motion"], [1.0, 1.0, 0.6], dev)
  pol = im.Policy(spec["ckpt"], dev)
  z = np.load(d / "real.npz")
  done = torch.tensor(z["done"]); fr = torch.tensor(z["frame"]).long()
  tele = torch.zeros_like(done); tele[:-1] = fr[1:] != fr[:-1] + 1
  res = {"real_term_per_step": round((done & ~tele).float().mean().item(), 5),
         "real_term_frames": np.bincount(fr[:-1][(done & ~tele)[:-1]].numpy() // 20 * 20, minlength=1).nonzero()[0].tolist()}
  with torch.no_grad():
    g = torch.Generator(device=dev).manual_seed(0)
    frames = torch.randint(0, env.ref.T - a.H - 1, (4096,), device=dev, generator=g)
    r1, ft = roll(env, pol, env.reset_from_reference(frames), a.H)
    res["imag_from_rsi"] = r1
    ok = ft >= 0
    res["imag_rsi_start_frames_of_ended"] = np.histogram(frames[ok].cpu().numpy(), bins=[0, 46, 81, 131, 200, 500])[0].tolist()
    res["imag_rsi_start_frames_all"] = np.histogram(frames.cpu().numpy(), bins=[0, 46, 81, 131, 200, 500])[0].tolist()
    S, XY, YAW = real_states(z, dev)
    T, N = S.shape[:2]
    act = torch.tensor(z["action"], device=dev); dn = (done | tele).to(dev)
    st_ = [(t0, n) for t0 in range(1, T - a.H, 10) for n in range(N) if not dn[t0 - 1:t0 + a.H, n].any()]
    t0 = torch.tensor([s[0] for s in st_], device=dev); n0 = torch.tensor([s[1] for s in st_], device=dev)
    st = env.make_state(S[t0, n0], XY[t0, n0], YAW[t0, n0], fr.to(dev)[t0, n0], last_act=act[t0 - 1, n0])
    res["imag_from_real_states"], _ = roll(env, pol, st, a.H)
  print(json.dumps(res, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("dir")
  ap.add_argument("wm")
  ap.add_argument("--H", type=int, default=32)
  main(ap.parse_args())
