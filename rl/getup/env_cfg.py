"""G1 get-up env + PPO config (adapted from chaoticcuriosity-io/g1-humanoid-rl, MIT, recovery-task/config/g1)."""
from __future__ import annotations

from mjlab.managers.event_manager import EventTermCfg
from mjlab.managers.reward_manager import RewardTermCfg
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.tasks.velocity.config.g1.env_cfgs import unitree_g1_flat_env_cfg
from mjlab.tasks.velocity.config.g1.rl_cfg import unitree_g1_ppo_runner_cfg
from mjlab.tasks.velocity.mdp import UniformVelocityCommandCfg

from .mdp import reset_root_state_lying_down, stand_up_upright_reward, upright_signed_reward


def unitree_g1_recovery_env_cfg(play: bool = False):
  cfg = unitree_g1_flat_env_cfg(play=play)
  twist = cfg.commands["twist"]
  assert isinstance(twist, UniformVelocityCommandCfg)
  twist.ranges.lin_vel_x = (0.0, 0.0)
  twist.ranges.lin_vel_y = (0.0, 0.0)
  twist.ranges.ang_vel_z = (0.0, 0.0)
  twist.rel_standing_envs = 1.0
  cfg.events["reset_base"] = EventTermCfg(
    func=reset_root_state_lying_down, mode="reset",
    params={"height_range": (0.08, 0.15), "yaw_range": (-3.14, 3.14), "asset_cfg": SceneEntityCfg("robot")})
  cfg.events["reset_robot_joints"].params["position_range"] = (-0.2, 0.2)
  cfg.terminations.pop("fell_over")
  cfg.terminations.pop("out_of_terrain_bounds", None)
  for r in ("air_time", "foot_clearance", "foot_swing_height", "foot_slip", "soft_landing",
            "track_linear_velocity", "track_angular_velocity"):
    cfg.rewards.pop(r, None)
  # v5 (ours): signed uprightness + height counted only when upright (see mdp.py for the inverted-pose hack)
  cfg.rewards["upright"] = RewardTermCfg(func=upright_signed_reward, weight=2.0,
                                         params={"asset_cfg": SceneEntityCfg("robot")})
  cfg.rewards["action_rate_l2"].weight = -0.03
  cfg.rewards["stand_up"] = RewardTermCfg(
    func=stand_up_upright_reward, weight=10.0,
    params={"target_height": 0.76, "floor_height": 0.1, "asset_cfg": SceneEntityCfg("robot")})
  cfg.curriculum = {}
  return cfg


def unitree_g1_recovery_v6_env_cfg(play: bool = False):
  """v6: slow, physically plausible get-up (see mdp.py v6 section). Builds on v5."""
  from mjlab.envs import mdp as envs_mdp
  from mjlab.sensor import ContactMatch, ContactSensorCfg

  from .mdp import (feet_planted_reward, flight_penalty, overshoot_penalty, rise_speed_penalty,
                    standing_posture_reward)

  cfg = unitree_g1_recovery_env_cfg(play=play)
  # any robot body <-> ground contact, to detect flight
  cfg.scene.sensors = (cfg.scene.sensors or ()) + (ContactSensorCfg(
    name="robot_ground",
    primary=ContactMatch(mode="subtree", pattern=r"^pelvis$", entity="robot"),
    secondary=ContactMatch(mode="body", pattern="terrain"),
    fields=("found", "force"), reduce="netforce", num_slots=1),)
  robot = SceneEntityCfg("robot")
  cfg.rewards.pop("pose", None)  # replaced by the gated standing_posture term
  # no launching / jumping
  cfg.rewards["flight"] = RewardTermCfg(func=flight_penalty, weight=-5.0, params={"sensor_name": "robot_ground"})
  cfg.rewards["overshoot"] = RewardTermCfg(func=overshoot_penalty, weight=-50.0,
                                           params={"max_height": 0.85, "asset_cfg": robot})
  # slow rise
  cfg.rewards["rise_speed"] = RewardTermCfg(func=rise_speed_penalty, weight=-4.0,
                                            params={"max_speed": 0.6, "asset_cfg": robot})
  cfg.rewards["joint_vel"] = RewardTermCfg(func=envs_mdp.joint_vel_l2, weight=-1e-3, params={"asset_cfg": robot})
  cfg.rewards["joint_acc"] = RewardTermCfg(func=envs_mdp.joint_acc_l2, weight=-2.5e-7, params={"asset_cfg": robot})
  cfg.rewards["action_rate_l2"].weight = -0.1
  cfg.rewards["body_ang_vel"].weight = -0.2
  # good final stance
  cfg.rewards["standing_posture"] = RewardTermCfg(func=standing_posture_reward, weight=3.0,
                                                  params={"height": 0.65, "upright": 0.9, "std": 0.25,
                                                          "asset_cfg": robot})
  cfg.rewards["feet_planted"] = RewardTermCfg(func=feet_planted_reward, weight=2.0,
                                              params={"sensor_name": "feet_ground_contact", "height": 0.65,
                                                      "upright": 0.9, "asset_cfg": robot})
  return cfg


