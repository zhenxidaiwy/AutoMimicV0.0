"""Backflip technique rewards (capability probe), gated by the per-frame phase labels of the clip (labels_50fps.npz,
phases from scripts/data/package_backflip.py: stand, crouch, takeoff, flight, land, settle, other) AND by the robot's
own foot contact state.

Order of the skill (user's design 2026-10-22): feet on the ground -> only a moderate backward lean; both feet load
and push off upward; the big rotation is rewarded ONLY once the robot is really airborne.
Robot rewards so far (no technique terms): it fell backwards (106-153 deg) with 0 s of both feet off the ground;
with 1.5x torque it jumped (pelvis 0.92 m, 0.6 s off the ground) but did not spin (80-128 deg).

  push-off         flip_pushoff  crouch(last 0.2 s) / takeoff / first 30 % of flight, BOTH ankles still within
                                 12 cm of the floor: pelvis v_z / v0, v0 = g * t_flight / 2, clipped to [0, 1]
  lean, not fall   flip_lean     crouch / takeoff while any ankle is on the floor: 1 if torso tilt <= 35 deg,
                                 exp(-(tilt - 35) / 10 deg) beyond (rotating on the ground earns nothing)
  spin in the air  flip_spin     robot airborne (_airborne) during takeoff / flight / land(first 0.2 s):
                                 torso angular velocity projected on the reference's / |ref|, clipped to [0, 1.2]
  leave the ground flip_airborne flight: whole body > 5 cm above the floor and pelvis > 0.45 m (_airborne)
  height           flip_height   flight: exp(-max(z_ref - z_robot, 0) / 0.15) on the pelvis
  land upright     flip_land     land + settle: torso up-axis . world z (>= 0) * both ankles near the floor
Sources: standing back somersault biomechanics (vertical CoM elevation, arm swing), stage-wise acrobatic RL rewards
(arXiv 2409.15755), centroidal angular velocity reward for flips (CoRL 2025).
"""
import numpy as np
import torch

PHASES = ["stand", "crouch", "takeoff", "flight", "land", "settle", "other"]
_cache = {}


def _phase(env, labels, command_name):
  """(phase id, flight progress in [0,1], frames since the phase started) at each env's reference frame, t_flight s"""
  key = (labels, str(env.device))
  if key not in _cache:
    z = np.load(labels)
    ph = z["phase"]
    since = np.zeros(len(ph), np.int64)
    for i in range(1, len(ph)):
      since[i] = since[i - 1] + 1 if ph[i] == ph[i - 1] else 0
    until = np.zeros(len(ph), np.int64)  # frames until the phase ends
    for i in range(len(ph) - 2, -1, -1):
      until[i] = until[i + 1] + 1 if ph[i] == ph[i + 1] else 0
    fl = np.where(ph == PHASES.index("flight"))[0]
    prog = np.zeros(len(ph), np.float32)
    if len(fl):
      prog[fl] = (fl - fl[0]) / max(len(fl) - 1, 1)
    d = env.device
    _cache[key] = (torch.tensor(ph, device=d), torch.tensor(prog, device=d), torch.tensor(since, device=d),
                   torch.tensor(until, device=d), len(fl) / 50.0)
  ph, prog, since, until, tf = _cache[key]
  t = env.command_manager.get_term(command_name).time_steps.clamp(max=len(ph) - 1)
  return ph[t], prog[t], since[t], until[t], tf


def _ankle_z(env):
  robot = env.scene["robot"]
  if "_ank" not in _cache:
    _cache["_ank"] = [list(robot.body_names).index(n) for n in ("left_ankle_roll_link", "right_ankle_roll_link")]
  return robot.data.body_link_pos_w[:, _cache["_ank"], 2] - env.scene.env_origins[:, None, 2]


def _airborne(env):
  """Really in the air: EVERY body > 5 cm above the floor and the pelvis > 0.45 m. (v1 used 'both ankles > 8 cm':
  r2 flipB3k learned to lie on its side kicking its legs up and collected airborne + spin rewards.)"""
  robot = env.scene["robot"]
  z = robot.data.body_link_pos_w[:, :, 2] - env.scene.env_origins[:, None, 2]
  return (z.min(-1).values > 0.05) & (robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2] > 0.45)


def _tilt_deg(env, command_name):
  q = env.command_manager.get_term(command_name).robot_anchor_quat_w  # wxyz
  up = (1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)).clamp(-1.0, 1.0)
  return torch.rad2deg(torch.arccos(up))


