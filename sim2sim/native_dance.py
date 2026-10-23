"""Sim2sim for the two DANCE specialist tracking policies (Unitree-G1-Tracking-No-State-Estimation, rsl_rl 5.0.1):
  sss   = policies/sss_bda_v1     (闪身步)
  gxdsm = policies/gxdsm_full_v1  (狗熊哆嗦毛)
mjlab (mujoco_warp 3.5.0 on GPU, float32) vs native MuJoCo (CPU, float64) running the exported runtime model
models/dance.mjb with a from-scratch re-implementation of the 154-d actor observation, JointPositionAction and
the rsl_rl actor (obs normaliser + MLP) - no mjlab code is used on the native side.

What --mode mjlab does for one clip (needs the unitree_rl_mjlab env, CUDA):
  1. builds the mjlab play env (num_envs=1) with ALL randomisation off: startup events base_com / encoder_bias /
     foot_friction removed (push_robot is already removed by the play cfg), RSI pose/velocity ranges empty and
     joint_position_range=(0, 0); all terminations except time_out removed (falls are detected identically in
     both sims by this script: torso_link (= motion anchor) z < 0.45 m or torso z-axis . world z < 0.5).
  2. checks that the exported .mjb equals the runtime-compiled mj_model and that the warp model is nominal.
  3. rolls the policy in mjlab from frame 0 and from 8 random frames to the end of the clip. At EVERY step the
     mjlab state is copied into native MjData and (a) the native 154-d observation is compared term by term with
     mjlab's actor observation, (b) the native policy is evaluated on mjlab's observation and compared with the
     mjlab inference policy, (c) the pre-step state + the same action are stepped natively (4 x mj_step) and the
     next qpos/qvel are compared with mjlab's; the contact geom-pair sets of both sims at that identical pre-step
     state are compared too. The same one-step comparison is repeated off-nominal (random pushes every 20 steps;
     action noise N(0, 0.3)) on 2 starts. A separate single-substep test (1 x mj_step vs 1 x mjwarp.step,
     same state, ctrl and qacc_warmstart) is run on 40 states at the end. qacc_warmstart is zeroed after every mjlab
     reset so that both sims start from the same warm start.
  4. runs the policy fully natively from the same initial states (state rebuilt from the npz, checked against
     mjlab's reset state) and computes the same metrics for both sims (mjlab's state k <-> frame start+k-1 pairing,
     checked against mjlab's own online MotionCommand metrics); writes a side-by-side video for frame 0.
  -> results_dance_<clip>.json, traj_dance_<clip>.npz, ~/dance_win/videos/sim2sim/<clip>_side_by_side.mp4

--mode native  (pure mujoco + torch, works in any env, e.g. gmr with MuJoCo 3.16): load models/dance.xml (+ the G1
  meshes from the mjlab asset zoo, + the solver options mjlab applies at runtime), run the native closed loop from
  the same starts, compare with the 3.5.0 trajectories in traj_dance_<clip>.npz -> results_dance_<clip>_<tag>.json
--mode report: merge everything into results_dance.json / results_dance.md

Usage (WSL; see native_dance.sh):
  python native_dance.py --mode mjlab  --clip sss
  python native_dance.py --mode mjlab  --clip gxdsm
  python native_dance.py --mode native --clip sss --xml models/dance.xml --tag mj316      # gmr env
  python native_dance.py --mode report
"""
import argparse
import json
import re
from collections import Counter
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VID_DIR = ROOT / "videos" / "sim2sim"
CLIPS = {"sss": ("sss_bda_v1", "闪身步"), "gxdsm": ("gxdsm_full_v1", "狗熊哆嗦毛")}
TASK = "Unitree-G1-Tracking-No-State-Estimation"
TRACK_BODIES = ("pelvis", "left_hip_roll_link", "left_knee_link", "left_ankle_roll_link", "right_hip_roll_link",
                "right_knee_link", "right_ankle_roll_link", "torso_link", "left_shoulder_roll_link", "left_elbow_link",
                "left_wrist_yaw_link", "right_shoulder_roll_link", "right_elbow_link", "right_wrist_yaw_link")
ANCHOR = "torso_link"
FALL_Z, FALL_UP = 0.45, 0.5
N_RANDOM, SEED = 8, 2026
TERMS = ("command", "motion_anchor_ori_b", "base_ang_vel", "joint_pos", "joint_vel", "actions")
DIMS = (58, 6, 3, 29, 29, 29)
# Solver options mjlab applies to the compiled model at runtime (sim cfg in the env yaml); the scene XML lacks them.
OPT = dict(timestep=0.005, iterations=10, tolerance=1e-8, ls_iterations=20, ls_tolerance=0.01, impratio=1.0,
           ccd_iterations=50)
G1_ASSETS = (Path.home() / "miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab/asset_zoo/robots/"
             "unitree_g1/xmls/assets")


# ----------------------------------------------------------------------------------------------- math (wxyz quats)
def qmul(a, b):
  w1, x1, y1, z1 = a
  w2, x2, y2, z2 = b
  return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                   w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def qconj(q):
  return np.array([q[0], -q[1], -q[2], -q[3]])


def qmat(q):
  q = np.asarray(q, dtype=np.float64)
  m = np.zeros(9)
  mujoco.mju_quat2Mat(m, q / np.linalg.norm(q))
  return m.reshape(3, 3)


def yaw_of(q):
  w, x, y, z = q
  return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def yaw_quat(q):
  h = 0.5 * yaw_of(q)
  return np.array([np.cos(h), 0.0, 0.0, np.sin(h)])


def quat_angle(q1, q2):
  """Rotation angle (rad) between two orientations (= mjlab quat_error_magnitude)."""
  q1 = np.asarray(q1, float) / np.linalg.norm(q1)
  q2 = np.asarray(q2, float) / np.linalg.norm(q2)
  d = qmul(q1, qconj(q2))
  return float(2 * np.arctan2(np.linalg.norm(d[1:]), abs(d[0])))


# ------------------------------------------------------------------------------------------------- native pieces
class Motion:
  """Reference clip exactly as mjlab's MotionLoader holds it (50 fps = one frame per 20 ms policy step)."""

  def __init__(self, path):
    z = np.load(path)
    self.path = str(path)
    self.fps = float(np.asarray(z["fps"]).reshape(-1)[0]) if "fps" in z.files else None
    f32 = lambda k: np.asarray(z[k], dtype=np.float32).astype(np.float64)  # mjlab stores float32 tensors
    self.jp, self.jv = f32("joint_pos"), f32("joint_vel")
    self.bp, self.bq = f32("body_pos_w"), f32("body_quat_w")
    self.blv, self.bav = f32("body_lin_vel_w"), f32("body_ang_vel_w")
    self.T = self.jp.shape[0]


class Policy:
  """rsl_rl 5.0.1 actor re-implemented on CPU: (obs - mean) / (std + 1e-2) -> MLP(512,256,128, ELU) -> mean action."""

  def __init__(self, path):
    sd = torch.load(path, map_location="cpu", weights_only=False)["actor_state_dict"]
    self.mean, self.std = sd["obs_normalizer._mean"].float(), sd["obs_normalizer._std"].float()
    self.eps = 1e-2
    lin = sorted({int(k.split(".")[1]) for k in sd if k.startswith("mlp.") and k.endswith(".weight")})
    layers = []
    for i, li in enumerate(lin):
      w = sd[f"mlp.{li}.weight"]
      layer = torch.nn.Linear(w.shape[1], w.shape[0])
      layer.weight.data.copy_(w)
      layer.bias.data.copy_(sd[f"mlp.{li}.bias"])
      layers.append(layer)
      if i < len(lin) - 1:
        layers.append(torch.nn.ELU())
    self.net = torch.nn.Sequential(*layers).eval()

  @torch.no_grad()
  def __call__(self, obs):
    x = torch.as_tensor(np.asarray(obs, dtype=np.float32))[None]
    return self.net((x - self.mean) / (self.std + self.eps))[0].numpy().astype(np.float64)