def unitree_g1_recovery_v6b_env_cfg(play: bool = False):
  """v6b: v6 with (a) a standing-posture term that actually has gradient (std 0.25 -> 0.6, weight 3 -> 5; v6 sat at
  ~0 because the policy stood 0.76 rad RMS away from the keyframe) and (b) much stronger anti-launch terms
  (flight -5 -> -20, overshoot -50 -> -200, rise speed cap 0.6 -> 0.5 m/s with weight -4 -> -10): in v6 launches were
  rare per step, so their average cost (~0.5/s) was negligible next to the stand-up reward (~9.6/s)."""
  cfg = unitree_g1_recovery_v6_env_cfg(play=play)
  cfg.rewards["standing_posture"].params["std"] = 0.6
  cfg.rewards["standing_posture"].weight = 5.0
  cfg.rewards["flight"].weight = -20.0
  cfg.rewards["overshoot"].weight = -200.0
  cfg.rewards["rise_speed"].params["max_speed"] = 0.5
  cfg.rewards["rise_speed"].weight = -10.0
  return cfg


def unitree_g1_recovery_v6c_env_cfg(play: bool = False):
  """v6c = v6b + upright TORSO (not only pelvis) in both the upright and stand-up terms, straight waist and normal
  stance width once standing. See mdp.py v6c section for the measured failure it fixes."""
  from .mdp import stance_reward, stand_up_torso_reward, torso_upright_reward, waist_bend_penalty
  cfg = unitree_g1_recovery_v6b_env_cfg(play=play)
  robot = SceneEntityCfg("robot")
  cfg.rewards["upright"] = RewardTermCfg(func=torso_upright_reward, weight=2.0,
                                         params={"body_name": "torso_link", "asset_cfg": robot})
  cfg.rewards["stand_up"] = RewardTermCfg(func=stand_up_torso_reward, weight=10.0,
                                          params={"target_height": 0.76, "floor_height": 0.1,
                                                  "body_name": "torso_link", "asset_cfg": robot})
  cfg.rewards["waist_bend"] = RewardTermCfg(func=waist_bend_penalty, weight=-5.0,
                                            params={"height": 0.65, "upright": 0.9, "asset_cfg": robot})
  cfg.rewards["stance"] = RewardTermCfg(func=stance_reward, weight=2.0,
                                        params={"width": 0.24, "width_std": 0.08, "split_std": 0.08,
                                                "height": 0.65, "upright": 0.9, "asset_cfg": robot})
  return cfg


def unitree_g1_recovery_v7_env_cfg(play: bool = False):
  """v7 = v6c + whole-body canonical standing template reward (weight 6) + 25% of episodes start standing in the
  template pose (play mode keeps 0%: evaluation always starts from a fall)."""
  from .mdp import reset_root_state_mixed, stand_template_reward
  cfg = unitree_g1_recovery_v6c_env_cfg(play=play)
  robot = SceneEntityCfg("robot")
  cfg.rewards["stand_template"] = RewardTermCfg(func=stand_template_reward, weight=6.0,
                                                params={"std": 0.06, "ang_std": 0.35, "min_height": 0.55,
                                                        "asset_cfg": robot})
  cfg.events["reset_base"] = EventTermCfg(
    func=reset_root_state_mixed, mode="reset",
    params={"stand_prob": 0.0 if play else 0.25, "stand_height": 0.76, "height_range": (0.08, 0.15),
            "yaw_range": (-3.14, 3.14), "asset_cfg": robot})
  return cfg


