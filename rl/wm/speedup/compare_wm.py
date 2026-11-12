"""Open-loop fidelity of world models on our held-out mjlab data (logged executed actions): errors after H steps in
physical units. Models: wm.py checkpoints (e.g. v1b) and the CuboiLeo adapter (cuboi_wm.py).
Usage: python compare_wm.py --data <file.npz>[,...] --wm <wm.pt> --cuboi <ckpt.pt> [--windows 4000] [--cpu]"""
import argparse
import json

import torch

import cuboi_wm
import imagine as im

wm = im.wm


@torch.no_grad()
def errors(model, b, H):
  S, R = model.rollout(b["s"][:, 0], b["a"][:, :H], b["xi"])
  T = b["s"][:, : H + 1]
  e_h = (S[..., 0] - T[..., 0]).abs()
  e_j = (S[..., 13:42] - T[..., 13:42]).abs().mean(-1)
  Rp, Rt = wm.six_to_mat(S[..., 1:7]), wm.six_to_mat(T[..., 1:7])
  e_t = torch.rad2deg(torch.arccos((((Rp.transpose(-1, -2) @ Rt).diagonal(dim1=-2, dim2=-1).sum(-1) - 1) / 2).clamp(-1, 1)))
  e_v = (S[..., 7:10] - T[..., 7:10]).norm(dim=-1)

  def integ(dr):
    yaw = torch.cumsum(dr[..., 0], 1)
    yp = torch.cat([torch.zeros_like(yaw[:, :1]), yaw[:, :-1]], 1)
    c, s = torch.cos(yp), torch.sin(yp)
    return torch.stack([torch.cumsum(c * dr[..., 1] - s * dr[..., 2], 1), torch.cumsum(s * dr[..., 1] + c * dr[..., 2], 1)], -1)
  e_xy = (integ(R) - integ(b["droot"][:, :H])).norm(dim=-1)
  f = lambda x: round(x[:, -1].mean().item(), 4)
  return {"height_m": f(e_h), "joint_rad": f(e_j), "tilt_deg": f(e_t), "lin_vel_mps": f(e_v), "xy_m": f(e_xy)}


def main(a):
  dev = "cpu" if a.cpu else "cuda"
  seq = wm.Sequences(a.data.split(","), 32, dev, torch.float32)
  sel = torch.randperm(len(seq), generator=torch.Generator().manual_seed(0))[: a.windows].to(dev)
  b = seq.windows(sel)
  b["xi"] = b["xi"].clone()
  b["xi"][:, 1] = 1.0  # kp scale nominal (the cuboi model has none; wm.py models get the logged value otherwise)
  models = {}
  if a.wm:
    models["ours_" + a.wm.split("/")[-2]] = wm.load(a.wm, dev)[0].eval()
  if a.cuboi:
    models["cuboi_e8"] = cuboi_wm.load(a.cuboi, dev).eval()
  res = {"windows": int(b["s"].shape[0]), "xi_logged_mean": [round(x, 3) for x in seq.xi[seq.starts[sel]].mean(0).tolist()]}
  for n, m in models.items():
    res[n] = {f"H{h}": errors(m, b, h) for h in (1, 8, 32)}
  print(json.dumps(res, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--data", required=True)
  ap.add_argument("--wm", default="")
  ap.add_argument("--cuboi", default="")
  ap.add_argument("--windows", type=int, default=4000)
  ap.add_argument("--cpu", action="store_true")
  main(ap.parse_args())