def flip_pushoff(env, labels: str, command_name: str = "motion"):
  ph, prog, _, until, tf = _phase(env, labels, command_name)
  gate = (((ph == PHASES.index("crouch")) & (until < 10)) | (ph == PHASES.index("takeoff"))
          | ((ph == PHASES.index("flight")) & (prog < 0.3)))
  both_down = (_ankle_z(env) < 0.12).all(-1)
  v0 = 9.81 * max(tf, 0.2) / 2
  vz = env.scene["robot"].data.root_link_lin_vel_w[:, 2]
  return (gate & both_down).float() * (vz / v0).clamp(0.0, 1.0)


def flip_lean(env, labels: str, command_name: str = "motion"):
  ph, _, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("crouch")) | (ph == PHASES.index("takeoff"))
  on_ground = ~_airborne(env)
  tilt = _tilt_deg(env, command_name)
  return (gate & on_ground).float() * torch.exp(-(tilt - 35.0).clamp(min=0.0) / 10.0)


def flip_spin(env, labels: str, command_name: str = "motion"):
  ph, _, since, _, _ = _phase(env, labels, command_name)
  gate = ((ph == PHASES.index("takeoff")) | (ph == PHASES.index("flight"))
          | ((ph == PHASES.index("land")) & (since < 10))) & _airborne(env)
  cmd = env.command_manager.get_term(command_name)
  wr, wa = cmd.robot_anchor_ang_vel_w, cmd.anchor_ang_vel_w
  n2 = (wa * wa).sum(-1)
  r = ((wr * wa).sum(-1) / n2.clamp(min=1e-6)).clamp(0.0, 1.2)
  return gate.float() * (n2 > 1.0).float() * r


def flip_airborne(env, labels: str, command_name: str = "motion"):
  ph, _, _, _, _ = _phase(env, labels, command_name)
  return (ph == PHASES.index("flight")).float() * _airborne(env).float()


def flip_height(env, labels: str, command_name: str = "motion"):
  ph, _, _, _, _ = _phase(env, labels, command_name)
  cmd = env.command_manager.get_term(command_name)
  short = (cmd.body_pos_w[:, 0, 2] - env.scene["robot"].data.root_link_pos_w[:, 2]).clamp(min=0.0)
  return (ph == PHASES.index("flight")).float() * torch.exp(-short / 0.15)


def flip_land(env, labels: str, command_name: str = "motion"):
  ph, _, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("land")) | (ph == PHASES.index("settle"))
  up = torch.cos(torch.deg2rad(_tilt_deg(env, command_name))).clamp(min=0.0)
  return gate.float() * up * (_ankle_z(env) < 0.1).all(-1).float()


def _axis_y(q):
  """torso lateral (left) axis in the world from wxyz quaternions (N, 4)."""
  w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
  return torch.stack([2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)], -1)


def _flip_window(env, labels, command_name):
  ph, _, since, _, _ = _phase(env, labels, command_name)
  return ((ph == PHASES.index("takeoff")) | (ph == PHASES.index("flight"))
          | ((ph == PHASES.index("land")) & (since < 10)))


def flip_plane_axis(env, labels: str, command_name: str = "motion"):
  """Stay in the flip plane (user 2026-10-22: the torso twisted / tilted out of plane while flipping): cosine of the
  angle between the robot's and the reference's torso lateral axes, takeoff -> early landing, >= 0."""
  cmd = env.command_manager.get_term(command_name)
  c = (_axis_y(cmd.robot_anchor_quat_w) * _axis_y(cmd.anchor_quat_w)).sum(-1).clamp(min=0.0)
  return _flip_window(env, labels, command_name).float() * c


def flip_plane_rate(env, labels: str, command_name: str = "motion"):
  """Spin only about the reference's axis: exp(-|omega_perp| / 2 rad/s), omega_perp = the torso angular velocity
  component orthogonal to the reference angular velocity direction (or all of it when the reference is still)."""
  cmd = env.command_manager.get_term(command_name)
  wr, wa = cmd.robot_anchor_ang_vel_w, cmd.anchor_ang_vel_w
  u = wa / wa.norm(dim=-1, keepdim=True).clamp(min=1e-6)
  perp = wr - (wr * u).sum(-1, keepdim=True) * u
  return _flip_window(env, labels, command_name).float() * torch.exp(-perp.norm(dim=-1) / 2.0)


