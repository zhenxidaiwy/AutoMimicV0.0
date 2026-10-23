"""Get-up task events / rewards / success check.
Adapted from chaoticcuriosity-io/g1-humanoid-rl (MIT), recovery-task/mdp/{events,rewards,terminations}.py.
"""
from __future__ import annotations

import math

import torch
from mjlab.entity import Entity
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.utils.lab_api.math import quat_from_euler_xyz, sample_uniform

_ROBOT = SceneEntityCfg("robot")


def reset_root_state_lying_down(env, env_ids, height_range=(0.08, 0.15), yaw_range=(-3.14, 3.14), asset_cfg=_ROBOT,
                                pose=None, pose_extra=(0.0, 0.0, 0.0, 0.0), true_supine=False):
  """Reset into one of four fallen poses (supine, face-down, left side, right side) with random yaw, zero velocity.
  pose: None = random per env; 0..3 = force supine / face-down / left side / right side (used for demo videos).
  pose_extra: extra drop height per pose (v7e: lying on a side at 0.08-0.15 m puts the shoulder/arm into the floor and
  the contact solver ejects the robot at up to ~9 m/s in the first 0.1 s - the "bounce" seen in the videos).
  true_supine (v7e): the upstream "supine" pose is roll = pi, i.e. the robot standing UPSIDE DOWN with the torso and
  head buried in the floor; it is ejected at ~8.6 m/s (measured) and only then lands on its back. True supine =
  pitch -pi/2 (lying on the back)."""
  if env_ids is None:
    env_ids = torch.arange(env.num_envs, device=env.device, dtype=torch.int)
  asset: Entity = env.scene[asset_cfg.name]
  n = len(env_ids)
  yaw = sample_uniform(yaw_range[0], yaw_range[1], (n,), env.device)
  pose_idx = torch.randint(0, 4, (n,), device=env.device) if pose is None else torch.full((n,), pose, device=env.device)
  if true_supine:
    roll = torch.tensor([0.0, 0.0, math.pi / 2, -math.pi / 2], device=env.device)[pose_idx]
    pitch = torch.tensor([-math.pi / 2, math.pi / 2, 0.0, 0.0], device=env.device)[pose_idx]
  else:
    roll = torch.tensor([math.pi, 0.0, math.pi / 2, -math.pi / 2], device=env.device)[pose_idx]
    pitch = torch.tensor([0.0, math.pi / 2, 0.0, 0.0], device=env.device)[pose_idx]
  quat = quat_from_euler_xyz(roll, pitch, yaw)
  pos = env.scene.env_origins[env_ids].clone()
  pos[:, 2] += sample_uniform(height_range[0], height_range[1], (n,), env.device)
  pos[:, 2] += torch.tensor(pose_extra, device=env.device)[pose_idx]
  asset.write_root_link_pose_to_sim(torch.cat([pos, quat], dim=-1), env_ids=env_ids)
  asset.write_root_link_velocity_to_sim(torch.zeros(n, 6, device=env.device), env_ids=env_ids)
  if not hasattr(env, "_getup_pose"):
    env._getup_pose = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)
  env._getup_pose[env_ids.long()] = pose_idx


def stand_up_height_reward(env, target_height, floor_height=0.1, asset_cfg=_ROBOT):
  """Clamped linear ramp on pelvis height: 0 on the floor, 1 at the standing height (gradient everywhere)."""
  z = env.scene[asset_cfg.name].data.root_link_pos_w[:, 2]
  return torch.clamp((z - floor_height) / (target_height - floor_height), 0.0, 1.0)


# --- v5 (ours): fix the upside-down reward hack -------------------------------------------------------------------
# mjlab's flat_orientation only penalises the xy components of the projected gravity, so an inverted pelvis
# (gravity along +z of the body) scores like an upright one; together with a pure height reward the v4 policy
# learned a folded / headstand-like pose that lifts the pelvis to ~0.69 m with the pelvis up-axis pointing down.

def pelvis_up(env, asset_cfg=_ROBOT):
  """Signed uprightness of the pelvis: +1 upright, 0 horizontal, -1 upside down (= -gravity_z in the body frame)."""
  return -env.scene[asset_cfg.name].data.projected_gravity_b[:, 2]


