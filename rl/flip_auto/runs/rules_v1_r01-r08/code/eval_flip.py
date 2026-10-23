"""Backflip probe evaluation of a tracking checkpoint: play the clip once from frame 0 with ALL terminations off,
then measure what the robot actually did vs the reference: cumulative torso pitch rotation (unwrapped), peak pelvis
height, airborne time (every body > 5 cm above the floor, pelvis > 0.45 m), landed upright (torso tilt < 30 deg and pelvis > 0.5 m at
the end, held for the last 0.5 s). Video side by side with the reference ghost (play config render).
Usage (unitree_rl_mjlab env, MUJOCO_GL=egl): python eval_flip.py --ckpt <model.pt> --motion <clip.npz> [--tag name]
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"


def cum_pitch(quats_wxyz):
  """Unwrapped rotation (deg) about the dominant axis of the per-step rotations."""
  import numpy as np
  from scipy.spatial.transform import Rotation as R
  r = R.from_quat(np.asarray(quats_wxyz)[:, [1, 2, 3, 0]])
  inc = (r[:-1].inv() * r[1:]).as_rotvec()
  ax = inc.sum(0)
  ax = ax / (np.linalg.norm(ax) + 1e-9)
  return np.degrees(np.concatenate([[0.0], np.cumsum(inc @ ax)]))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  # no steps past the clip: at the clip end the env times out and resets (teleport), which looked like "landed"
  ap.add_argument("--extra_steps", type=int, default=0)
  ap.add_argument("--tag", default="")
  ap.add_argument("--effort-scale", type=float, default=1.0, help="must match the training run's --effort-scale")
  ap.add_argument("--knee-limit", type=float, default=None, help="must match the training run's --knee-limit")
  ap.add_argument("--labels", default=None, help="labels_50fps.npz: report whether the torso fell before take-off")
  ap.add_argument("--size", type=int, nargs=2, default=None, metavar=("W", "H"),
                  help="render size (default = the play cfg's 320x240, too small to judge the legs)")
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  import imageio.v2 as imageio
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  env_cfg = load_env_cfg(a.task, play=True)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = 1
  env_cfg.commands["motion"].motion_file = str(Path(a.motion).resolve())
  env_cfg.terminations = {}
  if a.size:
    env_cfg.viewer.width, env_cfg.viewer.height = a.size
  if a.knee_limit is not None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from flip_rewards import set_knee_limit
    set_knee_limit(env_cfg.scene.entities["robot"].articulation, a.knee_limit)
  if a.effort_scale != 1.0:
    import dataclasses
    art = env_cfg.scene.entities["robot"].articulation
    art.actuators = tuple(dataclasses.replace(c, effort_limit=c.effort_limit * a.effort_scale) for c in art.actuators)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0", render_mode="rgb_array")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location="cuda:0")
  policy = runner.get_inference_policy(device="cuda:0")
  cmd = env.command_manager.get_term("motion")
  robot = env.scene["robot"]
  T = int(cmd.motion.time_step_total)
  env.reset()
  obs = venv.get_observations()
  ank = [list(robot.body_names).index(n) for n in ("left_ankle_roll_link", "right_ankle_roll_link")]
  frames, rq, aq, rz, az, ankz = [], [], [], [], [], []
  legs = ("hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll")
  jn = list(robot.joint_names)
  li = [jn.index(f"left_{j}_joint") for j in legs]
  ri = [jn.index(f"right_{j}_joint") for j in legs]
  mirror = np.array([1, -1, -1, 1, 1, -1], float)
  leg_asym, leg_err, feet_d, steps_q, steps_qr, knee_sep = [], [], [], [], [], []
  knees = [list(robot.body_names).index(n) for n in ("left_knee_link", "right_knee_link")]
  trk_body, trk_joint = [], []  # fidelity to the green reference (mjlab tracking metrics)
  # quiet standing after landing: arm joint speed, action change, pelvis horizontal speed, torso angular speed
  arm_ids = [i for i, n in enumerate(jn) if any(s in n for s in ("shoulder", "elbow", "wrist"))]
  arm_v, act_d, pel_v, tor_w = [], [], [], []
  prev_act = None
  # full per-step record for the automatic critic (rl/flip_auto/critic.py): every joint and tracked body
  rec = {k: [] for k in ("q", "qr", "dq", "dqr", "bp", "bpr", "bq", "bqr", "act", "foot_z")}
  for t in range(T - 2 + a.extra_steps):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    frames.append(env.render())
    rq.append(cmd.robot_anchor_quat_w[0].cpu().numpy())
    aq.append(cmd.anchor_quat_w[0].cpu().numpy())
    rz.append(float(robot.data.root_link_pos_w[0, 2]))
    az.append(float(cmd.body_pos_w[0, 0, 2]))
    # airborne = every body > 5 cm above the floor and pelvis > 0.45 m (= flip_rewards._airborne; "both ankles up"
    # also counted lying on the back with the legs raised)
    rec["q"].append(robot.data.joint_pos[0].cpu().numpy())
    rec["qr"].append(cmd.joint_pos[0].cpu().numpy())
    rec["dq"].append(robot.data.joint_vel[0].cpu().numpy())
    rec["dqr"].append(cmd.joint_vel[0].cpu().numpy())
    rec["bp"].append(cmd.robot_body_pos_w[0].cpu().numpy())
    rec["bpr"].append(cmd.body_pos_relative_w[0].cpu().numpy())
    rec["bq"].append(cmd.robot_body_quat_w[0].cpu().numpy())
    rec["bqr"].append(cmd.body_quat_relative_w[0].cpu().numpy())
    rec["act"].append(env.action_manager.action[0].cpu().numpy())
    rec["foot_z"].append((robot.data.body_link_pos_w[0, ank, 2] - env.scene.env_origins[0, 2]).cpu().numpy())
    act = env.action_manager.action[0].cpu().numpy()
    act_d.append(float(np.abs(act - prev_act).mean()) if prev_act is not None else 0.0)
    prev_act = act
    arm_v.append(float(np.sqrt((robot.data.joint_vel[0, arm_ids].cpu().numpy() ** 2).mean())))
    pel_v.append(float(robot.data.root_link_lin_vel_w[0, :2].norm()))
    tor_w.append(float(cmd.robot_anchor_ang_vel_w[0].norm()))
    trk_body.append(float(cmd.metrics["error_body_pos"][0]))
    trk_joint.append(float(cmd.metrics["error_joint_pos"][0]))
    qj = robot.data.joint_pos[0].cpu().numpy()
    qrj = cmd.joint_pos[0].cpu().numpy()
    steps_q.append(qj)
    steps_qr.append(qrj)
    leg_asym.append(float(np.abs(qj[ri] - mirror * qj[li]).mean()))
    leg_err.append(float(np.abs(qj[li + ri] - qrj[li + ri]).mean()))
    pa = robot.data.body_link_pos_w[0, ank, :2].cpu().numpy()
    feet_d.append(float(np.linalg.norm(pa[0] - pa[1])))
    # crossed legs: knee lateral separation in the pelvis frame (left knee should stay on the +y side)
    pq = robot.data.root_link_quat_w[0].cpu().numpy()
    pp = robot.data.root_link_pos_w[0].cpu().numpy()
    kp = robot.data.body_link_pos_w[0, knees].cpu().numpy() - pp
    w_, x_, y_, z_ = pq
    yax = np.array([2 * (x_ * y_ - w_ * z_), 1 - 2 * (x_ * x_ + z_ * z_), 2 * (y_ * z_ + w_ * x_)])
    knee_sep.append(float((kp[0] - kp[1]) @ yax))
    zb = robot.data.body_link_pos_w[0, :, 2] - env.scene.env_origins[0, 2]
    ankz.append(float(zb.min() > 0.05 and rz[-1] - float(env.scene.env_origins[0, 2]) > 0.45))
  dt = env.step_dt
  rot_r, rot_a = cum_pitch(rq), cum_pitch(aq[:T])
  ref_rot = np.concatenate([rot_a, np.full(max(len(rot_r) - len(rot_a), 0), rot_a[-1])])[:len(rot_r)]
  air = np.array(ankz) > 0.5
  air[:15] = False  # the reset places the robot slightly above the floor: the first drop is not a jump
  # longest airborne run
  best, cur = 0, 0
  for x in air:
    cur = cur + 1 if x else 0
    best = max(best, cur)
  up = np.array([1 - 2 * (q[1] ** 2 + q[2] ** 2) for q in rq])  # torso z-axis . world z
  tilt = np.degrees(np.arccos(np.clip(up, -1, 1)))
  tail = slice(-10, None)  # last 0.2 s of the clip
  res = {"ckpt": a.ckpt, "motion": a.motion, "clip_s": round(T * dt, 2),
         "ref_rotation_deg": round(float(rot_a[-1]), 1), "robot_rotation_deg": round(float(rot_r[-1]), 1),
         "robot_max_rotation_deg": round(float(np.abs(rot_r).max()), 1),
         "ref_peak_pelvis_m": round(float(max(az)), 3), "robot_peak_pelvis_m": round(float(max(rz)), 3),
         "robot_airborne_s": round(best * dt, 2),
         "landed_upright": bool((tilt[tail] < 30).all() and (np.array(rz)[tail] > 0.5).all()),
         "end_tilt_deg": round(float(tilt[-1]), 1), "end_pelvis_m": round(rz[-1], 3),
         "pelvis_rise_m": round(float(max(rz[15:]) - np.mean(rz[15:25])), 3),
         # strict: the last 1 s really standing (round 4 passed 'landed_upright' while sliding into a lunge)
         "stand_stable": bool((np.array(feet_d[-50:]) < 0.4).all() and (tilt[-50:] < 15).all()
                              and (np.array(rz[-50:]) > 0.7).all()),
         "stand_feet_d_end": round(float(feet_d[-1]), 3),
         # fidelity to the reference over the whole clip (first steps skipped: metrics are stale right after reset)
         "track_body_err_m": round(float(np.mean(trk_body[3:])), 4),
         "track_joint_err": round(float(np.mean(trk_joint[3:])), 4)}
  if a.labels:
    lz = np.load(a.labels)
    pn = [str(x) for x in lz["phase_names"]]
    fl = np.where(lz["phase"] == pn.index("flight"))[0]
    if len(fl):
      # fell while STILL ON THE GROUND before the reference take-off (an early take-off that is already rotating
      # in the air is not a fall: round 7 was flagged by mistake)
      pre = slice(0, min(int(fl[0]), len(tilt)))
      res["early_fall"] = bool(((tilt[pre] > 60) & ~air[pre]).any())
      # out-of-plane: angle between robot and reference torso lateral axes, take-off -> 10 steps after landing
      tk = np.where(lz["phase"] == pn.index("takeoff"))[0]
      s0, s1 = int(tk[0] if len(tk) else fl[0]), min(int(fl[-1]) + 11, len(rq))
      def ly(q):
        w, x, y, z = q
        return np.array([2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)])
      dev = [np.degrees(np.arccos(np.clip(ly(rq[i]) @ ly(aq[i]), -1, 1))) for i in range(s0, s1)]
      res["plane_dev_max_deg"] = round(float(max(dev)), 1) if dev else None
      res["plane_dev_mean_deg"] = round(float(np.mean(dev)), 1) if dev else None
      # legs in the air (flight + 10 steps): left/right asymmetry and error to the reference, mean |rad| -> deg
      a0, a1 = int(fl[0]), min(int(fl[-1]) + 11, len(leg_asym))
      res["leg_asym_deg"] = round(float(np.degrees(np.mean(leg_asym[a0:a1]))), 1)
      res["leg_err_deg"] = round(float(np.degrees(np.mean(leg_err[a0:a1]))), 1)
      # legs together: max horizontal ankle distance from flight to 0.5 s after landing, and at touchdown
      ld = np.where(lz["phase"] == pn.index("land"))[0]
      b1 = min(int(ld[0]) + 25 if len(ld) else a1, len(feet_d))
      res["feet_dist_max_m"] = round(float(max(feet_d[a0:b1])), 3)
      if len(ld) and int(ld[0]) < len(feet_d):
        res["feet_dist_touchdown_m"] = round(feet_d[int(ld[0])], 3)
      # timing / posture found in the step-by-step review of round 2
      f0, f1 = int(fl[0]), int(fl[-1]) + 1  # reference first flight step / landing step
      airs = np.where(air)[0]
      airs = airs[airs >= f0 - 20]  # the jump, not a stray early drop
      if len(airs):
        res["takeoff_offset_steps"] = int(airs[0]) - f0  # < 0 = robot leaves the ground early
        res["landing_offset_steps"] = int(airs[airs >= airs[0]][-1] + 1) - f1 if len(airs) else None
      hp = np.array([[s[jn.index("left_hip_pitch_joint")], s[jn.index("right_hip_pitch_joint")]] for s in steps_q])
      hpr = np.array([[s[jn.index("left_hip_pitch_joint")], s[jn.index("right_hip_pitch_joint")]] for s in steps_qr])
      mid = slice(f0 + (f1 - f0) // 5, f0 + 4 * (f1 - f0) // 5)
      res["flight_hip_err_rad"] = round(float((hp[mid] - hpr[mid]).mean()), 2)  # > 0 = hips extended vs the tuck
      res["flight_hip_mean_rad"] = round(float(hp[mid].mean()), 2)  # > 0 = arched (hips extended), tuck is < 0
      kn = np.array([[s[jn.index("left_knee_joint")], s[jn.index("right_knee_joint")]] for s in steps_q])
      knr = np.array([[s[jn.index("left_knee_joint")], s[jn.index("right_knee_joint")]] for s in steps_qr])
      res["flight_knee_max_rad"] = round(float(kn[mid].max()), 2)
      res["flight_knee_overfold_rad"] = round(float((kn[mid] - knr[mid]).max()), 2)  # > 0.6 = legs coiled
      if f1 < len(rot_r):
        res["rot_at_ref_landing_deg"] = round(float(rot_r[f1]), 1)
        res["ref_rot_at_landing_deg"] = round(float(ref_rot[f1]) if len(ref_rot) > f1 else 0.0, 1)
      # crossed / twisted legs in the air: the left knee must stay left of the right knee (pelvis frame)
      ks = np.array(knee_sep[f0:min(f1 + 10, len(knee_sep))])
      res["knee_sep_min_m"] = round(float(ks.min()), 3) if len(ks) else None
      res["knee_sep_max_m"] = round(float(np.abs(ks).max()), 3) if len(ks) else None  # > 0.45 = knees splayed
      rl = np.array([[s[jn.index("left_hip_roll_joint")], s[jn.index("right_hip_roll_joint")],
                      s[jn.index("left_hip_yaw_joint")], s[jn.index("right_hip_yaw_joint")]] for s in steps_q])
      seg = rl[f0:min(f1 + 10, len(rl))]
      res["flight_hip_roll_max_rad"] = round(float(np.abs(seg[:, :2]).max()), 2) if len(seg) else None
      res["flight_hip_yaw_max_rad"] = round(float(np.abs(seg[:, 2:]).max()), 2) if len(seg) else None
      res["legs_crossed_frac"] = round(float((ks < 0.08).mean()), 3) if len(ks) else None
      # quiet stance: from 0.5 s after the reference landing to the end
      q0 = min(f1 + 25, len(arm_v) - 1)
      res["stand_arm_vel_rms"] = round(float(np.sqrt(np.mean(np.square(arm_v[q0:])))), 3)   # rad/s
      res["stand_action_change"] = round(float(np.mean(act_d[q0:])), 4)
      res["stand_pelvis_speed"] = round(float(np.mean(pel_v[q0:])), 3)                       # m/s
      res["stand_torso_angvel"] = round(float(np.mean(tor_w[q0:])), 3)                       # rad/s
      res["pelvis_min_after_landing_m"] = round(float(min(rz[f1:min(f1 + 25, len(rz))])), 3) if f1 < len(rz) else None
  ck = Path(a.ckpt)
  out = ck.parent / "eval"
  out.mkdir(exist_ok=True)
  # per-step table (every control step, robot vs reference) for frame-by-frame review
  kh = [jn.index(n) for n in ("left_knee_joint", "right_knee_joint", "left_hip_pitch_joint", "right_hip_pitch_joint")]
  utilt = np.degrees(np.arccos(np.clip([1 - 2 * (q[1] ** 2 + q[2] ** 2) for q in aq], -1, 1)))
  with open(out / f"flip_{a.tag or ck.stem}_steps.tsv", "w") as f:
    f.write("step\tphase\trot_robot\trot_ref\tpelvis_z\tpelvis_z_ref\tairborne\ttilt\ttilt_ref\tknee_L\tknee_R\t"
            "knee_ref\thip_L\thip_R\thip_ref\tfeet_d\tleg_asym_deg\troll_L\troll_R\tyaw_L\tyaw_R\tknee_sep\n")
    hr = [jn.index(n) for n in ("left_hip_roll_joint", "right_hip_roll_joint", "left_hip_yaw_joint",
                                "right_hip_yaw_joint")]
    phs = None
    if a.labels:
      lz2 = np.load(a.labels)
      phs = [str(lz2["phase_names"][p]) for p in lz2["phase"]]
    for i in range(len(rot_r)):
      q, qr = steps_q[i], steps_qr[i]
      f.write(f"{i}\t{phs[min(i, len(phs) - 1)] if phs else ''}\t{rot_r[i]:.0f}\t{ref_rot[i]:.0f}\t{rz[i]:.3f}\t"
              f"{az[i]:.3f}\t{int(air[i])}\t{tilt[i]:.0f}\t{utilt[i]:.0f}\t{q[kh[0]]:.2f}\t{q[kh[1]]:.2f}\t"
              f"{qr[kh[0]]:.2f}\t{q[kh[2]]:.2f}\t{q[kh[3]]:.2f}\t{qr[kh[2]]:.2f}\t{feet_d[i]:.2f}\t"
              f"{np.degrees(leg_asym[i]):.0f}\t{q[hr[0]]:.2f}\t{q[hr[1]]:.2f}\t{q[hr[2]]:.2f}\t{q[hr[3]]:.2f}\t"
              f"{knee_sep[i]:.3f}\n")
  np.savez_compressed(out / f"flip_{a.tag or ck.stem}_record.npz", joint_names=np.array(jn),
                      body_names=np.array(list(cmd.cfg.body_names)), dt=dt, **{k: np.array(v) for k, v in rec.items()})
  mp4 = out / f"flip_{a.tag or ck.stem}.mp4"
  imageio.mimsave(mp4, [f for f in frames if f is not None], fps=int(round(1 / dt)), macro_block_size=1)
  res["video"] = str(mp4)
  json.dump(res, open(out / f"flip_{a.tag or ck.stem}.json", "w"), indent=1)
  print(json.dumps(res))