LEG = ("hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll")
MIRROR = torch.tensor([1.0, -1.0, -1.0, 1.0, 1.0, -1.0])  # right = sign * left for a symmetric pose


def _legs(env):
  """indices of the left / right leg joints (robot joint order = motion joint order)."""
  if "_legs" not in _cache:
    names = list(env.scene["robot"].joint_names)
    li = [names.index(f"left_{j}_joint") for j in LEG]
    ri = [names.index(f"right_{j}_joint") for j in LEG]
    _cache["_legs"] = (li, ri, MIRROR.to(env.device))
  return _cache["_legs"]


def _air_window(env, labels, command_name):
  """flight and the first 0.2 s of landing (legs must be tucked and symmetric, then meet the floor together)."""
  ph, _, since, _, _ = _phase(env, labels, command_name)
  return (ph == PHASES.index("flight")) | ((ph == PHASES.index("land")) & (since < 10))


def flip_leg_sym(env, labels: str, command_name: str = "motion"):
  """Legs symmetric in the air (user: the legs flailed during the flip, so it could not stand after landing)."""
  li, ri, s = _legs(env)
  q = env.scene["robot"].data.joint_pos
  d = (q[:, ri] - s * q[:, li]).abs().mean(-1)
  return _air_window(env, labels, command_name).float() * torch.exp(-d / 0.2)


def flip_leg_track(env, labels: str, command_name: str = "motion"):
  """Leg joints follow the reference tuck in the air."""
  li, ri, _ = _legs(env)
  idx = li + ri
  q = env.scene["robot"].data.joint_pos[:, idx]
  qr = env.command_manager.get_term(command_name).joint_pos[:, idx]
  return _air_window(env, labels, command_name).float() * torch.exp(-(q - qr).abs().mean(-1) / 0.3)


def flip_leg_calm(env, labels: str, command_name: str = "motion"):
  """No flailing: leg joint velocities close to the reference's in the air."""
  li, ri, _ = _legs(env)
  idx = li + ri
  v = env.scene["robot"].data.joint_vel[:, idx]
  vr = env.command_manager.get_term(command_name).joint_vel[:, idx]
  return _air_window(env, labels, command_name).float() * torch.exp(-(v - vr).abs().mean(-1) / 5.0)


def flip_feet_together(env, labels: str, command_name: str = "motion"):
  """Legs together (user: the legs were spread wide at landing and it could not stand): in flight / land / settle,
  horizontal ankle distance d vs allowed = max(reference distance, 0.18 m standing width):
  exp(-max(d - allowed, 0) / 0.06)."""
  ph, _, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("flight")) | (ph == PHASES.index("land")) | (ph == PHASES.index("settle"))
  robot = env.scene["robot"]
  _ankle_z(env)  # fills _cache["_ank"]
  p = robot.data.body_link_pos_w[:, _cache["_ank"], :2]
  d = (p[:, 0] - p[:, 1]).norm(dim=-1)
  cmd = env.command_manager.get_term(command_name)
  if "_ank_ref" not in _cache:
    bn = list(cmd.cfg.body_names)
    _cache["_ank_ref"] = [bn.index("left_ankle_roll_link"), bn.index("right_ankle_roll_link")]
  pr = cmd.body_pos_w[:, _cache["_ank_ref"], :2]
  allowed = (pr[:, 0] - pr[:, 1]).norm(dim=-1).clamp(min=0.18)
  return gate.float() * torch.exp(-(d - allowed).clamp(min=0.0) / 0.06)


# --- batch from the frame-by-frame review of round 2 (2026-10-22): took off ~4 frames early, flew with straight body
# and legs (layout, ~2x the tucked inertia) -> rotation lagged 6-8 frames -> landed 45 deg under-rotated with the CoM
# behind the feet -> fell back and split the legs.

def _knee_hip(env):
  if "_kh" not in _cache:
    names = list(env.scene["robot"].joint_names)
    _cache["_kh"] = [names.index(f"{s}_{j}_joint") for s in ("left", "right") for j in ("knee", "hip_pitch")]
  return _cache["_kh"]