def unitree_g1_recovery_v7b_env_cfg(play: bool = False):
  """v7b = v7 + waist joint-limit barrier (gated by height only) + 50% standing starts. v7 matched the template
  key-body positions to 2 cm but kept waist pitch pinned at its limit with the pelvis tilted 20 deg back."""
  from .mdp import waist_limit_penalty
  cfg = unitree_g1_recovery_v7_env_cfg(play=play)
  cfg.rewards["waist_limit"] = RewardTermCfg(func=waist_limit_penalty, weight=-40.0,
                                             params={"free": 0.15, "min_height": 0.55,
                                                     "asset_cfg": SceneEntityCfg("robot")})
  if not play:
    cfg.events["reset_base"].params["stand_prob"] = 0.5
  return cfg


def unitree_g1_recovery_v7c_env_cfg(play: bool = False):
  """v7c = v7b + slow get-up: pelvis must stay under a 2.5 s rising schedule (rise_schedule_penalty) and a stronger
  vertical speed limit (0.5 m/s, w -10 -> 0.4 m/s, w -50). v7 stood up in 0.6-0.9 s, peak pelvis speed ~1.3 m/s."""
  from .mdp import rise_schedule_penalty
  cfg = unitree_g1_recovery_v7b_env_cfg(play=play)
  # weight: standing ~2 s earlier earns ~22/s x 2 s ~ 44 (stand_up + posture terms); with -1000 a v7-style rush
  # (standing at t = 1 s) costs ~100 over the schedule, so rushing no longer pays
  cfg.rewards["rise_schedule"] = RewardTermCfg(func=rise_schedule_penalty, weight=-1000.0,
                                               params={"duration": 2.5, "delay": 0.3, "floor": 0.2, "target": 0.76,
                                                       "tol": 0.05, "asset_cfg": SceneEntityCfg("robot")})
  cfg.rewards["rise_speed"].params["max_speed"] = 0.4
  cfg.rewards["rise_speed"].weight = -50.0
  return cfg


def unitree_g1_recovery_v7d_env_cfg(play: bool = False):
  """v7d = v7c with no payoff for rushing (target 2-3.5 s get-up): schedule reaches standing height at 3.0 s
  (delay 0.5 + 2.5 s, tol 0.03, + linear term), the stand-up height reward is capped at the schedule, and the
  standing-quality terms (posture, template, stance, feet planted) pay only from t = 2.5 s for lying starts.
  v7c measured: perfect stance but median time-to-stand 1.58 s."""
  from .mdp import stand_up_scheduled_reward, time_gated_reward
  cfg = unitree_g1_recovery_v7c_env_cfg(play=play)
  robot = SceneEntityCfg("robot")
  sched = {"duration": 2.5, "delay": 0.5, "floor": 0.2}
  cfg.rewards["rise_schedule"].params.update(sched, tol=0.03, linear=0.1)
  cfg.rewards["stand_up"] = RewardTermCfg(func=stand_up_scheduled_reward, weight=10.0,
                                          params={**sched, "target_height": 0.76, "floor_height": 0.1, "tol": 0.03,
                                                  "body_name": "torso_link", "asset_cfg": robot})
  for name in ("standing_posture", "stand_template", "stance", "feet_planted"):
    term = cfg.rewards[name]
    cfg.rewards[name] = RewardTermCfg(func=time_gated_reward, weight=term.weight,
                                      params={"inner": term.func, "t_min": 2.5, "inner_params": dict(term.params)})
  return cfg


def unitree_g1_recovery_v7e_env_cfg(play: bool = False):
  """v7e = v7d + (a) correct fallen poses: true supine instead of the upstream upside-down pose that was ejected from
  the floor at ~8.6 m/s, +5 cm drop for face-down / sides; (b) smooth joints: joint speed cap 5 rad/s (squared excess,
  w -0.2), joint_acc x10, action_rate x4."""
  from .mdp import joint_speed_cap_penalty
  cfg = unitree_g1_recovery_v7d_env_cfg(play=play)
  cfg.events["reset_base"].params.update(true_supine=True, pose_extra=(0.0, 0.05, 0.05, 0.05))
  cfg.rewards["joint_speed_cap"] = RewardTermCfg(func=joint_speed_cap_penalty, weight=-0.2,
                                                 params={"max_speed": 5.0, "asset_cfg": SceneEntityCfg("robot")})
  cfg.rewards["joint_acc"].weight = -2.5e-6
  cfg.rewards["action_rate_l2"].weight = -0.4
  return cfg