class NativeG1:
  """Observation / action / stepping of the tracking task on a plain MuJoCo model."""

  def __init__(self, model, info):
    m = self.m = model
    self.info = info
    J = mujoco.mjtObj.mjOBJ_JOINT
    self.jnames = info["joint_names"]
    jids = [mujoco.mj_name2id(m, J, "robot/" + n) for n in self.jnames]
    assert min(jids) >= 0, "joint names not found"
    self.qadr = np.array([m.jnt_qposadr[j] for j in jids])
    self.dadr = np.array([m.jnt_dofadr[j] for j in jids])
    self.act = np.array([int(np.where((m.actuator_trnid[:, 0] == j) & (m.actuator_trntype == 0))[0][0]) for j in jids])
    self.default = np.array(info["default_joint_pos"])
    at = info["action_terms"]["joint_pos"]
    self.scale, self.offset = np.array(at["scale"]), np.array(at["offset"])
    rng = m.jnt_range[jids]
    mid, half = rng.mean(1), 0.5 * (rng[:, 1] - rng[:, 0]) * 0.9  # mjlab soft_joint_pos_limit_factor = 0.9
    self.soft_lo, self.soft_hi = mid - half, mid + half
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SENSOR, "robot/imu_ang_vel")
    self.gyro = slice(int(m.sensor_adr[sid]), int(m.sensor_adr[sid]) + 3)
    B = mujoco.mjtObj.mjOBJ_BODY
    self.bid = {n: mujoco.mj_name2id(m, B, "robot/" + n) for n in info["body_names"]}
    self.mot_idx = {n: i for i, n in enumerate(info["body_names"])}  # npz body axis = robot body order
    self.decim = int(info["decimation"])
    fj = mujoco.mj_name2id(m, J, "robot/floating_base_joint")
    self.rq, self.rv = int(m.jnt_qposadr[fj]), int(m.jnt_dofadr[fj])
    self.track = [self.bid[n] for n in TRACK_BODIES]
    self.track_mot = [self.mot_idx[n] for n in TRACK_BODIES]

  def ref_state(self, mot, f):
    """Reset state of MotionCommand._resample_command with all randomisation off (robot placed on frame f)."""
    qpos, qvel = np.zeros(self.m.nq), np.zeros(self.m.nv)
    quat = mot.bq[f, 0]
    qpos[self.rq:self.rq + 3] = mot.bp[f, 0]
    qpos[self.rq + 3:self.rq + 7] = quat
    qpos[self.qadr] = np.clip(mot.jp[f], self.soft_lo, self.soft_hi)
    qvel[self.rv:self.rv + 3] = mot.blv[f, 0]
    qvel[self.rv + 3:self.rv + 6] = qmat(quat).T @ mot.bav[f, 0]  # world ang vel -> free-joint local frame
    qvel[self.dadr] = mot.jv[f]
    return qpos, qvel

  def set_state(self, d, qpos, qvel, warm=None):
    mujoco.mj_resetData(self.m, d)
    d.qpos[:] = qpos
    d.qvel[:] = qvel
    if warm is not None:
      d.qacc_warmstart[:] = warm
    mujoco.mj_forward(self.m, d)

  def targets(self, a):
    return a * self.scale + self.offset  # JointPositionAction (encoder bias = 0)

  def step(self, d, a):
    d.ctrl[self.act] = self.targets(a)
    for _ in range(self.decim):
      mujoco.mj_step(self.m, d)
    mujoco.mj_forward(self.m, d)  # mjlab calls sim.forward() before computing observations

  def obs_terms(self, d, mot, t, last_a):
    R_rob = d.xmat[self.bid[ANCHOR]].reshape(3, 3)
    R_ref = qmat(mot.bq[t, self.mot_idx[ANCHOR]])
    rel = R_rob.T @ R_ref  # subtract_frame_transforms(robot anchor, ref anchor) -> rotation matrix
    return [np.concatenate([mot.jp[t], mot.jv[t]]), rel[:, :2].reshape(-1), d.sensordata[self.gyro].copy(),
            d.qpos[self.qadr] - self.default, d.qvel[self.dadr].copy(), np.asarray(last_a, dtype=np.float64)]

  def obs(self, d, mot, t, last_a):
    return np.concatenate(self.obs_terms(d, mot, t, last_a)).astype(np.float32)

  def fell(self, d):
    a = self.bid[ANCHOR]
    return bool(d.xpos[a, 2] < FALL_Z or d.xmat[a, 8] < FALL_UP)


def native_rollout(g, pol, mot, f, nsteps):
  d = mujoco.MjData(g.m)
  g.set_state(d, *g.ref_state(mot, f))
  last, t, traj = np.zeros(29), f, [d.qpos.copy()]
  t0 = time.perf_counter()
  for _ in range(nsteps):
    a = pol(g.obs(d, mot, t, last))
    g.step(d, a)
    last, t = a, t + 1
    traj.append(d.qpos.copy())
    if g.fell(d):
      break
  wall = time.perf_counter() - t0
  return np.array(traj), wall


# ------------------------------------------------------------------------------------------------------- metrics
EE_BODIES = ("left_ankle_roll_link", "right_ankle_roll_link", "left_wrist_yaw_link", "right_wrist_yaw_link")
TERM_Z, TERM_ORI = 0.25, 0.8  # training terminations anchor_pos (z only), anchor_ori, ee_body_pos (z only)


def frame_metrics(g, dk, dprev, mot, t, qpos, qpos_prev):
  """Robot state after policy step k (qpos) vs reference frame t = start + k - 1, i.e. the pairing mjlab uses for its
  MotionCommand error_* metrics (CommandManager.compute() runs _update_metrics() BEFORE _update_command() advances
  time_steps) and that the training rewards / terminations see (they run before command_manager.compute() in
  ManagerBasedRlEnv.step). body_pos_relative_w is the one built by the previous _update_command(): reference frame t
  moved to the robot anchor of the PREVIOUS state (qpos_prev) in xy + yaw, reference anchor height kept."""
  dk.qpos[:] = qpos
  mujoco.mj_kinematics(g.m, dk)
  dprev.qpos[:] = qpos_prev
  mujoco.mj_kinematics(g.m, dprev)
  a, ai = g.bid[ANCHOR], g.mot_idx[ANCHOR]
  rq_rob, rq_ref = dk.xquat[a].copy(), mot.bq[t, ai]
  rp_rob, rp_ref = dk.xpos[a].copy(), mot.bp[t, ai]
  dp = dprev.xpos[a].copy()
  dp[2] = rp_ref[2]
  dR = qmat(yaw_quat(qmul(dprev.xquat[a].copy(), qconj(rq_ref))))
  rel = dp + (mot.bp[t, g.track_mot] - rp_ref) @ dR.T
  body_err = float(np.linalg.norm(rel - dk.xpos[g.track], axis=1).mean())
  ee = [TRACK_BODIES.index(n) for n in EE_BODIES]
  ee_z_err = np.abs(rel[ee, 2] - dk.xpos[[g.track[i] for i in ee], 2])
  jerr = qpos[g.qadr] - mot.jp[t]

  def spread(pl, pr, pelvis_q):
    y = yaw_of(pelvis_q)
    dd = pl - pr
    return abs(-np.sin(y) * dd[0] + np.cos(y) * dd[1])

  la, ra, pv = g.bid["left_ankle_roll_link"], g.bid["right_ankle_roll_link"], g.bid["pelvis"]
  lm, rm = g.mot_idx["left_ankle_roll_link"], g.mot_idx["right_ankle_roll_link"]
  R_rob, R_ref = qmat(rq_rob), qmat(rq_ref)
  # training-time termination criteria (only reported; all three terms of the policies' env.yaml):
  #   anchor_pos  : |anchor z err| > 0.25 m      anchor_ori : |projected-gravity z diff| > 0.8
  #   ee_body_pos : any of the 4 ankle/wrist bodies with |z err vs body_pos_relative_w| > 0.25 m
  lost_z = bool(abs(rp_ref[2] - rp_rob[2]) > TERM_Z)
  lost_ori = bool(abs(R_ref[2, 2] - R_rob[2, 2]) > TERM_ORI)
  lost_ee = bool((ee_z_err > TERM_Z).any())
  return dict(
    joint_rms=float(np.sqrt(np.mean(jerr ** 2))), joint_err_norm=float(np.linalg.norm(jerr)),
    anchor_ori_rad=quat_angle(rq_ref, rq_rob), anchor_ori_deg=float(np.degrees(quat_angle(rq_ref, rq_rob))),
    anchor_pos_err=float(np.linalg.norm(rp_ref - rp_rob)),
    body_pos_err=body_err, spread_robot=spread(dk.xpos[la], dk.xpos[ra], dk.xquat[pv]),
    spread_ref=spread(mot.bp[t, lm], mot.bp[t, rm], mot.bq[t, 0]),
    anchor_z=float(rp_rob[2]), upright=float(R_rob[2, 2]),
    lost_anchor_z=lost_z, lost_anchor_ori=lost_ori, lost_ee_z=lost_ee, track_lost=lost_z or lost_ori or lost_ee)


