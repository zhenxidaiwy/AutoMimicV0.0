"""L0 (generic) reward / termination building blocks for motion imitation, independent of the motion family.
Family modules (e.g. flip_rewards.py = family 'aerial') import these; the harness instantiates the dyn_* templates
from the diagnostic library (rl/flip_auto/library.py, scope generic / family:<f> / task:<clip>).

Phases come from the clip's own label file (labels_50fps.npz: phase ids + phase_names), so the same templates work
for any vocabulary. Extra pseudo-phase:
  <first phase>_after  e.g. 'stand_after' = frames labelled with the clip's first phase (the rest pose) that come
                       after the main event (the first 'land' frame if the vocabulary has one, otherwise the start of
                       the final contiguous run). Round 9-11 lesson: rest-pose terms must cover these frames.
"""
import numpy as np
import torch

_cache = {}


def label_info(env, labels, command_name="motion"):
  """per-env (phase id, phase names, frames since phase start, frames until phase end, after-event mask)."""
  key = ("label_info", labels, str(env.device))
  if key not in _cache:
    z = np.load(labels)
    ph = z["phase"]
    names = [str(x) for x in z["phase_names"]]
    since = np.zeros(len(ph), np.int64)
    for i in range(1, len(ph)):
      since[i] = since[i - 1] + 1 if ph[i] == ph[i - 1] else 0
    until = np.zeros(len(ph), np.int64)
    for i in range(len(ph) - 2, -1, -1):
      until[i] = until[i + 1] + 1 if ph[i] == ph[i + 1] else 0
    event = event_frame(ph, names)
    d = env.device
    _cache[key] = (torch.tensor(ph, device=d), names, torch.tensor(since, device=d), torch.tensor(until, device=d),
                   event)
  ph, names, since, until, event = _cache[key]
  t = env.command_manager.get_term(command_name).time_steps.clamp(max=len(ph) - 1)
  return ph[t], names, since[t], until[t], (t >= event)


def event_frame(ph, names):
  """first frame of the main event's end: 'land' if labelled, else the start of the final contiguous run."""
  if "land" in names:
    ld = np.where(ph == names.index("land"))[0]
    if len(ld):
      return int(ld[0])
  i = len(ph) - 1
  while i > 0 and ph[i - 1] == ph[-1]:
    i -= 1
  return i


def phase_gate(env, labels, phases, command_name="motion"):
  """bool mask: the env's reference frame is in one of `phases` (label names, or '<rest>_after')."""
  ph, names, _, _, after = label_info(env, labels, command_name)
  g = torch.zeros_like(ph, dtype=torch.bool)
  for p in phases:
    if p.endswith("_after") and p[:-6] in names:
      g |= (ph == names.index(p[:-6])) & after
    elif p in names:
      g |= ph == names.index(p)
  return g


def jidx(env, joints):
  key = ("_j", tuple(joints))
  if key not in _cache:
    names = list(env.scene["robot"].joint_names)
    _cache[key] = [names.index(j) for j in joints]
  return _cache[key]


def ankle_z(env):
  robot = env.scene["robot"]
  if "_ank_g" not in _cache:
    _cache["_ank_g"] = [list(robot.body_names).index(n) for n in ("left_ankle_roll_link", "right_ankle_roll_link")]
  return robot.data.body_link_pos_w[:, _cache["_ank_g"], 2] - env.scene.env_origins[:, None, 2]


# --- generic fix templates (instantiated from the diagnostic library). Lesson (round 8): choose std of the order of
# the current error - exp(-err/std) with err >> std gives no gradient (quant_report section C prints the signal).

def dyn_joint(env, labels: str, joints: list, phases: list, std: float = 0.3, command_name: str = "motion"):
  """joint angles of `joints` close to the reference in `phases`: exp(-mean |q - q_ref| / std)."""
  i = jidx(env, joints)
  e = (env.scene["robot"].data.joint_pos[:, i] - env.command_manager.get_term(command_name).joint_pos[:, i]).abs()
  return phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_body(env, labels: str, bodies: list, phases: list, std: float = 0.1, command_name: str = "motion"):
  """tracked bodies at the reference shape (relative frame) in `phases`: exp(-mean |p - p_ref| / std)."""
  cmd = env.command_manager.get_term(command_name)
  key = ("_b", tuple(bodies))
  if key not in _cache:
    bn = list(cmd.cfg.body_names)
    _cache[key] = [bn.index(b) for b in bodies]
  i = _cache[key]
  e = (cmd.robot_body_pos_w[:, i] - cmd.body_pos_relative_w[:, i]).norm(dim=-1)
  return phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_quiet(env, labels: str, joints: list, phases: list, std: float = 1.0, command_name: str = "motion"):
  """no jitter: joint velocities of `joints` close to the reference's: exp(-mean |dq - dq_ref| / std)."""
  i = jidx(env, joints)
  e = (env.scene["robot"].data.joint_vel[:, i] - env.command_manager.get_term(command_name).joint_vel[:, i]).abs()
  return phase_gate(env, labels, phases, command_name).float() * torch.exp(-e.mean(-1) / std)