def upright_signed_reward(env, asset_cfg=_ROBOT):
  """Reward only the upright direction (inverted gets 0)."""
  return torch.clamp(pelvis_up(env, asset_cfg), 0.0, 1.0)


def stand_up_upright_reward(env, target_height, floor_height=0.1, asset_cfg=_ROBOT):
  """Height ramp counted only as much as the pelvis is upright (squared): no credit for lifting it upside down."""
  return stand_up_height_reward(env, target_height, floor_height, asset_cfg) * \
      torch.clamp(pelvis_up(env, asset_cfg), 0.0, 1.0) ** 2


# --- v6 (ours): slow, physically plausible get-up ------------------------------------------------------------------
# v5 got up in 0.3 s and, from supine, launched itself ~3 m into the air (contact-penetration exploit).

def _standing_gate(env, height, upright, asset_cfg=_ROBOT):
  a = env.scene[asset_cfg.name]
  return ((a.data.root_link_pos_w[:, 2] > height) & (pelvis_up(env, asset_cfg) > upright)).float()


def rise_speed_penalty(env, max_speed=0.6, asset_cfg=_ROBOT):
  """Squared excess of the pelvis vertical speed (up or down) over max_speed (m/s)."""
  vz = env.scene[asset_cfg.name].data.root_link_lin_vel_w[:, 2]
  return torch.square(torch.clamp(vz.abs() - max_speed, min=0.0))


def overshoot_penalty(env, max_height=0.85, asset_cfg=_ROBOT):
  """Pelvis above standing height (jumping / launching)."""
  z = env.scene[asset_cfg.name].data.root_link_pos_w[:, 2]
  return torch.clamp(z - max_height, min=0.0)


def flight_penalty(env, sensor_name="robot_ground"):
  """1 when no robot body touches the ground (airborne)."""
  found = env.scene[sensor_name].data.found
  return (found.reshape(found.shape[0], -1).sum(dim=1) == 0).float()


def standing_posture_reward(env, height=0.65, upright=0.9, std=0.25, asset_cfg=_ROBOT):
  """Once standing: joints close to the default standing keyframe (straight, symmetric stance)."""
  a = env.scene[asset_cfg.name]
  err = torch.mean(torch.square(a.data.joint_pos - a.data.default_joint_pos), dim=1)
  return _standing_gate(env, height, upright, asset_cfg) * torch.exp(-err / std**2)


# --- v6c (ours): upright TORSO, straight waist, normal stance width ------------------------------------------------
# v5/v6b stood with the pelvis level but the waist roll & pitch joints at their limits (+0.53 rad each): the torso
# leaned ~42 deg, because the upright terms only looked at the pelvis. Also the feet were 0.54 m apart (keyframe 0.24).

def _body_up(env, body_name, asset_cfg=_ROBOT):
  """Signed uprightness of a body: +1 upright, -1 upside down."""
  from mjlab.utils.lab_api.math import quat_apply_inverse
  a = env.scene[asset_cfg.name]
  q = a.data.body_link_quat_w[:, a.body_names.index(body_name)]
  g = torch.tensor([0.0, 0.0, -1.0], device=q.device).expand(q.shape[0], 3)
  return -quat_apply_inverse(q, g)[:, 2]


def torso_upright_reward(env, body_name="torso_link", asset_cfg=_ROBOT):
  return torch.clamp(_body_up(env, body_name, asset_cfg), 0.0, 1.0)


def stand_up_torso_reward(env, target_height, floor_height=0.1, body_name="torso_link", asset_cfg=_ROBOT):
  """Height ramp counted only as much as the TORSO is upright (squared)."""
  return stand_up_height_reward(env, target_height, floor_height, asset_cfg) * \
      torch.clamp(_body_up(env, body_name, asset_cfg), 0.0, 1.0) ** 2


def waist_bend_penalty(env, height=0.65, upright=0.9, asset_cfg=_ROBOT):
  """Once standing: squared waist yaw/roll/pitch angles (0 = straight torso)."""
  a = env.scene[asset_cfg.name]
  idx = [a.joint_names.index(j) for j in ("waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint")]
  return _standing_gate(env, height, upright, asset_cfg) * torch.sum(torch.square(a.data.joint_pos[:, idx]), dim=1)