def flip_tuck(env, labels: str, command_name: str = "motion"):
  """Mid-flight (20-80 % of the flight): knees and hips flexed AT LEAST as much as the reference tuck.
  G1 knee flexion is positive, hip pitch flexion (thigh to chest) is negative."""
  ph, prog, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("flight")) & (prog > 0.2) & (prog < 0.8)
  idx = _knee_hip(env)  # [L knee, L hip pitch, R knee, R hip pitch]
  q = env.scene["robot"].data.joint_pos[:, idx]
  qr = env.command_manager.get_term(command_name).joint_pos[:, idx]
  # hips one-sided (at least as flexed as the reference, hip flexion is negative); knees TWO-sided: the one-sided
  # version rewarded folding the knees to the 2.9 rad limit while the hips stayed extended (round 6: legs coiled
  # behind an arched body instead of a tuck)
  hip_short = (q[:, [1, 3]] - qr[:, [1, 3]]).clamp(min=0.0).mean(-1)
  knee_err = ((q[:, [0, 2]] - qr[:, [0, 2]]).abs() - 0.4).clamp(min=0.0).mean(-1)
  return gate.float() * torch.exp(-(hip_short + knee_err) / 0.3)


def flip_rot_track(env, labels: str, command_name: str = "motion"):
  """Rotation on time: gravity direction in the torso frame, robot vs reference, flight + first 0.2 s of landing."""
  cmd = env.command_manager.get_term(command_name)

  def g_body(q):  # world gravity (0,0,-1) in the body frame of wxyz q = third row of R(q), negated
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return -torch.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)
  d = (g_body(cmd.robot_anchor_quat_w) - g_body(cmd.anchor_quat_w)).pow(2).sum(-1)
  return _air_window(env, labels, command_name).float() * torch.exp(-d / 0.25)


def flip_land_balance(env, labels: str, command_name: str = "motion"):
  """Land with the CoM over the feet: horizontal distance pelvis -> ankle midpoint, land + settle,
  exp(-d / 0.08 m); plus knee flexion (absorption) in the first 0.3 s of landing."""
  ph, _, since, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("land")) | (ph == PHASES.index("settle"))
  robot = env.scene["robot"]
  _ankle_z(env)
  mid = robot.data.body_link_pos_w[:, _cache["_ank"], :2].mean(1)
  d = (robot.data.root_link_pos_w[:, :2] - mid).norm(dim=-1)
  r = torch.exp(-d / 0.08)
  idx = _knee_hip(env)
  knee = robot.data.joint_pos[:, [idx[0], idx[2]]].mean(-1)
  absorb = ((ph == PHASES.index("land")) & (since < 15)).float() * (knee / 0.6).clamp(0.0, 1.0)
  return gate.float() * (0.7 * r + 0.3 * absorb)


def flip_stay_down(env, labels: str, command_name: str = "motion"):
  """No early take-off: during crouch and the first 60 % of the takeoff phase both feet stay on the floor."""
  ph, _, since, until, _ = _phase(env, labels, command_name)
  tk = ph == PHASES.index("takeoff")
  gate = (ph == PHASES.index("crouch")) | (tk & (until > since))  # crouch + first half of takeoff
  return gate.float() * (_ankle_z(env) < 0.08).all(-1).float()


# --- round 4 review (2026-10-22): soft rewards lost against spin/airborne: the robot flew as a "star" (feet 1.26 m
# apart, hips +2.1 rad extended instead of the -1.57 tuck), and after a good touchdown slid into a lunge (feet 0.73 m).
# -> hard terminations (lose all future reward) + a stand-still reward after landing.

def _feet_dist(env):
  _ankle_z(env)
  p = env.scene["robot"].data.body_link_pos_w[:, _cache["_ank"], :2]
  return (p[:, 0] - p[:, 1]).norm(dim=-1)


def term_flight_spread(env, labels: str, max_d: float = 0.6, command_name: str = "motion"):
  """terminate: feet more than max_d apart in flight / first 0.2 s of landing."""
  return _air_window(env, labels, command_name) & (_feet_dist(env) > max_d)


def term_hip_extended(env, labels: str, max_hip: float = 1.2, command_name: str = "motion"):
  """terminate: mid-flight (20-80 %) mean hip pitch above max_hip (extended backwards instead of tucked)."""
  ph, prog, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("flight")) & (prog > 0.2) & (prog < 0.8)
  idx = _knee_hip(env)
  hip = env.scene["robot"].data.joint_pos[:, [idx[1], idx[3]]].mean(-1)
  return gate & (hip > max_hip)