def run_metrics(g, mot, f, traj, dt, with_rows=False):
  """traj[k] = state after k policy steps (traj[0] = reset state). Row k pairs traj[k] with reference frame f+k-1."""
  dk, dprev = mujoco.MjData(g.m), mujoco.MjData(g.m)
  rows = [frame_metrics(g, dk, dprev, mot, f + k - 1, traj[k], traj[k - 1]) for k in range(1, len(traj))]
  fell_at = None
  for k, r in enumerate(rows):
    if r["anchor_z"] < FALL_Z or r["upright"] < FALL_UP:
      fell_at = k + 1
      break
  arr = lambda k: np.array([r[k] for r in rows])
  sr, sf = arr("spread_robot"), arr("spread_ref")
  tl = arr("track_lost")
  res = dict(
    steps=len(rows), fell=fell_at is not None, fell_at_s=None if fell_at is None else round(fell_at * dt, 2),
    joint_rms_rad=round(float(arr("joint_rms").mean()), 4),
    joint_err_norm_rad=round(float(arr("joint_err_norm").mean()), 4),
    anchor_ori_err_deg=round(float(arr("anchor_ori_deg").mean()), 2),
    anchor_ori_err_deg_max=round(float(arr("anchor_ori_deg").max()), 2),
    body_pos_err_m=round(float(arr("body_pos_err").mean()), 4),
    spread_p90_robot_m=round(float(np.percentile(sr, 90)), 4), spread_p90_ref_m=round(float(np.percentile(sf, 90)), 4),
    spread_p90_ratio=round(float(np.percentile(sr, 90) / max(np.percentile(sf, 90), 1e-9)), 3),
    track_lost_frac=round(float(tl.mean()), 3),
    track_lost_terms_frac=dict(anchor_pos_z=round(float(arr("lost_anchor_z").mean()), 3),
                               anchor_ori=round(float(arr("lost_anchor_ori").mean()), 3),
                               ee_body_pos_z=round(float(arr("lost_ee_z").mean()), 3)),
    track_lost_first_s=None if not tl.any() else round((int(np.argmax(tl)) + 1) * dt, 2))
  return (res, rows) if with_rows else res


def divergence(g, ta, tb, dt):
  """Trajectory divergence between two closed loops started from the same state (index k = after k policy steps)."""
  n = min(len(ta), len(tb))
  dk1, dk2 = mujoco.MjData(g.m), mujoco.MjData(g.m)
  out = {}
  for name, k in (("t1s", min(50, n - 1)), ("end", n - 1)):
    dj = np.abs(ta[:k + 1][:, g.qadr] - tb[:k + 1][:, g.qadr])
    dk1.qpos[:], dk2.qpos[:] = ta[k], tb[k]
    mujoco.mj_kinematics(g.m, dk1)
    mujoco.mj_kinematics(g.m, dk2)
    a = g.bid[ANCHOR]
    out[name] = dict(at_s=round(k * dt, 2), bitwise_identical_upto=bool(np.array_equal(ta[:k + 1], tb[:k + 1])),
                     joint_max_abs_upto_rad=round(float(dj.max()), 5),
                     joint_rms_at_rad=round(float(np.sqrt(np.mean(dj[-1] ** 2))), 5),
                     pelvis_pos_diff_at_m=round(float(np.linalg.norm(ta[k][:3] - tb[k][:3])), 5),
                     anchor_ori_diff_at_deg=round(float(np.degrees(quat_angle(dk1.xquat[a], dk2.xquat[a]))), 3))
  return out


def summarize(runs, key):
  rs = [r[key] for r in runs]
  m = lambda k: round(float(np.mean([r[k] for r in rs])), 4)
  return dict(runs=len(rs), falls=int(sum(r["fell"] for r in rs)), joint_rms_rad=m("joint_rms_rad"),
              joint_err_norm_rad=m("joint_err_norm_rad"),
              anchor_ori_err_deg=m("anchor_ori_err_deg"), body_pos_err_m=m("body_pos_err_m"),
              spread_p90_ratio=m("spread_p90_ratio"), track_lost_frac=m("track_lost_frac"))


def stat(x):
  x = np.asarray(x, float)
  if x.size == 0:
    return None
  return dict(median=float(np.median(x)), p99=float(np.percentile(x, 99)), max=float(np.max(x)), n=int(x.size),
              frac_gt_1e_3=float(np.mean(x > 1e-3)), frac_gt_1e_1=float(np.mean(x > 0.1)),
              frac_gt_1=float(np.mean(x > 1.0)))