def stance_reward(env, width=0.24, width_std=0.08, split_std=0.08, height=0.65, upright=0.9, asset_cfg=_ROBOT):
  """Once standing: feet side by side at a normal width (in the pelvis yaw frame)."""
  from mjlab.utils.lab_api.math import quat_apply_inverse, yaw_quat
  a = env.scene[asset_cfg.name]
  lf = a.data.body_link_pos_w[:, a.body_names.index("left_ankle_roll_link")]
  rf = a.data.body_link_pos_w[:, a.body_names.index("right_ankle_roll_link")]
  d = quat_apply_inverse(yaw_quat(a.data.root_link_quat_w), lf - rf)
  r = torch.exp(-torch.square((d[:, 1].abs() - width) / width_std)) * torch.exp(-torch.square(d[:, 0] / split_std))
  return _standing_gate(env, height, upright, asset_cfg) * r


# --- v7 (ours): canonical standing TEMPLATE ------------------------------------------------------------------------
# Template = mjlab G1 KNEES_BENT_KEYFRAME (default standing pose): positions of shoulders, knees, ankles, wrists
# relative to the ankle midpoint, in the pelvis yaw frame (rl/getup/stand_template.npz, built by
# rl/make_stand_template.py; the pelvis itself is one of the bodies, so pelvis height/offset over the feet count).
# A whole-body task-space match: a leaning torso, a split or wide stance, bent/straight knees and flailing arms all
# show up directly, and moving the whole body towards the template is a balanced move (unlike forcing one joint).

_TEMPLATE = {}


def _template(env, asset_cfg, name="stand_template"):
  key = (id(env), name)
  if key not in _TEMPLATE:
    import numpy as np
    from pathlib import Path
    t = np.load(Path(__file__).resolve().parent / f"{name}.npz")
    a = env.scene[asset_cfg.name]
    idx = [a.body_names.index(str(b)) for b in t["bodies"]]
    _TEMPLATE[key] = (idx, torch.tensor(t["rel_pos"], dtype=torch.float32, device=env.device), float(t["pelvis_z"]))
  return _TEMPLATE[key]


def template_rel(env, asset_cfg=_ROBOT, name="stand_template"):
  """Key-body positions relative to the ankle midpoint, in the pelvis yaw frame (same convention as the template)."""
  from mjlab.utils.lab_api.math import quat_apply_inverse, yaw_quat
  a = env.scene[asset_cfg.name]
  idx, tmpl, _ = _template(env, asset_cfg, name)
  bp = a.data.body_link_pos_w
  origin = (bp[:, a.body_names.index("left_ankle_roll_link")] + bp[:, a.body_names.index("right_ankle_roll_link")]) / 2
  rel = bp[:, idx] - origin[:, None, :]
  yq = yaw_quat(a.data.root_link_quat_w)[:, None, :].expand(-1, len(idx), -1)
  return quat_apply_inverse(yq.reshape(-1, 4), rel.reshape(-1, 3)).reshape(-1, len(idx), 3), tmpl


def tilt_rad(env, body, asset_cfg=_ROBOT):
  """Angle (rad) between a body's z axis and world up (the template has pelvis and torso exactly upright)."""
  from mjlab.utils.lab_api.math import quat_apply_inverse
  a = env.scene[asset_cfg.name]
  q = a.data.root_link_quat_w if body == "pelvis" else a.data.body_link_quat_w[:, a.body_names.index(body)]
  g = torch.tensor([0.0, 0.0, -1.0], device=env.device).expand(q.shape[0], 3)
  return torch.acos(torch.clamp(-quat_apply_inverse(q, g)[:, 2], -1.0, 1.0))