def term_leg_twist(env, labels: str, max_roll: float = 0.6, max_yaw: float = 0.8, max_knee_sep: float = 0.45,
                   command_name: str = "motion"):
  """terminate: legs twisted / knees splayed in flight or the first 0.2 s of landing (round 7: feet together but
  knees 0.85 m apart, hip roll +-1.5 and yaw +-2.4 rad - a cross-legged 'lotus' shape instead of the tuck)."""
  robot = env.scene["robot"]
  if "_rollyaw" not in _cache:
    names = list(robot.joint_names)
    _cache["_rollyaw"] = ([names.index(f"{s}_hip_roll_joint") for s in ("left", "right")],
                          [names.index(f"{s}_hip_yaw_joint") for s in ("left", "right")],
                          [list(robot.body_names).index(f"{s}_knee_link") for s in ("left", "right")])
  ri, yi, ki = _cache["_rollyaw"]
  q = robot.data.joint_pos
  kp = robot.data.body_link_pos_w[:, ki]
  pq = robot.data.root_link_quat_w
  w, x, y, z = pq[:, 0], pq[:, 1], pq[:, 2], pq[:, 3]
  yax = torch.stack([2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)], -1)
  sep = ((kp[:, 0] - kp[:, 1]) * yax).sum(-1).abs()
  bad = (q[:, ri].abs() > max_roll).any(-1) | (q[:, yi].abs() > max_yaw).any(-1) | (sep > max_knee_sep)
  return _air_window(env, labels, command_name) & bad


def term_stand_fail(env, labels: str, max_d: float = 0.5, max_tilt: float = 35.0, max_waist: float = 0.6,
                    command_name: str = "motion"):
  """terminate: after landing (settle / stand) feet more than max_d apart, torso tilt above max_tilt deg, or the
  waist twisted more than max_waist rad (round 7 stood with waist_yaw +2.1 rad)."""
  ph, _, _, _, _ = _phase(env, labels, command_name)
  gate = (ph == PHASES.index("settle")) | (ph == PHASES.index("stand"))
  # 'stand' also labels the frames BEFORE the crouch: only count it once the reference has landed
  t = env.command_manager.get_term(command_name).time_steps
  key = (labels, "landed_from")
  if key not in _cache:
    z = np.load(labels)
    ld = np.where(z["phase"] == PHASES.index("land"))[0]
    _cache[key] = int(ld[0]) if len(ld) else 10 ** 9
  gate = gate & (t >= _cache[key])
  if "_waist" not in _cache:
    _cache["_waist"] = list(env.scene["robot"].joint_names).index("waist_yaw_joint")
  waist = env.scene["robot"].data.joint_pos[:, _cache["_waist"]].abs()
  return gate & ((_feet_dist(env) > max_d) | (_tilt_deg(env, command_name) > max_tilt) | (waist > max_waist))


def flip_stand_still(env, labels: str, command_name: str = "motion"):
  """after landing: leg joints at the reference standing pose and no horizontal drift of the pelvis."""
  ph, _, _, _, _ = _phase(env, labels, command_name)
  t = env.command_manager.get_term(command_name).time_steps
  key = (labels, "landed_from")
  if key not in _cache:
    term_stand_fail(env, labels)
  gate = ((ph == PHASES.index("settle")) | (ph == PHASES.index("stand"))) & (t >= _cache[key])
  # ALL joints (legs, waist, arms) back to the reference standing pose (round 7: waist twisted ~115 deg, arms
  # asymmetric by ~90 deg while the legs alone looked fine)
  q = env.scene["robot"].data.joint_pos
  qr = env.command_manager.get_term(command_name).joint_pos
  v = env.scene["robot"].data.root_link_lin_vel_w[:, :2].norm(dim=-1)
  return gate.float() * (0.5 * torch.exp(-(q - qr).abs().mean(-1) / 0.2) + 0.5 * torch.exp(-v / 0.2))


def flip_root_pos(env, labels: str, command_name: str = "motion", std: float = 0.3):
  """Replaces the tracking term motion_global_root_pos: full 3D anchor-position tracking until the reference lands,
  height only afterwards. Round 6 landed ~0.4 m beside the reference's landing spot and then walked towards it
  (pelvis 0.78 -> 0.65 m, stepping backwards) because the global xy term kept pulling."""
  cmd = env.command_manager.get_term(command_name)
  d = cmd.anchor_pos_w - cmd.robot_anchor_pos_w
  t = cmd.time_steps
  key = (labels, "landed_from")
  if key not in _cache:
    term_stand_fail(env, labels)
  after = (t >= _cache[key]).float()
  err = (d[:, :2] ** 2).sum(-1) * (1.0 - after) + d[:, 2] ** 2
  return torch.exp(-err / std ** 2)