def unitree_g1_recovery_v7f_env_cfg(play: bool = False):
  """v7f = v7e + no leg split while rising: ankle distance above 0.45 m penalised once the pelvis is off the floor
  (v7e: median peak 0.86 m)."""
  from .mdp import feet_spread_penalty
  cfg = unitree_g1_recovery_v7e_env_cfg(play=play)
  cfg.rewards["feet_spread"] = RewardTermCfg(func=feet_spread_penalty, weight=-80.0,
                                             params={"max_dist": 0.45, "min_height": 0.2,
                                                     "asset_cfg": SceneEntityCfg("robot")})
  return cfg


def unitree_g1_recovery_v8_env_cfg(play: bool = False):
  """v8 = v7f + squat transition (human-like lying -> squat -> stand): squat-template reward while the pelvis is at
  0.3-0.62 m (weight 4), and a tighter feet distance limit while rising (0.45 -> 0.35 m)."""
  from .mdp import squat_template_reward
  cfg = unitree_g1_recovery_v7f_env_cfg(play=play)
  cfg.rewards["squat_template"] = RewardTermCfg(func=squat_template_reward, weight=4.0,
                                                params={"std": 0.08, "min_height": 0.3, "max_height": 0.62,
                                                        "asset_cfg": SceneEntityCfg("robot")})
  cfg.rewards["feet_spread"].params["max_dist"] = 0.35
  return cfg


def load_auto_knobs():
  """Knobs of the self-iterating harness (rl/auto/harness.py): rl/auto/default_knobs.json overridden by the JSON in
  $GETUP_KNOBS. sched_* is shared by the rise_schedule penalty, the schedule-capped stand_up reward and t_gate."""
  import json
  import os
  from pathlib import Path
  knobs = json.loads((Path(__file__).resolve().parents[1] / "auto" / "default_knobs.json").read_text())
  path = os.environ.get("GETUP_KNOBS")
  if path and os.path.exists(path):
    with open(path) as f:
      knobs.update(json.load(f))
  return knobs