def stand_template_reward(env, std=0.06, ang_std=0.35, min_height=0.55, asset_cfg=_ROBOT):
  """exp(-[mean squared key-body distance to the standing template / std^2 + (pelvis tilt^2 + torso tilt^2) /
  ang_std^2]), once the pelvis is above min_height (so it also shapes the last part of rising).
  The tilt terms are needed: v6c leans its pelvis 23 deg and counter-bends the waist, which leaves the key bodies only
  ~6 cm off the template but looks clearly crooked."""
  a = env.scene[asset_cfg.name]
  rel, tmpl = template_rel(env, asset_cfg)
  pel = a.data.root_link_pos_w
  err = torch.mean(torch.sum(torch.square(rel - tmpl[None]), dim=-1), dim=1) / std**2
  err = err + (tilt_rad(env, "pelvis", asset_cfg) ** 2 + tilt_rad(env, "torso_link", asset_cfg) ** 2) / ang_std**2
  gate = (pel[:, 2] - env.scene.env_origins[:, 2] > min_height).float()
  return gate * torch.exp(-err)


def waist_limit_penalty(env, free=0.15, min_height=0.55, asset_cfg=_ROBOT):
  """v7b: squared excess of |waist roll| and |waist pitch| over `free` rad, once the pelvis is above min_height
  (height gate only: the v6c-style gate also needs the pelvis upright, so a robot leaning >26 deg escaped it).
  Measured v7 habit: started exactly in the template, the policy drives waist pitch to its limit (0.55 rad) within
  0.2 s and tilts the pelvis 20 deg backwards to compensate - a reflex left over from the get-up motion."""
  a = env.scene[asset_cfg.name]
  idx = [a.joint_names.index(j) for j in ("waist_roll_joint", "waist_pitch_joint")]
  excess = torch.clamp(a.data.joint_pos[:, idx].abs() - free, min=0.0)
  gate = (a.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2] > min_height).float()
  return gate * torch.sum(torch.square(excess), dim=1)


def _episode_time(env):
  """Time since reset, shifted per env by _getup_t0 (set by reset_root_state_mixed): 0 for lying starts, the
  schedule time of the squat height for squat starts (RSI), 100 s for standing starts (all schedules/gates done)."""
  t = env.episode_length_buf.float() * env.step_dt
  t0 = getattr(env, "_getup_t0", None)
  return t if t0 is None else t + t0


def _stand_start(env):
  s = getattr(env, "_getup_stand_start", None)
  return s if s is not None else torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)


def stand_up_scheduled_reward(env, target_height=0.76, floor_height=0.1, duration=2.5, delay=0.5, floor=0.2,
                              tol=0.03, body_name="torso_link", asset_cfg=_ROBOT):
  """v7d: stand_up_torso_reward, but the height counted is capped at the rising schedule (see rise_schedule_penalty),
  so getting up faster than the schedule earns nothing extra (envs that started standing are not capped)."""
  t = _episode_time(env)
  h_cap = floor + (target_height - floor) * torch.clamp((t - delay) / duration, 0.0, 1.0) + tol
  h_cap = torch.where(_stand_start(env), torch.full_like(h_cap, 10.0), h_cap)
  z = env.scene[asset_cfg.name].data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  ramp = torch.clamp((torch.minimum(z, h_cap) - floor_height) / (target_height - floor_height), 0.0, 1.0)
  return ramp * torch.clamp(_body_up(env, body_name, asset_cfg), 0.0, 1.0) ** 2


def time_gated_reward(env, inner, t_min=2.5, inner_params=None):
  """v7d: `inner` reward paid only from t_min s after reset for episodes that started lying down (always for envs that
  started standing). Used on the standing-quality terms, which otherwise pay ~15/s more for every second the robot
  stands earlier - v7c (schedule penalty only) still stood up in ~1.6 s."""
  r = inner(env, **(inner_params or {}))
  return r * ((_episode_time(env) >= t_min) | _stand_start(env)).float()


def rise_schedule_penalty(env, duration=2.5, delay=0.3, floor=0.2, target=0.76, tol=0.05, linear=0.0,
                          asset_cfg=_ROBOT):
  """v7c: squared height of the pelvis ABOVE a slow rising schedule h_ref(t) = floor -> target linearly over
  `duration` s after `delay` s (t = time since reset; envs that started standing are exempt).
  Being below the schedule is free, so rolling over first is fine; only rushing up is penalised. Measured v7: stood up
  in 0.6-0.9 s with a median peak pelvis speed of 1.3 m/s, because every second spent standing earns the stand-up and
  template rewards, which outweighed the (soft, per-step) vertical speed penalty."""
  t = _episode_time(env)
  h_ref = floor + (target - floor) * torch.clamp((t - delay) / duration, 0.0, 1.0)
  z = env.scene[asset_cfg.name].data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  excess = torch.clamp(z - h_ref - tol, min=0.0)
  stand_start = getattr(env, "_getup_stand_start", None)
  if stand_start is not None:
    excess = excess * (~stand_start).float()
  return torch.square(excess) + linear * excess


