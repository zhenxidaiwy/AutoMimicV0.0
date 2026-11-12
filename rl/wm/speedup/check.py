"""S2 gate: is the imagined env a faithful stand-in for mjlab? On a record.py rollout:
  a) policy: our Policy(obs_real) == the recorded action
  b) obs: imagined obs on the real state == mjlab's actor obs (per term block)
  c) reward: our reward terms on the real state == mjlab's per-term step reward
  d) closed loop: the same policy from the same real states, H steps in the world model vs the real continuation
Usage: python check.py <record dir> <wm.pt> [--H 32]"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imagine as im  # noqa: E402
import wm  # noqa: E402
from fk import quat_to_mat  # noqa: E402

TRACK = ("motion_global_root_pos", "motion_global_root_ori", "motion_body_pos", "motion_body_ori",
         "motion_body_lin_vel", "motion_body_ang_vel")


def real_states(z, dev):
  f = lambda k: torch.tensor(z[k], dtype=torch.float32, device=dev)
  R = quat_to_mat(f("root_quat"))
  yaw = wm.yaw_of(R)
  Rrel = wm.rot_z(yaw).transpose(-1, -2) @ R
  Rt = R.transpose(-1, -2)
  v, w = (Rt @ f("root_lin_vel").unsqueeze(-1)).squeeze(-1), (Rt @ f("root_ang_vel").unsqueeze(-1)).squeeze(-1)
  pos = f("root_pos")
  s = torch.cat([pos[..., 2:3], wm.mat_to_six(Rrel), v, w, f("joint_pos"), f("joint_vel")], -1)
  return s, pos[..., :2], yaw


def main(a):
  dev = "cuda"
  d = Path(a.dir)
  z = np.load(d / "real.npz")
  spec = json.loads((d / "spec.json").read_text())
  model, _ = wm.load(a.wm, dev)
  model.eval()
  env = im.ImaginedTracking(model, d / "spec.json", spec["motion"], [1.0, 1.0, a.hand_friction], dev)
  pol = im.Policy(spec["ckpt"], dev)
  S, XY, YAW = real_states(z, dev)
  T, N = S.shape[:2]
  act = torch.tensor(z["action"], device=dev)
  obs = torch.tensor(z["obs"], device=dev)
  fr = torch.tensor(z["frame"], dtype=torch.long, device=dev)
  done = torch.tensor(z["done"], device=dev)
  done[:-1] |= fr[1:] != fr[:-1] + 1  # clip-end teleports
  rew = torch.tensor(z["reward"], device=dev)
  terms = [str(x) for x in z["terms"]]
  res = {}
  with torch.no_grad():
    # a) policy
    res["policy_max_abs_diff"] = round((pol(obs) - act).abs().max().item(), 5)
    # b) obs at t >= 1 (needs a_{t-1}), only steps not right after a reset
    ok = torch.ones(T, N, dtype=torch.bool, device=dev); ok[0] = False; ok[1:] &= ~done[:-1]
    t_, n_ = torch.nonzero(ok, as_tuple=True)
    st = env.make_state(S[t_, n_], XY[t_, n_], YAW[t_, n_], fr[t_, n_], last_act=act[t_ - 1, n_])
    o = env.obs(st)
    blocks = {"command": (0, 58), "anchor_ori": (58, 64), "ang_vel": (64, 67), "joint_pos": (67, 96),
              "joint_vel": (96, 125), "actions": (125, 154)}
    res["obs_max_abs_diff"] = {k: round((o[:, i:j] - obs[t_, n_, i:j]).abs().max().item(), 4) for k, (i, j) in blocks.items()}
    # c) reward recorded at step t lives on state t+1 (frame t+1), action a_t, previous a_{t-1}
    ok2 = torch.zeros(T, N, dtype=torch.bool, device=dev); ok2[1:-1] = ~done[1:-1] & ~done[:-2]
    t_, n_ = torch.nonzero(ok2, as_tuple=True)
    st = env.make_state(S[t_ + 1, n_], XY[t_ + 1, n_], YAW[t_ + 1, n_], fr[t_ + 1, n_], last_act=act[t_, n_])
    r = env.reward_terms(st, act[t_, n_], act[t_ - 1, n_])
    res["reward_mean_ours_vs_mjlab"] = {n: [round(r[n].mean().item(), 4), round(rew[t_, n_, terms.index(n)].mean().item(), 4),
                                            round((r[n] - rew[t_, n_, terms.index(n)]).abs().max().item(), 4)] for n in r}
    # d) closed loop from real states: windows of H steps without reset / teleport
    H = a.H
    lo, hi = (int(x) for x in a.frames.split(",")) if a.frames else (-1, 10 ** 9)
    starts = [(t0, n) for t0 in range(1, T - H, a.every) for n in range(N)
              if not done[t0 - 1:t0 + H, n].any() and lo <= int(fr[t0, n]) <= hi]
    t0 = torch.tensor([s[0] for s in starts], device=dev); n0 = torch.tensor([s[1] for s in starts], device=dev)
    st = env.make_state(S[t0, n0], XY[t0, n0], YAW[t0, n0], fr[t0, n0], last_act=act[t0 - 1, n0])
    o = env.obs(st)
    imag, real, perr = [], [], []
    for h in range(H):
      a_ = pol(o)
      st, rr, dn, k = env.step(st, a_)
      o = env.obs(st, k)
      imag.append(sum(rr[n] for n in TRACK))
      real.append(rew[t0 + h, n0][:, [terms.index(n) for n in TRACK]].sum(-1))
      # root position error imagined vs real (world), as a drift measure
      perr.append((torch.cat([st["xy"], st["s"][:, :1]], -1) - torch.cat([XY[t0 + h + 1, n0], S[t0 + h + 1, n0, :1]], -1)).norm(dim=-1))
    imag, real, perr = torch.stack(imag, 1), torch.stack(real, 1), torch.stack(perr, 1)
    Ri, Rr = imag.sum(1), real.sum(1)
    corr = torch.corrcoef(torch.stack([Ri, Rr]))[0, 1].item()
    res["closed_loop"] = {"windows": len(starts), "H": H, "return_imag": round(Ri.mean().item(), 3),
                          "return_real": round(Rr.mean().item(), 3),
                          "rel_diff": round((Ri.mean() / Rr.mean() - 1).item(), 4), "return_corr": round(corr, 3),
                          "per_step_imag": [round(x, 3) for x in imag.mean(0)[:: max(H // 8, 1)].tolist()],
                          "per_step_real": [round(x, 3) for x in real.mean(0)[:: max(H // 8, 1)].tolist()],
                          "root_pos_err_m_end": round(perr[:, -1].mean().item(), 3)}
  print(json.dumps(res, indent=1))
  (d / f"check_H{H}{'_f' + a.frames.replace(',', '-') if a.frames else ''}.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("dir")
  ap.add_argument("wm")
  ap.add_argument("--H", type=int, default=32)
  ap.add_argument("--every", type=int, default=10)
  ap.add_argument("--frames", default="", help="only windows starting at these reference frames, e.g. 46,80 (support)")
  ap.add_argument("--hand-friction", type=float, default=0.6)
  main(ap.parse_args())