# ------------------------------------------------------------------------------------------------------ rendering
def render_side_by_side(g, mot, f, ta, tb, labels, out):
  import imageio.v2 as imageio
  try:
    import cv2
  except ImportError:  # labels are optional
    cv2 = None
  m = g.m
  r = mujoco.Renderer(m, 480, 480)
  d, dg = mujoco.MjData(m), mujoco.MjData(m)
  cam = mujoco.MjvCamera()
  cam.type = mujoco.mjtCamera.mjCAMERA_FREE
  cam.distance, cam.azimuth, cam.elevation = 3.0, 120.0, -10.0
  opt, pert = mujoco.MjvOption(), mujoco.MjvPerturb()
  n = max(len(ta), len(tb))
  frames = []
  ai, ab = g.mot_idx[ANCHOR], g.bid[ANCHOR]
  for k in range(n):
    t = min(f + max(k - 1, 0), mot.T - 1)  # same state/frame pairing as the metrics (state k vs frame f+k-1)
    halves = []
    for traj, lab in zip((ta, tb), labels):
      i = min(k, len(traj) - 1)
      d.qpos[:] = traj[i]
      mujoco.mj_forward(m, d)
      cam.lookat[:] = [d.xpos[g.bid["pelvis"], 0], d.xpos[g.bid["pelvis"], 1], 0.75]
      r.update_scene(d, cam, scene_option=opt)
      # translucent green ghost = reference frame t, re-anchored to the robot's CURRENT torso xy + yaw (reference
      # torso height kept; like mjlab body_pos_relative_w) so that it overlays the robot despite xy/yaw drift
      dq = yaw_quat(qmul(d.xquat[ab].copy(), qconj(mot.bq[t, ai])))
      dpos = d.xpos[ab].copy()
      dpos[2] = mot.bp[t, ai, 2]
      dg.qpos[:] = 0
      dg.qpos[g.rq:g.rq + 3] = dpos + qmat(dq) @ (mot.bp[t, 0] - mot.bp[t, ai])
      dg.qpos[g.rq + 3:g.rq + 7] = qmul(dq, mot.bq[t, 0])
      dg.qpos[g.qadr] = mot.jp[t]
      mujoco.mj_kinematics(m, dg)
      n0 = r.scene.ngeom
      mujoco.mjv_addGeoms(m, dg, opt, pert, mujoco.mjtCatBit.mjCAT_DYNAMIC, r.scene)
      for j in range(n0, r.scene.ngeom):
        r.scene.geoms[j].rgba[:] = (0.3, 0.85, 0.4, 0.3)
      img = r.render().copy()
      if cv2 is not None:
        txt = lab + ("  FELL" if i < k else "")
        cv2.putText(img, txt, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"t={k * 0.02:5.2f}s  ref frame {t} (ghost aligned xy+yaw)", (10, 470),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
      halves.append(img)
    frames.append(np.concatenate(halves, axis=1))
  r.close()
  out.parent.mkdir(parents=True, exist_ok=True)
  imageio.mimsave(out, frames, fps=50, macro_block_size=1)
  return str(out)


# ---------------------------------------------------------------------------------------------------- mjlab mode
def mjlab_mode(a):
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  from dataclasses import asdict

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  tag, name_cn = CLIPS[a.clip]
  pdir = ROOT / "policies" / tag
  info = json.loads((HERE / "models" / "dance_info.json").read_text())
  dev = "cuda:0" if torch.cuda.is_available() else "cpu"

  cfg = load_env_cfg(TASK, play=True)
  cfg.scene.num_envs = 1
  mc = cfg.commands["motion"]
  mc.motion_file = str(pdir / "reference_motion.npz")
  mc.pose_range, mc.velocity_range, mc.joint_position_range = {}, {}, (0.0, 0.0)
  removed_events = [k for k in ("base_com", "encoder_bias", "foot_friction", "push_robot")
                    if cfg.events.pop(k, None) is not None]
  removed_terms = [k for k in list(cfg.terminations) if k != "time_out"]
  for k in removed_terms:
    cfg.terminations.pop(k)
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent_cfg = load_rl_cfg(TASK)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(str(pdir / "policy.pt"), load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  cmd = env.command_manager.get_term("motion")
  robot = env.scene["robot"]
  start = [0]
  cmd.cfg.sampling_mode = "uniform"  # route the reset to our fixed start frame
  cmd._uniform_sampling = lambda env_ids: cmd.time_steps.__setitem__(env_ids, start[0])
  origin = env.scene.env_origins[0].double().cpu().numpy()

  m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
  g = NativeG1(m, info)
  pol = Policy(pdir / "policy.pt")
  mot = Motion(pdir / "reference_motion.npz")
  T, dt = mot.T, float(info["step_dt"])
  assert T == int(cmd.motion.time_step_total), (T, cmd.motion.time_step_total)
  npy = lambda x: torch.as_tensor(x).detach().double().cpu().numpy()

  # ---- model checks
  mrt = env.sim.mj_model
  fields = ("body_mass", "body_ipos", "body_inertia", "body_pos", "body_quat", "geom_friction", "geom_size",
            "geom_pos", "geom_solref", "geom_solimp", "geom_condim", "geom_contype", "geom_conaffinity", "dof_armature",
            "dof_damping", "dof_frictionloss", "jnt_range", "actuator_gainprm", "actuator_biasprm",
            "actuator_forcerange", "actuator_trnid")
  model_check = {"exported_vs_runtime_mj_model_max_abs": {}, "warp_model_vs_nominal_max_abs": {}}
  for f_ in fields:
    model_check["exported_vs_runtime_mj_model_max_abs"][f_] = float(
      np.abs(np.asarray(getattr(m, f_), float) - np.asarray(getattr(mrt, f_), float)).max())
  for f_ in ("geom_friction", "body_ipos", "body_mass", "dof_armature", "actuator_gainprm", "actuator_biasprm"):
    try:
      w = npy(getattr(env.sim.model, f_))
      w = w.reshape((-1,) + np.asarray(getattr(m, f_)).shape)[0]
      model_check["warp_model_vs_nominal_max_abs"][f_] = float(np.abs(w - np.asarray(getattr(m, f_), float)).max())
    except Exception as e:  # noqa: BLE001
      model_check["warp_model_vs_nominal_max_abs"][f_] = repr(e)[:120]
  model_check["opt"] = {k: [float(getattr(m.opt, k)), float(getattr(mrt.opt, k))] for k in
                        ("timestep", "iterations", "tolerance", "ls_iterations", "ls_tolerance", "impratio",
                         "integrator", "cone", "solver", "jacobian", "noslip_iterations")}
  model_check["env_origin"] = origin.tolist()
  print("[model]", json.dumps(model_check)[:1500], flush=True)

  tt = lambda x: torch.as_tensor(x, dtype=env.sim.data.qpos.dtype, device=env.sim.data.qpos.device)

  def mj_state():
    q, v = npy(env.sim.data.qpos[0]).copy(), npy(env.sim.data.qvel[0]).copy()
    q[:3] -= origin
    w = npy(env.sim.data.qacc_warmstart[0]).copy()
    return q, v, w

  de = mujoco.MjData(m)
  eq = {"obs_term_max_abs": {t: 0.0 for t in TERMS}, "obs_checks": 0, "action_impl_max_abs": 0.0,
        "ctrl_max_abs": 0.0, "init_qpos_max_abs": 0.0, "init_qvel_max_abs": 0.0,
        "time_step_mismatch": 0, "reset_warmstart_max_abs_before_zeroing": 0.0}
  dof_name = lambda i: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, int(m.dof_jntid[i])).replace("robot/", "")

  def check_obs(t, into):
    q, v, _ = mj_state()
    g.set_state(de, q, v)
    nat = g.obs_terms(de, mot, t, npy(env.action_manager.action[0]))
    ref = npy(env.obs_buf["actor"][0])
    i = 0
    for name, dim, x in zip(TERMS, DIMS, nat):
      into[name] = max(into.get(name, 0.0), float(np.abs(x - ref[i:i + dim]).max()))
      i += dim
    eq["obs_checks"] += 1

  def warp_contacts():
    d_ = env.sim.data
    nac = int(npy(d_.nacon).reshape(-1)[0])
    return Counter(tuple(sorted(int(x) for x in p)) for p in npy(d_.contact.geom)[:nac].astype(int))

  def native_contacts(dn):
    return Counter(tuple(sorted((int(c.geom1), int(c.geom2)))) for c in dn.contact[:dn.ncon])

  def reset_to(f):
    start[0] = f
    env.reset()
    # mujoco_warp reset_data zeroes qacc_warmstart; zero it again explicitly (and record what was there) so that
    # both sims start every rollout from the same warm start as native mj_resetData
    eq["reset_warmstart_max_abs_before_zeroing"] = max(eq["reset_warmstart_max_abs_before_zeroing"],
                                                       float(np.abs(npy(env.sim.data.qacc_warmstart[0])).max()))
    env.sim.data.qacc_warmstart[0] = tt(np.zeros(m.nv))
    o = venv.get_observations()
    if int(cmd.time_steps[0]) != f:
      raise RuntimeError(f"start frame not applied: {int(cmd.time_steps[0])} != {f}")
    return o

  def new_acc():
    return dict(sq=[], sv=[], dof=[], ceq=[], worst=None, obs={}, pushes=0, falls=0, starts=[])

  def compare_step(acc, f, k, pq, pv, pw, wset, a_np, q1, v1):
    """one policy step (4 substeps) natively from the identical pre-step state, action and warm start"""
    g.set_state(de, pq, pv, pw)
    same_contacts = native_contacts(de) == wset  # contact set at the identical pre-step state
    g.step(de, a_np)
    eq["ctrl_max_abs"] = max(eq["ctrl_max_abs"], float(np.abs(de.ctrl - npy(env.sim.data.ctrl[0])).max()))
    dv = np.abs(de.qvel - v1)
    acc["sq"].append(float(np.abs(de.qpos - q1).max()))
    acc["sv"].append(float(dv.max()))
    acc["dof"].append(dof_name(int(np.argmax(dv))))
    acc["ceq"].append(bool(same_contacts))
    if acc["worst"] is None or acc["sv"][-1] > acc["worst"]["qvel_max_abs"]:
      acc["worst"] = dict(start_frame=f, step=k, qvel_max_abs=acc["sv"][-1], qpos_max_abs=acc["sq"][-1],
                          worst_dof=acc["dof"][-1], contact_set_equal_at_pre_state=bool(same_contacts),
                          ncon_at_pre_state=int(sum(wset.values())))

  def summarize_steps(acc):
    sv, dofs, ceq = np.array(acc["sv"]), np.array(acc["dof"]), np.array(acc["ceq"])
    big = sv > 0.1
    return dict(steps=int(sv.size), starts=acc["starts"], pushes=acc["pushes"], runs_that_fell=acc["falls"],
                qpos_max_abs=stat(acc["sq"]), qvel_max_abs=stat(sv),
                contact_set_equal_frac=float(ceq.mean()),
                contact_set_equal_frac_on_steps_qvel_gt_0_1=float(ceq[big].mean()) if big.any() else None,
                worst_dof_on_steps_qvel_gt_0_1=Counter(dofs[big].tolist()).most_common(6),
                worst_dof_on_steps_qvel_gt_1e_3=Counter(dofs[sv > 1e-3].tolist()).most_common(6),
                worst_case=acc["worst"], obs_term_max_abs_at_perturbed_states=acc["obs"] or None)

  ONLINE = ("error_joint_pos", "error_anchor_rot", "error_body_pos", "error_anchor_pos")
  RECOMP = {"error_joint_pos": "joint_err_norm", "error_anchor_rot": "anchor_ori_rad",
            "error_body_pos": "body_pos_err", "error_anchor_pos": "anchor_pos_err"}
  metric_check = {k: dict(max_abs_diff_steps_ge_2=0.0, max_abs_diff_step_1=0.0) for k in ONLINE}
  rng = np.random.default_rng(SEED + (0 if a.clip == "sss" else 1))
  starts = [0] + sorted(int(x) for x in rng.choice(np.arange(1, T - 1 - 60), N_RANDOM, replace=False))
  runs, trajs, snaps = [], {}, []
  nominal = new_acc()
  for f in starts:
    obs = reset_to(f)
    nominal["starts"].append(f)
    q0, v0, _ = mj_state()
    nq0, nv0 = g.ref_state(mot, f)
    eq["init_qpos_max_abs"] = max(eq["init_qpos_max_abs"], float(np.abs(q0 - nq0).max()))
    eq["init_qvel_max_abs"] = max(eq["init_qvel_max_abs"], float(np.abs(v0 - nv0).max()))
    check_obs(f, eq["obs_term_max_abs"])
    nsteps = T - 1 - f
    traj_m = [q0]
    onl = {k: [] for k in ONLINE}
    tw = time.perf_counter()
    for k in range(nsteps):
      pq, pv, pw = mj_state()
      wset = warp_contacts()
      with torch.no_grad():
        act = policy(obs)
      a_np = npy(act[0])
      eq["action_impl_max_abs"] = max(eq["action_impl_max_abs"],
                                      float(np.abs(pol(npy(obs["actor"][0])) - a_np).max()))
      obs, _, _, _ = venv.step(act)
      for kk in ONLINE:  # mjlab's own MotionCommand metrics (updated inside this env.step)
        onl[kk].append(float(cmd.metrics[kk][0]))
      q1, v1, _ = mj_state()
      compare_step(nominal, f, k, pq, pv, pw, wset, a_np, q1, v1)
      if f == 0 and k % 8 == 0 and len(snaps) < 40:
        snaps.append((pq, pv, pw, a_np))
      t_now = int(cmd.time_steps[0])
      if t_now != f + k + 1:
        eq["time_step_mismatch"] += 1
      check_obs(t_now, eq["obs_term_max_abs"])
      traj_m.append(q1)
      g.set_state(de, q1, v1)
      if g.fell(de):
        break
    wall_m = time.perf_counter() - tw
    traj_m = np.array(traj_m)
    # re-run: the same mjlab rollout again (run-to-run reproducibility of mujoco_warp on the GPU)
    obs = reset_to(f)
    traj_r = [mj_state()[0]]
    for k in range(len(traj_m) - 1):
      with torch.no_grad():
        obs, _, _, _ = venv.step(policy(obs))
      traj_r.append(mj_state()[0])
    traj_r = np.array(traj_r)
    traj_n, wall_n = native_rollout(g, pol, mot, f, nsteps)
    rm, rows_m = run_metrics(g, mot, f, traj_m, dt, with_rows=True)
    rn = run_metrics(g, mot, f, traj_n, dt)
    # metric definition check: our recomputation from the recorded mjlab qpos vs mjlab's online metrics. Step 1 is
    # reported separately: after a reset mjlab's body_pos_relative_w still holds the previous episode's value.
    mc_run = {}
    for kk in ONLINE:
      on, rc = np.array(onl[kk]), np.array([r[RECOMP[kk]] for r in rows_m])
      metric_check[kk]["max_abs_diff_steps_ge_2"] = max(metric_check[kk]["max_abs_diff_steps_ge_2"],
                                                       float(np.abs(on[1:] - rc[1:]).max()))
      metric_check[kk]["max_abs_diff_step_1"] = max(metric_check[kk]["max_abs_diff_step_1"], float(abs(on[0] - rc[0])))
      mc_run[kk] = dict(mjlab_online_mean=round(float(on.mean()), 5), recomputed_mean=round(float(rc.mean()), 5),
                        mjlab_online_mean_steps_ge_2=round(float(on[1:].mean()), 5),
                        recomputed_mean_steps_ge_2=round(float(rc[1:].mean()), 5))
    run = dict(start_frame=f, start_s=round(f * dt, 2), steps_planned=nsteps, mjlab=rm, native=rn,
               divergence=divergence(g, traj_m, traj_n, dt),
               divergence_mjlab_rerun=divergence(g, traj_m, traj_r, dt), metric_check=mc_run,
               wall_s=dict(mjlab_incl_checks=round(wall_m, 2), native=round(wall_n, 3)))
    runs.append(run)
    trajs[f"mjlab_{f}"], trajs[f"native_{f}"] = traj_m, traj_n
    print(f"[run] start {f:4d} ({nsteps} steps) | mjlab fell {rm['fell']} rms {rm['joint_rms_rad']:.3f} "
          f"ori {rm['anchor_ori_err_deg']:.1f} spread {rm['spread_p90_ratio']:.2f} | native fell {rn['fell']} "
          f"rms {rn['joint_rms_rad']:.3f} ori {rn['anchor_ori_err_deg']:.1f} spread {rn['spread_p90_ratio']:.2f} | "
          f"div1s pelvis {run['divergence']['t1s']['pelvis_pos_diff_at_m']:.4f} m (mjlab rerun "
          f"{run['divergence_mjlab_rerun']['t1s']['pelvis_pos_diff_at_m']:.4f}) | native wall {wall_n:.2f}s",
          flush=True)

  # ---- off-nominal one-step equivalence: the same per-step comparison while the robot is driven off the nominal
  # path. push: every 20 steps a random root velocity kick + joint pos/vel perturbation is written into mjlab's
  # state (obs re-computed and checked at the perturbed state); noise: policy action + N(0, 0.3).
  prng = np.random.default_rng(SEED + 100 + (0 if a.clip == "sss" else 1))
  p_starts = [starts[0], starts[len(starts) // 2]]
  perturbed = {}
  for scen in ("push", "noise"):
    acc = new_acc()
    for f in p_starts:
      obs = reset_to(f)
      acc["starts"].append(f)
      for k in range(T - 1 - f):
        if scen == "push" and k > 0 and k % 20 == 0:
          q = env.sim.data.qpos[0].clone()
          v = env.sim.data.qvel[0].clone()
          v[g.rv:g.rv + 3] += tt(prng.uniform([-0.5, -0.5, -0.2], [0.5, 0.5, 0.2]))
          v[g.rv + 3:g.rv + 6] += tt(prng.uniform(-0.5, 0.5, 3))
          q[torch.as_tensor(g.qadr)] += tt(prng.uniform(-0.15, 0.15, 29))
          v[torch.as_tensor(g.dadr)] += tt(prng.uniform(-1.0, 1.0, 29))
          env.sim.data.qpos[0] = q
          env.sim.data.qvel[0] = v
          env.sim.forward()
          env.sim.sense()
          env.obs_buf = env.observation_manager.compute(update_history=True)  # actor group has no history terms
          obs = venv.get_observations()
          check_obs(int(cmd.time_steps[0]), acc["obs"])
          acc["pushes"] += 1
        pq, pv, pw = mj_state()
        wset = warp_contacts()
        with torch.no_grad():
          act = policy(obs)
        if scen == "noise":
          act = act + torch.as_tensor(prng.normal(0.0, 0.3, tuple(act.shape)), dtype=act.dtype, device=act.device)
        a_np = npy(act[0])
        obs, _, _, _ = venv.step(act)
        q1, v1, _ = mj_state()
        compare_step(acc, f, k, pq, pv, pw, wset, a_np, q1, v1)
        g.set_state(de, q1, v1)
        if g.fell(de):
          acc["falls"] += 1
          break
    perturbed[scen] = summarize_steps(acc)
    print(f"[perturbed:{scen}]", json.dumps(perturbed[scen]), flush=True)

  # ---- single substep: 1 x mjwarp.step vs 1 x mj_step from identical state / ctrl / warm start
  sub_q, sub_v = [], []
  for pq, pv, pw, a_np in snaps:
    qw = pq.copy()
    qw[:3] += origin
    env.sim.data.qpos[0] = tt(qw)
    env.sim.data.qvel[0] = tt(pv)
    env.sim.data.qacc_warmstart[0] = tt(pw)
    ctrl = np.zeros(m.nu)
    ctrl[g.act] = g.targets(a_np)
    env.sim.data.ctrl[0] = tt(ctrl)
    env.sim.step()
    q1, v1, _ = mj_state()
    g.set_state(de, pq, pv, pw)
    de.ctrl[:] = ctrl
    mujoco.mj_step(m, de)
    sub_q.append(float(np.abs(de.qpos - q1).max()))
    sub_v.append(float(np.abs(de.qvel - v1).max()))

  equivalence = dict(
    steps_checked=eq["obs_checks"], obs_term_max_abs=eq["obs_term_max_abs"],
    obs_all_terms_max_abs=max(eq["obs_term_max_abs"].values()),
    policy_impl_action_max_abs=eq["action_impl_max_abs"], ctrl_targets_max_abs=eq["ctrl_max_abs"],
    reset_state_npz_vs_mjlab=dict(qpos_max_abs=eq["init_qpos_max_abs"], qvel_max_abs=eq["init_qvel_max_abs"]),
    reset_warmstart_max_abs_before_zeroing=eq["reset_warmstart_max_abs_before_zeroing"],
    motion_time_step_mismatches=eq["time_step_mismatch"],
    one_policy_step_4_substeps=summarize_steps(nominal),
    one_policy_step_4_substeps_perturbed=perturbed,
    one_substep=dict(qpos_max_abs=stat(sub_q), qvel_max_abs=stat(sub_v)) if sub_q else None,
    metric_definition_check=dict(
      note="our run_metrics recomputation (state k vs frame f+k-1) from the recorded mjlab qpos vs mjlab "
           "MotionCommand.metrics read after every env.step; step 1 separate (stale body_pos_relative_w after reset)",
      max_abs_diff=metric_check))
  print("[equivalence]", json.dumps(equivalence), flush=True)

  video = None
  if not a.no_video:
    video = render_side_by_side(g, mot, 0, trajs["mjlab_0"], trajs["native_0"],
                                ("mjlab (mujoco_warp 3.5, GPU)", "native MuJoCo 3.5 (CPU)"),
                                VID_DIR / f"{a.clip}_side_by_side.mp4")
  res = dict(clip=a.clip, name=name_cn, policy=str(pdir / "policy.pt"), motion=mot.path, motion_fps=mot.fps,
             frames=T, step_dt=dt, decimation=g.decim, mujoco_native=mujoco.__version__, device_mjlab=dev,
             randomisation=dict(removed_events=removed_events, removed_terminations=removed_terms,
                                rsi_pose_velocity_joint_ranges="all zero", obs_corruption="off (play cfg)"),
             fall_rule=f"torso_link z < {FALL_Z} m or torso z-axis . world z < {FALL_UP} (same code for both sims)",
             starts=starts, model_check=model_check, equivalence=equivalence, runs=runs,
             summary=dict(mjlab=summarize(runs, "mjlab"), native=summarize(runs, "native"),
                          start0=dict(mjlab=runs[0]["mjlab"], native=runs[0]["native"],
                                      divergence=runs[0]["divergence"],
                                      divergence_mjlab_rerun=runs[0]["divergence_mjlab_rerun"]),
                          divergence_mean={
                            name: {f"{w}_{q}": round(float(np.mean([r[key][w][q] for r in runs])), 5)
                                   for w, q in (("t1s", "pelvis_pos_diff_at_m"), ("t1s", "joint_max_abs_upto_rad"),
                                                ("t1s", "anchor_ori_diff_at_deg"), ("end", "pelvis_pos_diff_at_m"))}
                            for name, key in (("mjlab_vs_native", "divergence"),
                                              ("mjlab_vs_mjlab_rerun", "divergence_mjlab_rerun"))},
                          bitwise_identical_first_1s_starts={
                            name: int(sum(r[key]["t1s"]["bitwise_identical_upto"] for r in runs))
                            for name, key in (("mjlab_vs_native", "divergence"),
                                              ("mjlab_vs_mjlab_rerun", "divergence_mjlab_rerun"))},
                          divergence_t1s_max={
                            name: dict(pelvis_m=round(max(r[key]["t1s"]["pelvis_pos_diff_at_m"] for r in runs), 5),
                                       joint_rad=round(max(r[key]["t1s"]["joint_max_abs_upto_rad"] for r in runs), 5))
                            for name, key in (("mjlab_vs_native", "divergence"),
                                              ("mjlab_vs_mjlab_rerun", "divergence_mjlab_rerun"))},
                          native_realtime_factor=round(sum(r["native"]["steps"] for r in runs) * dt /
                                                       sum(r["wall_s"]["native"] for r in runs), 1)),
             video=video)
  (HERE / f"results_dance_{a.clip}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
  np.savez_compressed(HERE / f"traj_dance_{a.clip}.npz", starts=np.array(starts), **trajs)
  print("[done]", a.clip, json.dumps(res["summary"], ensure_ascii=False), flush=True)


# --------------------------------------------------------------------------------------------------- native mode
def load_xml_model(xml_path, assets_dir):
  xml = Path(xml_path).read_text()
  # MjSpec.to_xml() (3.5.0) writes an empty nested <default/> that the XML parser rejects ("empty class name");
  # it carries no attributes, so dropping it does not change the model.
  xml = re.sub(r"<default\s*/>", "", xml)
  assets = {}
  for fn in set(re.findall(r'file="([^"]+)"', xml)):
    p = Path(assets_dir) / Path(fn).name
    assets[fn] = p.read_bytes()
  m = mujoco.MjModel.from_xml_string(xml, assets)
  for k, v in OPT.items():
    setattr(m.opt, k, v)
  m.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
  m.opt.cone = mujoco.mjtCone.mjCONE_PYRAMIDAL
  m.opt.solver = mujoco.mjtSolver.mjSOL_NEWTON
  m.opt.jacobian = mujoco.mjtJacobian.mjJAC_AUTO
  return m


def native_mode(a):
  tag, name_cn = CLIPS[a.clip]
  pdir = ROOT / "policies" / tag
  info = json.loads((HERE / "models" / "dance_info.json").read_text())
  xml = Path(a.xml) if Path(a.xml).is_absolute() else HERE / a.xml
  m = load_xml_model(xml, a.assets)
  g = NativeG1(m, info)
  pol = Policy(pdir / "policy.pt")
  mot = Motion(pdir / "reference_motion.npz")
  dt = float(info["step_dt"])
  ref = np.load(HERE / f"traj_dance_{a.clip}.npz")
  out = dict(clip=a.clip, mujoco=mujoco.__version__, model=str(xml), runs=[])
  # model sanity vs exported 3.5 numbers in the info json
  out["model_check_vs_info"] = dict(
    nq=[m.nq, info["nq"]], nv=[m.nv, info["nv"]], nu=[m.nu, info["nu"]],
    gain_max_abs=float(np.abs(m.actuator_gainprm[:, 0] - np.array(info["actuator_gainprm0"])).max()),
    armature_max_abs=float(np.abs(m.dof_armature - np.array(info["dof_armature"])).max()))
  # field-by-field comparison with the exported .mjb (loaded directly when the version matches, otherwise via the
  # field dump written by the same-version run)
  fields = ("body_mass", "body_ipos", "body_iquat", "body_inertia", "body_pos", "body_quat", "geom_friction",
            "geom_size", "geom_pos", "geom_quat", "geom_solref", "geom_solimp", "geom_margin", "geom_gap",
            "geom_condim", "geom_priority", "geom_contype", "geom_conaffinity", "dof_armature", "dof_damping",
            "jnt_range", "actuator_gainprm", "actuator_biasprm", "actuator_forcerange", "actuator_trnid", "qpos0")
  dump = HERE / "models" / "dance_fields.npz"
  try:
    mb = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
    ref_fields = {f_: np.asarray(getattr(mb, f_), float) for f_ in fields}
    np.savez(dump, **ref_fields)
    src = "dance.mjb (same MuJoCo version)"
  except Exception:  # noqa: BLE001  (mjb is version specific)
    ref_fields = dict(np.load(dump)) if dump.exists() else {}
    src = "dance_fields.npz (dumped from dance.mjb by the 3.5.0 run)"
  out["model_check_vs_mjb"] = dict(source=src, max_abs={
    f_: (float(np.abs(np.asarray(getattr(m, f_), float) - ref_fields[f_]).max())
         if f_ in ref_fields and ref_fields[f_].shape == np.asarray(getattr(m, f_)).shape else "shape/missing")
    for f_ in fields})
  print(f"[{a.tag}] model vs mjb:", json.dumps(out["model_check_vs_mjb"]), flush=True)
  for f in [int(x) for x in ref["starts"]]:
    traj, wall = native_rollout(g, pol, mot, f, mot.T - 1 - f)
    r = dict(start_frame=f, metrics=run_metrics(g, mot, f, traj, dt), wall_s=round(wall, 3),
             divergence_vs_native350=divergence(g, ref[f"native_{f}"], traj, dt),
             divergence_vs_mjlab=divergence(g, ref[f"mjlab_{f}"], traj, dt))
    out["runs"].append(r)
    mm = r["metrics"]
    print(f"[{a.tag}] start {f:4d} fell {mm['fell']} rms {mm['joint_rms_rad']:.3f} ori {mm['anchor_ori_err_deg']:.1f} "
          f"spread {mm['spread_p90_ratio']:.2f} | 1s pelvis diff vs native3.5 "
          f"{r['divergence_vs_native350']['t1s']['pelvis_pos_diff_at_m']:.4f} m", flush=True)
  out["summary"] = summarize([{"x": r["metrics"]} for r in out["runs"]], "x")
  (HERE / f"results_dance_{a.clip}_{a.tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
  print("[done]", a.tag, json.dumps(out["summary"]), flush=True)


# --------------------------------------------------------------------------------------------------- report mode
def report_mode(a):
  allres = {}
  for clip in CLIPS:
    p = HERE / f"results_dance_{clip}.json"
    if not p.exists():
      continue
    r = json.loads(p.read_text())
    r["cross_checks"] = {}
    for q in sorted(HERE.glob(f"results_dance_{clip}_*.json")):
      r["cross_checks"][q.stem.split(f"{clip}_", 1)[1]] = json.loads(q.read_text())
    allres[clip] = r
  (HERE / "results_dance.json").write_text(json.dumps(allres, indent=1, ensure_ascii=False))

  L = ["# Dance specialist sim2sim: mjlab (mujoco_warp) vs native MuJoCo", "",
       "Generated by `sim2sim/native_dance.py --mode report` from the per-clip JSONs. All numbers are measured.", ""]
  for clip, r in allres.items():
    e = r["equivalence"]
    L += [f"## {r['name']} ({clip}, {Path(r['policy']).parent.name}) - {r['frames']} frames @ {r['motion_fps']} fps", "",
          f"Randomisation off: removed events {r['randomisation']['removed_events']}, removed terminations "
          f"{r['randomisation']['removed_terminations']}; RSI ranges zero. Fall rule: {r['fall_rule']}.", "",
          f"### Equivalence (state copied mjlab -> native at every step, {e['steps_checked']} steps)", "",
          "| term | max abs diff |", "|---|---|"]
    L += [f"| {k} | {v:.2e} |" for k, v in e["obs_term_max_abs"].items()]
    s4, s1 = e["one_policy_step_4_substeps"], e["one_substep"]
    L += ["", f"- policy re-implementation (same obs): max |action diff| {e['policy_impl_action_max_abs']:.2e}",
          f"- ctrl targets: max abs diff {e['ctrl_targets_max_abs']:.2e}",
          f"- reset state (npz rebuild vs mjlab): qpos {e['reset_state_npz_vs_mjlab']['qpos_max_abs']:.2e}, "
          f"qvel {e['reset_state_npz_vs_mjlab']['qvel_max_abs']:.2e}; mjlab qacc_warmstart right after reset (before "
          f"it is zeroed explicitly for both sims): max abs {e['reset_warmstart_max_abs_before_zeroing']:.2e}"]
    L += ["", "One policy step (4 substeps) from the identical pre-step state, action and qacc_warmstart; max over "
          "DOFs of |native - mjlab|; contact set = geom-pair multiset of mujoco_warp vs mj_forward at that identical "
          "pre-step state:", "",
          "| scenario | steps | qvel median | qvel p99 | qvel max | frac qvel>0.1 | frac qvel>1 | qpos max | "
          "contact set equal | contact set equal on qvel>0.1 steps | DOF with the largest diff on qvel>0.1 steps |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    scen_rows = [("nominal rollouts (9 starts)", s4)] + [
      (f"{k} (starts {v['starts']}" + (f", {v['pushes']} pushes" if v["pushes"] else "") +
       f", {v['runs_that_fell']} fell)", v) for k, v in e["one_policy_step_4_substeps_perturbed"].items()]
    for lab, s in scen_rows:
      qv, qp = s["qvel_max_abs"], s["qpos_max_abs"]
      ce = s["contact_set_equal_frac_on_steps_qvel_gt_0_1"]
      dofs = ", ".join(f"{n} {c}" for n, c in s["worst_dof_on_steps_qvel_gt_0_1"]) or "-"
      L.append(f"| {lab} | {s['steps']} | {qv['median']:.1e} | {qv['p99']:.1e} | {qv['max']:.2f} | "
               f"{qv['frac_gt_1e_1']:.2%} | {qv['frac_gt_1']:.2%} | {qp['max']:.1e} | {s['contact_set_equal_frac']:.1%} | "
               f"{'-' if ce is None else f'{ce:.1%}'} | {dofs} |")
    cnt = []
    for lab, s in scen_rows:
      nb = int(round(s["qvel_max_abs"]["frac_gt_1e_1"] * s["steps"]))
      ce = s["contact_set_equal_frac_on_steps_qvel_gt_0_1"]
      ne = int(round((ce or 0.0) * nb))
      nd_ = int(round((1 - s["contact_set_equal_frac"]) * s["steps"]))
      cnt.append(f"{lab.split(' (')[0]}: {nb} steps with qvel diff > 0.1, {ne} of them with identical contact sets; "
                 f"{nd_}/{s['steps']} steps with any contact-set difference")
    L += ["", "- counts: " + "; ".join(cnt)]
    po = {k: v["obs_term_max_abs_at_perturbed_states"] for k, v in e["one_policy_step_4_substeps_perturbed"].items()
          if v["obs_term_max_abs_at_perturbed_states"]}
    if po:
      L += ["", "- obs at the directly perturbed (pushed) states, max abs diff over all terms: " +
            ", ".join(f"{k} {max(v.values()):.2e}" for k, v in po.items())]
    mdc = e["metric_definition_check"]["max_abs_diff"]
    L += [f"- metric definition check (recomputed from recorded mjlab qpos vs mjlab's own online MotionCommand "
          f"metrics, steps >= 2, max abs diff): " +
          ", ".join(f"{k} {v['max_abs_diff_steps_ge_2']:.1e}" for k, v in mdc.items()) +
          "; step 1 (mjlab body_pos_relative_w still from the previous episode): error_body_pos "
          f"{mdc['error_body_pos']['max_abs_diff_step_1']:.2f}"]
    if s1:
      L += [f"- one substep: qpos median {s1['qpos_max_abs']['median']:.2e} / max {s1['qpos_max_abs']['max']:.2e}; "
            f"qvel median {s1['qvel_max_abs']['median']:.2e} / max {s1['qvel_max_abs']['max']:.2e}"]
    mc = r["model_check"]
    L += [f"- exported .mjb vs runtime mj_model: max abs diff over {len(mc['exported_vs_runtime_mj_model_max_abs'])} "
          f"fields = {max(mc['exported_vs_runtime_mj_model_max_abs'].values()):.1e}; warp model vs nominal (no DR): "
          f"{max(v for v in mc['warp_model_vs_nominal_max_abs'].values() if isinstance(v, float)):.1e} (float32)",
          f"- native closed loop speed (obs + torch CPU policy + 4 mj_step): "
          f"{r['summary']['native_realtime_factor']}x real time (single thread)"]
    L += ["", "### Closed loop (same initial states)", "",
          "Divergence columns: native row = mjlab vs native; mjlab row = mjlab vs an identical mjlab re-run "
          "(run-to-run reproducibility of mujoco_warp; 0.0000 with 'bitwise' = identical trajectories).", "",
          "| start (s) | sim | fell | joint RMS (rad) | joint err norm (rad) | anchor ori err (deg) | body pos err (m) | "
          "spread p90 ratio | track-lost frac | 1 s pelvis diff (m) | 1 s max joint diff (rad) | end pelvis diff (m) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in r["runs"]:
      for sim in ("mjlab", "native"):
        x = run[sim]
        fell = f"yes @{x['fell_at_s']}s" if x["fell"] else "no"
        # mjlab row: divergence of an identical mjlab re-run; native row: mjlab vs native
        dd = run["divergence_mjlab_rerun"] if sim == "mjlab" else run["divergence"]
        bw = " (bitwise)" if dd["t1s"].get("bitwise_identical_upto") else ""
        tail = (f"{dd['t1s']['pelvis_pos_diff_at_m']:.4f}{bw} | {dd['t1s']['joint_max_abs_upto_rad']:.4f} | "
                f"{dd['end']['pelvis_pos_diff_at_m']:.4f}")
        L.append(f"| {run['start_s']} | {sim} | {fell} | {x['joint_rms_rad']:.4f} | {x['joint_err_norm_rad']:.4f} | "
                 f"{x['anchor_ori_err_deg']:.2f} | {x['body_pos_err_m']:.4f} | {x['spread_p90_ratio']:.1%} | "
                 f"{x['track_lost_frac']:.2f} | {tail} |")
    sm = r["summary"]
    L += ["", "| summary (all starts) | runs | falls | joint RMS | joint err norm | anchor ori deg | body pos m | "
          "spread p90 ratio | track-lost frac |", "|---|---|---|---|---|---|---|---|---|"]
    for sim in ("mjlab", "native"):
      x = sm[sim]
      L.append(f"| {sim} | {x['runs']} | {x['falls']} | {x['joint_rms_rad']:.4f} | {x['joint_err_norm_rad']:.4f} | "
               f"{x['anchor_ori_err_deg']:.2f} | {x['body_pos_err_m']:.4f} | {x['spread_p90_ratio']:.1%} | "
               f"{x['track_lost_frac']:.3f} |")
    cross = []
    for tag, c in r["cross_checks"].items():
      x = c["summary"]
      L.append(f"| native {tag} (MuJoCo {c['mujoco']}, xml) | {x['runs']} | {x['falls']} | {x['joint_rms_rad']:.4f} | "
               f"{x.get('joint_err_norm_rad', float('nan')):.4f} | {x['anchor_ori_err_deg']:.2f} | "
               f"{x['body_pos_err_m']:.4f} | {x['spread_p90_ratio']:.1%} | {x['track_lost_frac']:.3f} |")
      mm = lambda key, w, q: np.mean([run_[key][w][q] for run_ in c["runs"]])
      mx = max(v for v in c["model_check_vs_mjb"]["max_abs"].values() if isinstance(v, float))
      cross.append(f"- {tag} (MuJoCo {c['mujoco']}, scene XML + meshes + runtime solver options): model fields vs "
                   f".mjb max abs {mx:.1e}; mean divergence vs native 3.5 .mjb run: 1 s pelvis "
                   f"{mm('divergence_vs_native350', 't1s', 'pelvis_pos_diff_at_m'):.5f} m / max joint "
                   f"{mm('divergence_vs_native350', 't1s', 'joint_max_abs_upto_rad'):.4f} rad, end pelvis "
                   f"{mm('divergence_vs_native350', 'end', 'pelvis_pos_diff_at_m'):.4f} m; vs mjlab: 1 s pelvis "
                   f"{mm('divergence_vs_mjlab', 't1s', 'pelvis_pos_diff_at_m'):.5f} m, end pelvis "
                   f"{mm('divergence_vs_mjlab', 'end', 'pelvis_pos_diff_at_m'):.4f} m")
    dm, bi, dx = sm["divergence_mean"], sm["bitwise_identical_first_1s_starts"], sm["divergence_t1s_max"]
    nr = len(r["runs"])
    L += ["", f"Mean divergence over the {nr} starts: mjlab vs native " + json.dumps(dm["mjlab_vs_native"]) +
          "; mjlab vs mjlab re-run " + json.dumps(dm["mjlab_vs_mjlab_rerun"]),
          f"- first 1 s bitwise identical: mjlab re-run {bi['mjlab_vs_mjlab_rerun']}/{nr} starts, native "
          f"{bi['mjlab_vs_native']}/{nr}; max over starts at 1 s: mjlab vs native pelvis "
          f"{dx['mjlab_vs_native']['pelvis_m']:.4f} m / joint {dx['mjlab_vs_native']['joint_rad']:.4f} rad, mjlab "
          f"re-run {dx['mjlab_vs_mjlab_rerun']['pelvis_m']:.4f} m / {dx['mjlab_vs_mjlab_rerun']['joint_rad']:.4f} rad"]
    if cross:
      L += ["", "Cross checks (native only):"] + cross
    if r.get("video"):
      L += ["", f"Video: `{r['video']}` (left = recorded mjlab qpos, right = native rollout, both drawn by the native "
                "renderer; green ghost = reference frame start+k-1 re-anchored to the robot's current torso xy + yaw)"]
    L.append("")
  L += ["## Notes / assumptions", "",
        "- Native side uses no mjlab code: observation, reference-frame lookup, JointPositionAction, reset state and "
        "the rsl_rl actor (EmpiricalNormalization eps 1e-2 + ELU MLP, deterministic mean) are re-implemented.",
        "- Motion clock: npz fps = 50 = 1 / step_dt, one reference frame per policy step; obs at step k uses frame "
        "start+k; runs stop at frame T-1 because mjlab re-samples (teleports) when the time step reaches T.",
        "- motion_anchor_ori_b = first two columns of R_torso_robot^T R_torso_ref, row-major (anchor = torso_link, "
        "no yaw/position alignment enters the actor obs); base_ang_vel = imu gyro sensor after mj_forward.",
        "- Metrics are computed by the same native kinematics code from the recorded qpos of both sims, with mjlab's "
        "pairing: the state after policy step k is compared with reference frame start+k-1 (CommandManager.compute() "
        "runs MotionCommand._update_metrics() before _update_command() advances time_steps; the training rewards and "
        "terminations also run before it in ManagerBasedRlEnv.step). Joint err norm = mjlab error_joint_pos (L2 over "
        "29 joints); joint RMS = that / sqrt(29); anchor ori err = mjlab error_anchor_rot (global torso orientation "
        "incl. yaw drift); body pos err = mjlab error_body_pos (14 bodies vs body_pos_relative_w, i.e. reference frame "
        "start+k-1 moved to the PREVIOUS state's torso xy + yaw, reference torso height kept). For step 1 we use the "
        "reset state's torso; mjlab still holds the previous episode's body_pos_relative_w there (not reproducible, "
        "excluded from the online-metric check). All values are means over the run (steps 1..N).",
        "- spread = |lateral left-right ankle distance| in the pelvis heading frame, p90 robot / p90 reference.",
        "- track-lost = any of the three training terminations in the policies' env.yaml, evaluated per step and only "
        "reported (they are removed from the env): anchor_pos (|torso z err| > 0.25 m), anchor_ori (|projected gravity "
        "z diff| > 0.8), ee_body_pos (|z err| > 0.25 m for left/right ankle_roll_link or wrist_yaw_link vs "
        "body_pos_relative_w). Evaluated on fresh kinematics; mjlab's own terminations read kinematics that are one "
        "physics substep stale (ManagerBasedRlEnv.step docstring), so a step right at a threshold could differ.",
        "- Warm start: mjlab's qacc_warmstart is set to zero after every reset (the value found there is listed "
        "above), so both sims start each rollout from the same state and the same (zero) warm start.",
        "- The videos render both trajectories with the same native renderer (left = recorded mjlab qpos). The ghost is "
        "re-anchored to the robot so tracking quality can be judged visually; world-frame xy/yaw drift is not shown.",
        "- Divergence: mujoco_warp (float32, GPU) and MuJoCo C (float64) produce different next states from identical "
        "pre-step state, ctrl and warm start (table above). Most steps agree to ~1e-5 rad/s, but a small fraction "
        "differ by > 0.1 rad/s (up to several rad/s), more often off-nominal (pushes / action noise) than on the "
        "nominal path, mostly at an ankle pitch/roll or waist DOF. The contact geom-pair sets at the identical "
        "pre-step states were equal on most of those large-difference steps (counts above), so for those steps the "
        "difference arises in the constraint solve / integration, not in collision detection; a few large steps "
        "coincide with a contact-set difference. We did not isolate whether the solve difference comes from float32 "
        "rounding or from differences between the warp and C solver implementations. These per-step differences, "
        "not run-to-run GPU non-determinism, cause the closed-loop divergence: the mjlab re-run columns (run-to-run "
        "reproducibility of mujoco_warp) are bitwise identical over the first 1 s in most starts and much smaller "
        "than mjlab vs native.",
        ""]
  (HERE / "results_dance.md").write_text("\n".join(L), encoding="utf-8")
  print("\n".join(L))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--mode", choices=("mjlab", "native", "report"), required=True)
  ap.add_argument("--clip", choices=tuple(CLIPS), default="sss")
  ap.add_argument("--xml", default="models/dance.xml")
  ap.add_argument("--assets", default=str(G1_ASSETS))
  ap.add_argument("--tag", default="mj316")
  ap.add_argument("--no_video", action="store_true")
  a = ap.parse_args()
  torch.set_num_threads(1)
  {"mjlab": mjlab_mode, "native": native_mode, "report": report_mode}[a.mode](a)