def joint_speed_cap_penalty(env, max_speed=5.0, asset_cfg=_ROBOT):
  """v7e: sum over joints of the squared joint speed above max_speed (rad/s). The l2 joint_vel / joint_acc terms are
  too weak to stop single-joint snaps: v7c (after the reset transient) peaks at ~16 rad/s on the hip yaw / hip pitch /
  elbow joints, ~730 rad/s^2, while human-like get-ups stay at a few rad/s."""
  qd = env.scene[asset_cfg.name].data.joint_vel
  return torch.sum(torch.square(torch.clamp(qd.abs() - max_speed, min=0.0)), dim=1)


def feet_spread_penalty(env, max_dist=0.45, min_height=0.2, ramp_height=None, asset_cfg=_ROBOT):
  """v7f: squared horizontal ankle-to-ankle distance above max_dist (m), once the pelvis is off the floor
  (> min_height). Measured v7e: the feet are 0.86 m apart (median peak; near a split) while the pelvis rises through
  0.25-0.70 m; a human-like get-up keeps the feet roughly under the hips (kneel / squat, then stand).
  ramp_height (harness round 4+): the gate ramps linearly from 0 at min_height to 1 at ramp_height instead of
  switching on at once - the step gate made a reward cliff at 0.2 m and round 3 got stuck sitting at 0.17 m with the
  legs wide open (rising past 0.2 m cost ~24/s at once)."""
  a = env.scene[asset_cfg.name]
  bp = a.data.body_link_pos_w
  d = torch.norm(bp[:, a.body_names.index("left_ankle_roll_link"), :2] -
                 bp[:, a.body_names.index("right_ankle_roll_link"), :2], dim=1)
  z = a.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  if ramp_height is None:
    gate = (z > min_height).float()
  else:
    gate = torch.clamp((z - min_height) / (ramp_height - min_height), 0.0, 1.0)
  return gate * torch.square(torch.clamp(d - max_dist, min=0.0))


def floor_stall_penalty(env, t_min=3.5, height=0.4, asset_cfg=_ROBOT):
  """Harness round 4+: 1 per second while the pelvis is still below `height` after the episode clock passed t_min
  (sitting / lying around instead of getting up; also after being pushed over). Round 3 sat at 0.17 m for 10 s."""
  z = env.scene[asset_cfg.name].data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  return ((_episode_time(env) >= t_min) & (z < height)).float()


def squat_template_reward(env, std=0.08, min_height=0.3, max_height=0.62, t_max=None, asset_cfg=_ROBOT):
  """v8: human-like get-up passes through a squat. exp(-mean squared key-body distance to the deep-squat template
  (rl/getup/squat_template.npz: knee 2.0, ankle -0.8, hip -1.2, waist pitch 0.5, arms forward; feet flat and side by
  side, CoM 5 cm in front of the ankles, pelvis 0.49 m) / std^2), paid while the pelvis is between min_height and
  max_height in episodes that started lying down. v7f instead rises through a kneeling lunge (feet 0.68 m apart)."""
  a = env.scene[asset_cfg.name]
  rel, tmpl = template_rel(env, asset_cfg, "squat_template")
  err = torch.mean(torch.sum(torch.square(rel - tmpl[None]), dim=-1), dim=1)
  z = a.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  gate = (z > min_height) & (z < max_height) & ~_stand_start(env)
  if t_max is not None:
    # harness round 6+: the squat is a waypoint, not a place to stay - paid only while the rising schedule is
    # still running (episode clock < t_max). Round 6 (w_squat 16.9) learned to squat for the whole episode.
    gate = gate & (_episode_time(env) < t_max)
  return gate.float() * torch.exp(-err / std**2)