def flip_stand_quiet(env, labels: str, command_name: str = "motion"):
  """Quiet standing after landing (user: hands trembling, body swaying): arm joint speed, torso angular speed and
  action change all small. Bounded positive: mean of exp(-arm_vel_rms / 1.0), exp(-|w_torso| / 0.5),
  exp(-|a_t - a_t-1|_mean / 0.05)."""
  ph, _, _, _, _ = _phase(env, labels, command_name)
  t = env.command_manager.get_term(command_name).time_steps
  key = (labels, "landed_from")
  if key not in _cache:
    term_stand_fail(env, labels)
  gate = ((ph == PHASES.index("settle")) | (ph == PHASES.index("stand"))) & (t >= _cache[key])
  robot = env.scene["robot"]
  if "_arms" not in _cache:
    _cache["_arms"] = [i for i, n in enumerate(robot.joint_names) if any(s in n for s in ("shoulder", "elbow", "wrist"))]
  arm = robot.data.joint_vel[:, _cache["_arms"]].pow(2).mean(-1).sqrt()
  w = env.command_manager.get_term(command_name).robot_anchor_ang_vel_w.norm(dim=-1)
  am = env.action_manager
  da = (am.action - am.prev_action).abs().mean(-1)
  r = (torch.exp(-arm / 1.0) + torch.exp(-w / 0.5) + torch.exp(-da / 0.05)) / 3.0
  return gate.float() * r


def flip_root_ori(env, labels: str, command_name: str = "motion", std: float = 0.4):
  """Replaces motion_global_root_ori: full torso orientation until the reference lands, then only tilt (gravity
  direction in the torso frame), heading free. Round 7 landed with a heading offset and twisted the waist by
  ~115 deg (waist_yaw +2.1 rad) to bring the torso back to the reference heading; arms and ankles then flailed."""
  cmd = env.command_manager.get_term(command_name)
  from mjlab.utils.lab_api.math import quat_error_magnitude
  full = quat_error_magnitude(cmd.anchor_quat_w, cmd.robot_anchor_quat_w) ** 2

  def g_body(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return torch.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)
  tilt_err = torch.arccos(((g_body(cmd.anchor_quat_w) * g_body(cmd.robot_anchor_quat_w)).sum(-1)).clamp(-1, 1)) ** 2
  key = (labels, "landed_from")
  if key not in _cache:
    term_stand_fail(env, labels)
  after = cmd.time_steps >= _cache[key]
  return torch.exp(-torch.where(after, tilt_err, full) / std ** 2)


# --- generic fix templates, instantiated by the harness from the diagnostic library (rl/flip_auto/library.json) ---
# phases: label names; "stand_after" = 'stand' frames once the reference has landed.

def _phase_gate(env, labels, phases, command_name="motion"):
  ph, _, _, _, _ = _phase(env, labels, command_name)
  t = env.command_manager.get_term(command_name).time_steps
  key = (labels, "landed_from")
  if key not in _cache:
    term_stand_fail(env, labels)
  g = torch.zeros_like(ph, dtype=torch.bool)
  for p in phases:
    if p == "stand_after":
      g |= (ph == PHASES.index("stand")) & (t >= _cache[key])
    elif p in PHASES:
      g |= ph == PHASES.index(p)
  return g


def _jidx(env, joints):
  key = ("_j", tuple(joints))
  if key not in _cache:
    names = list(env.scene["robot"].joint_names)
    _cache[key] = [names.index(j) for j in joints]
  return _cache[key]