def unitree_g1_recovery_auto_env_cfg(play: bool = False):
  """Harness task = v8 structure (v7f + squat template + squat RSI) with every tunable weight / threshold taken from
  the knobs JSON, so the harness can adjust the reward between rounds without new code."""
  from .mdp import squat_rsi_joints
  k = load_auto_knobs()
  cfg = unitree_g1_recovery_v8_env_cfg(play=play)
  robot = SceneEntityCfg("robot")
  sched = {"duration": k["sched_duration"], "delay": k["sched_delay"], "floor": 0.2}
  cfg.rewards["rise_schedule"].weight = k["w_rise_schedule"]
  cfg.rewards["rise_schedule"].params.update(sched, tol=k["sched_tol"])
  cfg.rewards["stand_up"].params.update(sched, tol=k["sched_tol"])
  for name in ("standing_posture", "stand_template", "stance", "feet_planted"):
    cfg.rewards[name].params["t_min"] = k["t_gate"]
  cfg.rewards["stand_template"].weight = k["w_stand_template"]
  cfg.rewards["feet_spread"].weight = k["w_feet_spread"]
  cfg.rewards["feet_spread"].params["max_dist"] = k["feet_max_dist"]
  cfg.rewards["squat_template"].weight = k["w_squat"]
  cfg.rewards["squat_template"].params["std"] = k["squat_std"]
  if k.get("squat_time_limit", True):
    cfg.rewards["squat_template"].params["t_max"] = k["sched_delay"] + k["sched_duration"]
  cfg.rewards["joint_speed_cap"].weight = k["w_joint_speed_cap"]
  cfg.rewards["joint_speed_cap"].params["max_speed"] = k["joint_max_speed"]
  squat_z = 0.50
  squat_t0 = k["sched_delay"] + k["sched_duration"] * (squat_z - 0.2) / (0.76 - 0.2)
  cfg.events["reset_base"].params.update(stand_prob=0.0 if play else k["stand_prob"],
                                         squat_prob=0.0 if play else k["squat_prob"],
                                         squat_height=squat_z, squat_t0=squat_t0)
  cfg.events["squat_rsi"] = EventTermCfg(func=squat_rsi_joints, mode="reset",
                                         params={"noise": 0.05, "asset_cfg": robot})
  # v9: no stomping / balance stepping (feet still once standing, calm feet while rising, no hard impacts)
  from .mdp import feet_motion_penalty, foot_impact_penalty
  cfg.rewards["feet_move_stand"] = RewardTermCfg(func=feet_motion_penalty, weight=k["w_feet_move_stand"],
                                                 params={"phase": "stand", "t_min": k["t_gate"],
                                                         "max_body_speed": k["feet_still_body_speed"],
                                                         "push_grace": k["push_grace"], "asset_cfg": robot})
  if "push_robot" in cfg.events:
    from .mdp import push_and_mark
    cfg.events["push_robot"].func = push_and_mark
  # round 6+: still upper body and arms once calmly standing (no slow ~0.7 Hz sway)
  from .mdp import arm_still_penalty, torso_still_penalty
  cfg.rewards["torso_still"] = RewardTermCfg(func=torso_still_penalty, weight=k["w_torso_still"],
                                             params={"t_min": k["t_gate"], "push_grace": k["push_grace"],
                                                     "w_ang": 0.25, "asset_cfg": robot})
  cfg.rewards["arm_still"] = RewardTermCfg(func=arm_still_penalty, weight=k["w_arm_still"],
                                           params={"t_min": k["t_gate"], "push_grace": k["push_grace"],
                                                   "asset_cfg": robot})
  if k.get("w_still_bonus", 0.0):
    # round 6d+: standing still as a positive bonus (see mdp.stillness_bonus)
    from .mdp import stillness_bonus
    # still_sigma_scale (round 9+): the round-8 kernels (0.05 m/s, 0.3 rad/s, 1 (rad/s)^2) were ~0 under the
    # training action noise (still_bonus 0.14 of max 6) - no gradient; widened 3x by default
    s = k.get("still_sigma_scale", 1.0)
    cfg.rewards["still_bonus"] = RewardTermCfg(func=stillness_bonus, weight=k["w_still_bonus"],
                                               params={"t_min": k["t_gate"], "push_grace": k["push_grace"],
                                                       "sigma_v": 0.05 * s, "sigma_w": 0.3 * s,
                                                       "sigma_arm": 1.0 * s, "asset_cfg": robot})
  if k.get("stillness_time_only", False):
    # round 6b+: stillness penalties gated by the clock (schedule end + 0.5 s) instead of 'standing tall', so that
    # not standing up is no way out of them (round 6 crouched just under the 0.65 m standing gate)
    t_still = k["sched_delay"] + k["sched_duration"] + 0.5
    for name in ("feet_move_stand", "torso_still", "arm_still"):
      cfg.rewards[name].params.update(time_only=True, t_min=t_still)
  # round 4+: no reward cliff for the feet-spread term, and sitting around after the schedule is penalised
  from .mdp import floor_stall_penalty
  cfg.rewards["feet_spread"].params["ramp_height"] = k["feet_spread_ramp"]
  cfg.rewards["floor_stall"] = RewardTermCfg(func=floor_stall_penalty, weight=k["w_floor_stall"],
                                             params={"t_min": k["sched_delay"] + k["sched_duration"] + 0.5,
                                                     "height": k["stall_height"], "asset_cfg": robot})
  cfg.rewards["feet_move_rise"] = RewardTermCfg(func=feet_motion_penalty, weight=k["w_feet_move_rise"],
                                                params={"phase": "rise", "t_min": k["t_gate"], "asset_cfg": robot})
  cfg.rewards["foot_impact"] = RewardTermCfg(func=foot_impact_penalty, weight=k["w_foot_impact"],
                                             params={"sensor_name": "feet_ground_contact", "max_force": 450.0})
  return cfg


def unitree_g1_recovery_ppo_runner_cfg():
  cfg = unitree_g1_ppo_runner_cfg()
  cfg.experiment_name = "g1_recovery"
  return cfg