# --- v9 (ours): no stomping / balance stepping ----------------------------------------------------------------------
# Measured (v7f final, 64 falls): 6.5 foot touchdowns while rising, then ~3 more steps after standing with 0.27 m of
# foot travel; peak foot contact force 533 N median (robot weight ~340 N), up to 1000 N.

def _feet_ids(a):
  return [a.body_names.index("left_ankle_roll_link"), a.body_names.index("right_ankle_roll_link")]


def push_and_mark(env, env_ids, velocity_range, asset_cfg=_ROBOT):
  """The training push (mjlab push_by_setting_velocity) + remember the step of the last push per env, so the
  no-stepping penalty can allow catch steps right after a push (and only then)."""
  from mjlab.envs import mdp as envs_mdp
  envs_mdp.push_by_setting_velocity(env, env_ids, velocity_range, asset_cfg)
  if not hasattr(env, "_getup_push_step"):
    env._getup_push_step = torch.full((env.num_envs,), -10**6, dtype=torch.long, device=env.device)
  ids = torch.arange(env.num_envs, device=env.device) if env_ids is None else env_ids.long()
  env._getup_push_step[ids] = env.episode_length_buf[ids].long()


def _since_push(env):
  """Seconds since the last training push in this episode (large if none)."""
  ps = getattr(env, "_getup_push_step", None)
  if ps is None:
    return torch.full((env.num_envs,), 1e6, device=env.device)
  d = env.episode_length_buf.long() - ps
  return torch.where(d >= 0, d.float() * env.step_dt, torch.full_like(d, 10**6).float())


def feet_motion_penalty(env, phase="stand", t_min=2.5, min_height=0.3, max_body_speed=None, push_grace=None,
                        time_only=False, asset_cfg=_ROBOT):
  """Sum of the two feet's speeds (m/s). phase 'stand': once the episode clock passed t_min (standing starts always)
  and the pelvis is upright above 0.65 m - planted feet, no balance stepping. phase 'rise': pelvis above min_height
  and before that - fewer, calmer foot repositionings while getting up.
  max_body_speed (harness round 4+, stand phase): only while the pelvis moves slower than this (m/s) horizontally,
  i.e. stepping without a reason. Training has random pushes; stepping to catch a push is fine, and penalising it
  cost ~10.6/s in round 2 (half of the standing reward)."""
  a = env.scene[asset_cfg.name]
  v = a.data.body_link_lin_vel_w[:, _feet_ids(a)].norm(dim=-1).sum(dim=1)
  z = a.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  if phase == "stand" and time_only:  # round 6b+: see _calm_standing - no standing-state gate to escape through
    standing = (_episode_time(env) >= t_min) & (z > 0.4)
  else:
    standing = (_episode_time(env) >= t_min) & (z > 0.65) & (pelvis_up(env, asset_cfg) > 0.9)
  if phase == "stand" and max_body_speed is not None:
    standing = standing & (a.data.root_link_lin_vel_w[:, :2].norm(dim=-1) < max_body_speed)
  if phase == "stand" and push_grace is not None:
    # round 5+: the body-speed gate leaked (a stepping robot moves its pelvis > 0.15 m/s and switched the penalty
    # off itself: round 4 foot travel after standing 0.11 m) -> allow steps only within push_grace s after a push
    standing = standing & (_since_push(env) > push_grace)
  gate = standing if phase == "stand" else ((z > min_height) & ~standing)
  return v * gate.float()


def _calm_standing(env, t_min, push_grace, time_only=False, asset_cfg=_ROBOT):
  """Gate of the stillness penalties. time_only (harness round 6b+): only the episode clock (and the push grace)
  plus 'not fallen' (pelvis > 0.4 m) - NOT 'standing tall'. With a standing-state gate the policy escaped every
  stillness penalty by not standing: round 6 crouched at 0.55-0.6 m, just under the 0.65 m standing gate."""
  a = env.scene[asset_cfg.name]
  z = a.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  if time_only:
    g = (_episode_time(env) >= t_min) & (z > 0.4)
  else:
    g = (_episode_time(env) >= t_min) & (z > 0.65) & (pelvis_up(env, asset_cfg) > 0.9)
  return g & (_since_push(env) > push_grace) if push_grace is not None else g


