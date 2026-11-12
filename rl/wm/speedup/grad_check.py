"""Is the BPTT gradient useful? On a fixed batch of RSI start states, J(theta) = mean H-step imagined tracking return
(no critic). Compare the first-order prediction eps * |g| with the actual change J(theta + eps g/|g|) - J(theta),
for several H and eps. If the actual change does not follow the prediction at small eps, the gradient is chaotic.
Usage: python grad_check.py <record dir> <wm.pt> [--envs 2048]"""
import argparse
import json
from pathlib import Path

import torch

import imagine as im


def J(env, pol, st0, H):
  st = {k: v.clone() for k, v in st0.items()}
  o = env.obs(st)
  ret, alive = 0.0, torch.ones(len(st["t"]), device=env.dev)
  for h in range(H):
    st, rr, term, k = env.step(st, pol(o))
    o = env.obs(st, k)
    ret = ret + alive * sum(rr.values()) * im.DT
    alive = alive * (~term & (st["t"] < env.ref.T - 1)).float()
  return ret.mean()


def main(a):
  dev = "cuda"
  d = Path(a.dir)
  spec = json.loads((d / "spec.json").read_text())
  model, _ = im.wm.load(a.wm, dev)
  model.eval()
  for p in model.parameters():
    p.requires_grad_(False)
  env = im.ImaginedTracking(model, d / "spec.json", spec["motion"], [1.0, 1.0, 0.6], dev)
  pol = im.Policy(spec["ckpt"], dev)
  params = list(pol.mlp.parameters())
  g_ = torch.Generator(device=dev).manual_seed(0)
  st0 = env.reset_from_reference(torch.randint(0, env.ref.T - 40, (a.envs,), device=dev, generator=g_))
  res = {}
  for H in (4, 8, 16, 32):
    pol.zero_grad()
    j0 = J(env, pol, st0, H)
    j0.backward()
    g = torch.cat([p.grad.flatten() for p in params])
    gn = g.norm().item()
    row = {"J": round(j0.item(), 5), "grad_norm": round(gn, 4)}
    base = [p.detach().clone() for p in params]
    for eps in (1e-4, 1e-3, 1e-2):
      with torch.no_grad():
        off = 0
        for p, b in zip(params, base):
          n = p.numel(); p.copy_(b + eps * g[off:off + n].view_as(p) / gn); off += n
        j1 = J(env, pol, st0, H).item()
        for p, b in zip(params, base):
          p.copy_(b)
      row[f"eps{eps:g}"] = {"pred": round(eps * gn, 6), "actual": round(j1 - j0.item(), 6)}
    res[f"H{H}"] = row
    print(json.dumps({f"H{H}": row}), flush=True)
  # split of the gradient by term at H=8: which reward terms drive it
  (d / "grad_check.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("dir")
  ap.add_argument("wm")
  ap.add_argument("--envs", type=int, default=2048)
  main(ap.parse_args())
