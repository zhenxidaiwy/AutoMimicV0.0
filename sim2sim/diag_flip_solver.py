"""Why do mjlab (mujoco_warp, float32) and native MuJoCo (float64) disagree most at the backflip take-off?
Native only. Along the native frame-0 closed loop of a backflip policy, for every policy step the pre-step state is
re-stepped (4 x mj_step, same ctrl) under variants and the next qvel compared with the nominal step:
  iters100   : solver iterations 10 -> 100, tolerance 1e-8 -> 1e-12 (is the 10-iteration solve converged?)
  f32_state  : qpos / qvel / qacc_warmstart rounded to float32 before stepping (sensitivity to float32 input rounding)
  f32_ctrl   : ctrl rounded to float32
plus the solver iteration count of every nominal substep (cap = 10). Grouped by reference phase.
Usage: python diag_flip_solver.py [--policy backflip_r14_fid2] -> results_flip_<P>_solverdiag.json
"""
import argparse
import json
import sys
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from native_flip import flip_rollout, load_ctx  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--policy", default="backflip_r14_fid2")
a = ap.parse_args()
torch.set_num_threads(1)
pdir, info, g, pol, mot, labels, dt = load_ctx(a)
m = g.m
T = mot.T
# record pre-step states of the native closed loop
d = mujoco.MjData(m)
g.set_state(d, *g.ref_state(mot, 0))
last, pre = np.zeros(29), []
for k in range(T - 1):
  act = pol(g.obs(d, mot, k, last))
  pre.append((d.qpos.copy(), d.qvel.copy(), d.qacc_warmstart.copy(), g.targets(act)))
  g.step(d, act)
  last = act
ref = flip_rollout(g, pol, mot, 0, T - 1)["traj"]
assert np.array_equal(ref[-1], d.qpos), "recording loop != flip_rollout"


def step4(q, v, w, tgt, iters=None, tol=None, f32_state=False, f32_ctrl=False):
  it0, tol0 = m.opt.iterations, m.opt.tolerance
  if iters:
    m.opt.iterations, m.opt.tolerance = iters, tol
  r = (lambda x: x.astype(np.float32).astype(np.float64)) if f32_state else (lambda x: x)
  dd = mujoco.MjData(m)
  g.set_state(dd, r(q), r(v), r(w))
  dd.ctrl[g.act] = tgt.astype(np.float32).astype(np.float64) if f32_ctrl else tgt
  niter = []
  for _ in range(g.decim):
    mujoco.mj_step(m, dd)
    niter.append(int(np.asarray(dd.solver_niter).reshape(-1)[0]))
  m.opt.iterations, m.opt.tolerance = it0, tol0
  return dd.qvel.copy(), niter


rows = []
for k, (q, v, w, tgt) in enumerate(pre):
  base, nit = step4(q, v, w, tgt)
  rows.append(dict(k=k, niter_max=max(nit), hit_cap=int(sum(n >= m.opt.iterations for n in nit)),
                   iters100=float(np.abs(step4(q, v, w, tgt, 100, 1e-12)[0] - base).max()),
                   f32_state=float(np.abs(step4(q, v, w, tgt, f32_state=True)[0] - base).max()),
                   f32_ctrl=float(np.abs(step4(q, v, w, tgt, f32_ctrl=True)[0] - base).max())))
pn = [str(x) for x in labels["phase_names"]]
ph = labels["phase"]
out = dict(policy=a.policy, mujoco=mujoco.__version__, iterations_cap=int(m.opt.iterations), by_phase={})
for p in sorted(set(ph[:T - 1].tolist())):
  sel = [r for r in rows if ph[r["k"]] == p]
  if not sel:
    continue
  arr = lambda key: np.array([r[key] for r in sel], float)
  out["by_phase"][pn[p]] = dict(
    steps=len(sel), substeps_at_iteration_cap_frac=round(float(arr("hit_cap").sum() / (4 * len(sel))), 3),
    niter_median=float(np.median(arr("niter_max"))),
    **{f"{key}_qvel_diff_{s}": float(fn(arr(key))) for key in ("iters100", "f32_state", "f32_ctrl")
       for s, fn in (("median", np.median), ("max", np.max))},
    **{f"{key}_frac_gt_0_1": float(np.mean(arr(key) > 0.1)) for key in ("iters100", "f32_state", "f32_ctrl")})
  print(pn[p], json.dumps(out["by_phase"][pn[p]]), flush=True)
out["per_step"] = rows
(HERE / f"results_flip_{a.policy}_solverdiag.json").write_text(json.dumps(out, indent=1))