def torso_still_penalty(env, t_min=2.5, push_grace=1.0, w_ang=0.25, time_only=False, asset_cfg=_ROBOT):
  """Harness round 6+: once calmly standing, torso horizontal speed (m/s) + w_ang * torso angular speed (rad/s).
  Measured round 4 (standing start): the upper body sways 4.3 cm fore-aft / 3.5 cm sideways peak-to-peak at
  ~0.7 Hz (torso angular speed RMS 0.23 rad/s) - slow enough that the action-rate / joint-acc terms ignore it."""
  a = env.scene[asset_cfg.name]
  i_t = a.body_names.index("torso_link")
  v = a.data.body_link_lin_vel_w[:, i_t, :2].norm(dim=-1)
  w = a.data.body_link_ang_vel_w[:, i_t].norm(dim=-1)
  return (v + w_ang * w) * _calm_standing(env, t_min, push_grace, time_only, asset_cfg).float()


def arm_still_penalty(env, t_min=2.5, push_grace=1.0, time_only=False, asset_cfg=_ROBOT):
  """Harness round 6+: once calmly standing, sum of squared arm joint speeds (shoulder / elbow / wrist; round 4
  waved wrists and shoulders by ~4 deg at the sway frequency)."""
  a = env.scene[asset_cfg.name]
  if not hasattr(env, "_getup_arm_ids"):
    env._getup_arm_ids = [j for j, nm in enumerate(a.joint_names)
                          if any(s in nm for s in ("shoulder", "elbow", "wrist"))]
  qd = a.data.joint_vel[:, env._getup_arm_ids]
  return torch.sum(torch.square(qd), dim=1) * _calm_standing(env, t_min, push_grace, time_only, asset_cfg).float()


def stillness_bonus(env, t_min=2.5, push_grace=1.0, sigma_v=0.05, sigma_w=0.3, sigma_arm=1.0, asset_cfg=_ROBOT):
  """Harness round 6d+: POSITIVE bounded reward for standing still, paid only while standing tall (pelvis > 0.65 m,
  upright, past t_min, not just pushed): mean of exp(-(torso horizontal speed/sigma_v)^2),
  exp(-(torso angular speed/sigma_w)^2) and exp(-(sum of squared arm joint speeds)/sigma_arm^2).
  Replaces the torso_still / arm_still penalties: every penalty version (gated on standing, on the clock, on
  'not fallen') was escaped by not standing (rounds 6a-6c: crouching at 0.55 m, then lying down). A bonus that only
  exists while standing can never be escaped by leaving the stance."""
  a = env.scene[asset_cfg.name]
  i_t = a.body_names.index("torso_link")
  v = a.data.body_link_lin_vel_w[:, i_t, :2].norm(dim=-1)
  w = a.data.body_link_ang_vel_w[:, i_t].norm(dim=-1)
  if not hasattr(env, "_getup_arm_ids"):
    env._getup_arm_ids = [j for j, nm in enumerate(a.joint_names)
                          if any(s in nm for s in ("shoulder", "elbow", "wrist"))]
  arm = torch.sum(torch.square(a.data.joint_vel[:, env._getup_arm_ids]), dim=1)
  r = (torch.exp(-torch.square(v / sigma_v)) + torch.exp(-torch.square(w / sigma_w)) +
       torch.exp(-arm / sigma_arm**2)) / 3.0
  return r * _calm_standing(env, t_min, push_grace, False, asset_cfg).float()


def foot_impact_penalty(env, sensor_name="feet_ground_contact", max_force=450.0, scale=100.0):
  """Sum over feet of ((contact force - max_force) / scale)^2 above max_force (N): stomping impacts."""
  f = env.scene[sensor_name].data.force
  f = f.reshape(f.shape[0], -1, 3).norm(dim=-1)
  return torch.sum(torch.square(torch.clamp(f - max_force, min=0.0) / scale), dim=1)