def dyn_sym(env, labels: str, base: str, sign: float, phases: list, std: float = 0.2, command_name: str = "motion"):
  """left/right symmetry of joint `base` as symmetric as the reference: exp(-| |qR - s qL| - |qrR - s qrL| | / std)."""
  li, ri = jidx(env, [f"left_{base}_joint", f"right_{base}_joint"])
  q = env.scene["robot"].data.joint_pos
  qr = env.command_manager.get_term(command_name).joint_pos
  e = ((q[:, ri] - sign * q[:, li]).abs() - (qr[:, ri] - sign * qr[:, li]).abs()).abs()
  return phase_gate(env, labels, phases, command_name).float() * torch.exp(-e / std)


def dyn_contact(env, labels: str, foot: int, phases: list, command_name: str = "motion"):
  """foot `foot` (0 left, 1 right) on the floor in `phases`."""
  return phase_gate(env, labels, phases, command_name).float() * (ankle_z(env)[:, foot] < 0.06).float()


TEMPLATES = ("dyn_joint", "dyn_body", "dyn_quiet", "dyn_sym", "dyn_contact")


def add_dyn_rewards(rewards, labels, dyn, family_module=None):
  """dyn: [{"name", "func", "weight", "params"}] from the diagnostic library / the decider; func is looked up in
  this module (generic templates) first, then in the family module (family-specific hand-written terms)."""
  from mjlab.managers.reward_manager import RewardTermCfg
  for d in dyn:
    f = globals().get(d["func"]) or getattr(family_module, d["func"])
    rewards[d["name"]] = RewardTermCfg(func=f, weight=d["weight"], params={"labels": labels, **d["params"]})
  return rewards


# --- real-robot constraints (generic: every skill is trained under them)

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


def _hold_delay_cfg():
  """DelayedActuatorCfg whose actuator does not command 0 rad after a reset. mjlab's delay buffer backfills a reset
  row with the FIRST value appended after the reset, which is an all-zero position target (no action yet), so the
  first `lag` physics steps of every episode drove all joints towards 0 rad (found by the sim2sim agent, r15).
  Fix: for a freshly reset row whose target is all zero, append the current joint position instead (hold pose)."""
  from dataclasses import dataclass

  import torch as _t
  from mjlab.actuator.actuator import ActuatorCmd
  from mjlab.actuator.delayed_actuator import DelayedActuator, DelayedActuatorCfg

  class HoldDelayedActuator(DelayedActuator):
    def compute(self, cmd):
      buf = self._delay_buffers.get("position")
      if buf is not None:
        fresh = buf._buffer._num_pushes == 0
        if bool(_t.any(fresh)):
          zero = cmd.position_target.abs().sum(-1) == 0
          pt = _t.where((fresh & zero)[:, None], cmd.pos, cmd.position_target)
          cmd = ActuatorCmd(position_target=pt, velocity_target=cmd.velocity_target, effort_target=cmd.effort_target,
                            pos=cmd.pos, vel=cmd.vel)
      return super().compute(cmd)

  @dataclass(kw_only=True)
  class HoldDelayedActuatorCfg(DelayedActuatorCfg):
    def build(self, entity, target_ids, target_names):
      return HoldDelayedActuator(self, self.base_cfg.build(entity, target_ids, target_names))

  return HoldDelayedActuatorCfg


def add_action_delay(articulation, max_ms, sim_dt=0.005, hold_prob=0.9):
  """Wrap every actuator so position targets arrive 0..max_ms late (random per env, in physics steps, mostly held;
  hold-pose instead of 0 rad right after a reset). Robustness eval of r14: 20 ms delay -> 70 % success, 40 ms -> 0 %
  (never trained); r15 trained with 0..25 ms -> 99 % at 20 ms."""
  cfg_cls = _hold_delay_cfg()
  lag = int(round(max_ms / 1000.0 / sim_dt))
  articulation.actuators = tuple(cfg_cls(base_cfg=c, delay_target="position", delay_min_lag=0,
                                         delay_max_lag=lag, delay_hold_prob=hold_prob)
                                 for c in articulation.actuators)
  return lag
