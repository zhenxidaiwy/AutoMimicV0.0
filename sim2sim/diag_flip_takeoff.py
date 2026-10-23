"""Where in the physics step do mujoco_warp (mjlab) and native MuJoCo disagree at the backflip take-off?
mjlab rollout from frame 0 (play cfg, knee limit 120, no randomisation, as native_flip.py --mode mjlab). At every
policy step, ONE physics substep is taken in both sims from the identical state / ctrl / qacc_warmstart and the
intermediate quantities of that step are compared (all computed by mj_step's forward pass at the pre-step state):
qfrc_actuator, qfrc_bias, qacc_smooth (smooth dynamics), qfrc_constraint (constraint solve), qacc, the solver iteration
count, nefc / ncon, and the next qvel. Usage (unitree_rl_mjlab env): python diag_flip_takeoff.py [--policy P]
-> results_flip_<P>_takeoffdiag.json
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
from native_flip import build_mjlab, load_ctx  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--policy", default="backflip_r14_fid2")
a = ap.parse_args()
torch.set_num_threads(1)
pdir, info, g, pol, mot, labels, dt = load_ctx(a)
m = g.m
E = build_mjlab(pdir)
env, venv, policy, cmd, start, npy = E["env"], E["venv"], E["policy"], E["cmd"], E["start"], E["npy"]
origin = E["origin"]
tt = lambda x: torch.as_tensor(x, dtype=env.sim.data.qpos.dtype, device=env.sim.data.qpos.device)
wd = env.sim.data
start[0] = 0
env.reset()
wd.qacc_warmstart[0] = tt(np.zeros(m.nv))
obs = venv.get_observations()
pn = [str(x) for x in labels["phase_names"]]
ph = labels["phase"]
FIELDS = ("qfrc_actuator", "qfrc_bias", "qacc_smooth", "qfrc_constraint", "qacc")
rows = []
de = mujoco.MjData(m)
for k in range(mot.T - 1):
  q, v, w = npy(wd.qpos[0]).copy(), npy(wd.qvel[0]).copy(), npy(wd.qacc_warmstart[0]).copy()
  with torch.no_grad():
    act = policy(obs)
  a_np = npy(act[0])
  ctrl = np.zeros(m.nu)
  ctrl[g.act] = g.targets(a_np)
  # single substep from this state in warp (state restored afterwards, then the real env.step)
  wd.ctrl[0] = tt(ctrl)
  env.sim.step()
  wr = {f: npy(getattr(wd, f)[0]).copy() for f in FIELDS}
  wr["qvel"] = npy(wd.qvel[0]).copy()
  try:
    wr["niter"] = int(npy(wd.solver_niter).reshape(-1)[0])
  except Exception:  # noqa: BLE001
    wr["niter"] = -1
  wr["nefc"] = int(npy(wd.nefc).reshape(-1)[0])
  wr["ncon"] = int(npy(wd.nacon).reshape(-1)[0])
  qn = q.copy()
  qn[:3] -= origin
  # hand-made implicitfast velocity update from the native forward pass at the pre-step state:
  #   v+ = v + h (M - h D)^-1 (M qacc),  D = d qfrc / d qvel = -dof_damping - kd (joint position actuators)
  # variant 'all': every actuator's -kd in D;  variant 'unclamped': actuators whose PD force is clamped by forcerange
  # contribute no velocity derivative
  g.set_state(de, qn, v, w)
  de.ctrl[:] = ctrl
  mujoco.mj_forward(m, de)
  M = np.zeros((m.nv, m.nv))
  mujoco.mj_fullM(m, M, de.qM)
  f_ = M @ de.qacc
  raw = m.actuator_gainprm[:, 0] * de.ctrl + m.actuator_biasprm[:, 1] * de.actuator_length + \
      m.actuator_biasprm[:, 2] * de.actuator_velocity
  clamped = (m.actuator_forcelimited > 0) & ((raw < m.actuator_forcerange[:, 0]) | (raw > m.actuator_forcerange[:, 1]))
  pred = {}
  for var in ("all", "unclamped"):
    D = -np.diag(m.dof_damping)
    for i in range(m.nu):
      if var == "unclamped" and clamped[i]:
        continue
      D[m.jnt_dofadr[m.actuator_trnid[i, 0]], m.jnt_dofadr[m.actuator_trnid[i, 0]]] += m.actuator_biasprm[i, 2]
    pred[var] = v + m.opt.timestep * np.linalg.solve(M - m.opt.timestep * D, f_)
  g.set_state(de, qn, v, w)
  de.ctrl[:] = ctrl
  mujoco.mj_step(m, de)
  hand = {f"hand_{var}_vs_native": float(np.abs(pred[var] - de.qvel).max()) for var in pred}
  hand.update({f"hand_{var}_vs_warp": float(np.abs(pred[var] - wr["qvel"]).max()) for var in pred})
  hand["n_clamped"] = int(clamped.sum())
  hand["clamped"] = [m.actuator(int(i)).name.replace("robot/", "") for i in np.where(clamped)[0]]
  dvv = np.abs(de.qvel - wr["qvel"])
  hand["worst_dof"] = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, int(m.dof_jntid[int(np.argmax(dvv))])).replace("robot/", "")
  r = dict(k=k, phase=pn[ph[min(k, len(ph) - 1)]], niter_warp=wr["niter"], niter_native=int(np.asarray(de.solver_niter).reshape(-1)[0]),
           nefc_warp=wr["nefc"], nefc_native=int(de.nefc), ncon_warp=wr["ncon"], ncon_native=int(de.ncon),
           qvel_next=float(np.abs(de.qvel - wr["qvel"]).max()), **hand)
  for f in FIELDS:
    x = np.asarray(getattr(de, f))
    r[f] = float(np.abs(x - wr[f]).max())
    r[f + "_scale"] = float(np.abs(x).max())
  rows.append(r)
  # restore and take the real policy step
  wd.qpos[0], wd.qvel[0], wd.qacc_warmstart[0] = tt(q), tt(v), tt(w)
  env.sim.forward()
  with torch.no_grad():
    obs, _, _, _ = venv.step(act)
out = dict(policy=a.policy, by_phase={}, per_step=rows)
for p in dict.fromkeys(r["phase"] for r in rows):
  sel = [r for r in rows if r["phase"] == p]
  arr = lambda key: np.array([r[key] for r in sel], float)
  out["by_phase"][p] = dict(steps=len(sel), **{f"{f}_max": float(arr(f).max()) for f in FIELDS + ("qvel_next",)},
                            **{f"{f}_median": float(np.median(arr(f))) for f in ("qfrc_constraint", "qacc", "qvel_next")},
                            niter_warp_max=int(arr("niter_warp").max()), niter_native_max=int(arr("niter_native").max()),
                            niter_warp_at_cap_frac=float(np.mean(arr("niter_warp") >= m.opt.iterations)),
                            nefc_equal_frac=float(np.mean(arr("nefc_warp") == arr("nefc_native"))),
                            **{f"{k}_max": float(arr(k).max()) for k in ("hand_all_vs_native", "hand_unclamped_vs_native",
                                                                       "hand_all_vs_warp", "hand_unclamped_vs_warp")},
                            steps_with_clamped_actuator=int((arr("n_clamped") > 0).sum()))
  print(p, json.dumps(out["by_phase"][p]), flush=True)
# all steps: is a large native-vs-warp next-qvel difference tied to force-clamped actuators?
big = [r for r in rows if r["qvel_next"] > 0.05]
out["steps_qvel_next_gt_0_05"] = dict(n=len(big), with_clamped_actuator=sum(r["n_clamped"] > 0 for r in big),
                                      steps_without_large_diff_with_clamped=sum(r["n_clamped"] > 0 for r in rows
                                                                                if r["qvel_next"] <= 0.05),
                                      total_steps=len(rows))
print("[clamp]", json.dumps(out["steps_qvel_next_gt_0_05"]), flush=True)
for r in rows:
  if r["phase"] in ("takeoff",) or r["qvel_next"] > 0.05:
    print(json.dumps(r), flush=True)
(HERE / f"results_flip_{a.policy}_takeoffdiag.json").write_text(json.dumps(out, indent=1))