def reset_root_state_mixed(env, env_ids, stand_prob=0.25, stand_height=0.76, height_range=(0.08, 0.15),
                           yaw_range=(-3.14, 3.14), asset_cfg=_ROBOT, pose=None, pose_extra=(0.0, 0.0, 0.0, 0.0),
                           true_supine=False, squat_prob=0.0, squat_height=0.50, squat_t0=0.0):
  """Like reset_root_state_lying_down, but a fraction stand_prob of the envs starts STANDING upright at the template
  pelvis height (joints come from the reset_robot_joints event: default pose + noise), so the policy experiences
  holding the canonical stance instead of only ever reaching standing through its own get-up habit.
  v8 (RSI): a fraction squat_prob starts in the deep squat of squat_template.npz (root here, joints set by the
  squat_rsi_joints event, which must run after reset_robot_joints); their episode clock starts at squat_t0 (the
  schedule time of the squat height) so the rising schedule and time gates line up."""
  if env_ids is None:
    env_ids = torch.arange(env.num_envs, device=env.device, dtype=torch.int)
  reset_root_state_lying_down(env, env_ids, height_range, yaw_range, asset_cfg, pose=pose, pose_extra=pose_extra,
                              true_supine=true_supine)
  u = torch.rand(len(env_ids), device=env.device)
  standing = u < stand_prob
  squat = (u >= stand_prob) & (u < stand_prob + squat_prob)
  for name, dtype in (("_getup_stand_start", torch.bool), ("_getup_kind", torch.long), ("_getup_t0", torch.float)):
    if not hasattr(env, name):
      setattr(env, name, torch.zeros(env.num_envs, dtype=dtype, device=env.device))
  ids_l = env_ids.long()
  env._getup_stand_start[ids_l] = standing
  env._getup_kind[ids_l] = standing.long() + 2 * squat.long()
  env._getup_t0[ids_l] = 100.0 * standing.float() + squat_t0 * squat.float()
  asset: Entity = env.scene[asset_cfg.name]
  for mask, height in ((standing, stand_height), (squat, squat_height)):
    if mask.any():
      ids = env_ids[mask]
      n = len(ids)
      yaw = sample_uniform(yaw_range[0], yaw_range[1], (n,), env.device)
      quat = quat_from_euler_xyz(torch.zeros(n, device=env.device), torch.zeros(n, device=env.device), yaw)
      pos = env.scene.env_origins[ids].clone()
      pos[:, 2] += height
      asset.write_root_link_pose_to_sim(torch.cat([pos, quat], dim=-1), env_ids=ids)
      asset.write_root_link_velocity_to_sim(torch.zeros(n, 6, device=env.device), env_ids=ids)


def squat_rsi_joints(env, env_ids, noise=0.05, asset_cfg=_ROBOT):
  """v8 RSI: joints of the squat-start envs (kind 2) set to the squat template's keyframe (+ small noise)."""
  kind = getattr(env, "_getup_kind", None)
  if kind is None:
    return
  if env_ids is None:
    env_ids = torch.arange(env.num_envs, device=env.device, dtype=torch.int)
  ids = env_ids[kind[env_ids.long()] == 2]
  if len(ids) == 0:
    return
  import numpy as np
  from pathlib import Path
  knee, ankle, waist, shoulder = np.load(Path(__file__).resolve().parent / "squat_template.npz")["joints"].tolist()
  vals = {"hip_pitch": -(knee + ankle), "knee": knee, "ankle_pitch": ankle, "waist_pitch": waist,
          "shoulder_pitch": shoulder, "elbow": 0.6}
  a: Entity = env.scene[asset_cfg.name]
  q = a.data.default_joint_pos[ids.long()].clone()
  for j, name in enumerate(a.joint_names):
    for k, v in vals.items():
      if name.endswith(k + "_joint"):
        q[:, j] = v
  q += sample_uniform(-noise, noise, q.shape, env.device)
  lim = a.data.soft_joint_pos_limits[ids.long()]
  q = q.clamp(lim[..., 0], lim[..., 1])
  a.write_joint_state_to_sim(q, torch.zeros_like(q), env_ids=ids)


def feet_planted_reward(env, sensor_name="feet_ground_contact", height=0.65, upright=0.9, asset_cfg=_ROBOT):
  """Once standing: both feet on the ground (no hopping / single-foot balancing)."""
  found = env.scene[sensor_name].data.found
  both = (found.reshape(found.shape[0], -1) > 0).all(dim=1).float()
  return _standing_gate(env, height, upright, asset_cfg) * both