def dyn_joint(env, labels: str, joints: list, phases: list, std: float = 0.3, command_name: str = "motion"):
  """joint angles of `joints` close to the reference in `phases`: exp(-mean |q - q_ref| / std)."""
  i = _jidx(env, joints)
  e = (env.scene["robot"].data.joint_pos[:, i] - env.command_manager.get_term(command_name).joint_pos[:, i]).abs()
  return _phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_body(env, labels: str, bodies: list, phases: list, std: float = 0.1, command_name: str = "motion"):
  """tracked bodies at the reference shape (relative frame) in `phases`: exp(-mean |p - p_ref| / std)."""
  cmd = env.command_manager.get_term(command_name)
  key = ("_b", tuple(bodies))
  if key not in _cache:
    bn = list(cmd.cfg.body_names)
    _cache[key] = [bn.index(b) for b in bodies]
  i = _cache[key]
  e = (cmd.robot_body_pos_w[:, i] - cmd.body_pos_relative_w[:, i]).norm(dim=-1)
  return _phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_quiet(env, labels: str, joints: list, phases: list, std: float = 1.0, command_name: str = "motion"):
  """no jitter: joint velocities of `joints` close to the reference's: exp(-mean |dq - dq_ref| / std)."""
  i = _jidx(env, joints)
  e = (env.scene["robot"].data.joint_vel[:, i] - env.command_manager.get_term(command_name).joint_vel[:, i]).abs()
  return _phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_sym(env, labels: str, base: str, sign: float, phases: list, std: float = 0.2, command_name: str = "motion"):
  """left/right symmetry of joint `base` as symmetric as the reference: exp(-| |qR - s qL| - |qrR - s qrL| | / std)."""
  li, ri = _jidx(env, [f"left_{base}_joint", f"right_{base}_joint"])
  q = env.scene["robot"].data.joint_pos
  qr = env.command_manager.get_term(command_name).joint_pos
  e = ((q[:, ri] - sign * q[:, li]).abs() - (qr[:, ri] - sign * qr[:, li]).abs()).abs()
  return _phase_gate(env, labels, phases, command_name).float() * torch.exp(-e / std)


def dyn_contact(env, labels: str, foot: int, phases: list, command_name: str = "motion"):
  """foot `foot` (0 left, 1 right) on the floor in `phases`."""
  return _phase_gate(env, labels, phases, command_name).float() * (_ankle_z(env)[:, foot] < 0.06).float()


def add_dyn_rewards(rewards, labels, dyn):
  """dyn: [{"name", "func", "weight", "params"}] from the harness's diagnostic library."""
  from mjlab.managers.reward_manager import RewardTermCfg
  for d in dyn:
    rewards[d["name"]] = RewardTermCfg(func=globals()[d["func"]], weight=d["weight"],
                                       params={"labels": labels, **d["params"]})
  return rewards


TERMS = {"term_flight_spread": {"max_d": 0.6}, "term_hip_extended": {"max_hip": 1.2},
         "term_stand_fail": {"max_d": 0.5, "max_tilt": 35.0}}


def add_flip_terminations(terminations, labels, terms):
  """terms: {name: params} (thresholds) -> TerminationTermCfg entries."""
  from mjlab.managers.termination_manager import TerminationTermCfg
  for name, params in terms.items():
    terminations[name] = TerminationTermCfg(func=globals()[name], params={"labels": labels, **params})
  return terminations


def set_knee_limit(articulation, limit):
  """Split the knee joints out of the 7520-22 actuator group (shared with hip roll) and give them `limit` N.m."""
  import dataclasses
  out = []
  for c in articulation.actuators:
    names = tuple(c.target_names_expr)
    if ".*_knee_joint" in names:
      rest = tuple(n for n in names if n != ".*_knee_joint")
      if rest:
        out.append(dataclasses.replace(c, target_names_expr=rest))
      out.append(dataclasses.replace(c, target_names_expr=(".*_knee_joint",), effort_limit=limit))
    else:
      out.append(c)
  articulation.actuators = tuple(out)


WEIGHTS = {"flip_pushoff": 2.0, "flip_lean": 1.0, "flip_spin": 3.0, "flip_airborne": 1.5, "flip_height": 1.0,
           "flip_land": 1.0, "flip_plane_axis": 1.5, "flip_plane_rate": 1.0, "flip_leg_sym": 1.0,
           "flip_leg_track": 1.0, "flip_leg_calm": 0.5, "flip_feet_together": 2.0, "flip_tuck": 2.0,
           "flip_rot_track": 2.0, "flip_land_balance": 2.0, "flip_stay_down": 1.0, "flip_stand_still": 2.0,
           "flip_stand_quiet": 2.0}


def add_flip_rewards(rewards, labels, scale=1.0):
  """Add the technique terms to an env cfg's reward dict (weights x scale)."""
  from mjlab.managers.reward_manager import RewardTermCfg
  for name, wt in WEIGHTS.items():
    rewards[name] = RewardTermCfg(func=globals()[name], weight=wt * scale, params={"labels": labels})
  return rewards
