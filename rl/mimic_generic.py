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


def dyn_base_still(env, labels: str, phases: list, std_v: float = 0.1, std_w: float = 0.3,
                   command_name: str = "motion"):
  """hold the final pose without drifting or rocking (user 2026-10-23, r16: drifted 9.5 cm forward in 5 s, pelvis up
  to 0.26 m/s): 0.5 exp(-|v_xy pelvis| / std_v) + 0.5 exp(-|w torso| / std_w) in `phases`."""
  robot = env.scene["robot"]
  v = robot.data.root_link_lin_vel_w[:, :2].norm(dim=-1)
  w = env.command_manager.get_term(command_name).robot_anchor_ang_vel_w.norm(dim=-1)
  r = 0.5 * torch.exp(-v / std_v) + 0.5 * torch.exp(-w / std_w)
  return phase_gate(env, labels, phases, command_name).float() * r


def dyn_hold_spot(env, labels: str, phases: list, std: float = 0.15, command_name: str = "motion"):
  """hold the final pose ON THE SPOT (generic): in `phases`, exp(-|pelvis xy - xy0| / std), xy0 = the pelvis xy at
  the env's first step inside the phases (per episode). After the main event the global position is not tracked
  (lesson walk-to-reference), and dyn_base_still only penalises speed, so a push made the robot step away and stay
  there (cartwheel_2 r07: robustness failed only by drift > 0.3 m in the 5 s past the reference)."""
  robot = env.scene["robot"]
  xy = robot.data.root_link_pos_w[:, :2]
  g = phase_gate(env, labels, phases, command_name)
  key = ("_spot", id(env))
  if key not in _cache:
    _cache[key] = (torch.zeros_like(xy), torch.zeros(xy.shape[0], dtype=torch.bool, device=xy.device))
  xy0, have = _cache[key]
  have &= env.episode_length_buf > 1          # new episode -> forget the spot
  new = g & ~have
  xy0[new] = xy[new]
  have |= new
  d = (xy - xy0).norm(dim=-1)
  return g.float() * torch.exp(-d / std)


TEMPLATES = ("dyn_joint", "dyn_body", "dyn_quiet", "dyn_sym", "dyn_contact", "dyn_base_still", "dyn_hold_spot")

_below = {}


def term_below_reference(env, labels: str = "", margin: float = 0.12, min_clear: float = 0.05,
                         command_name: str = "motion"):
  """terminate (generic, any skill): a tracked body goes lower than the reference EVER takes it, minus `margin` -
  e.g. head / elbows / shoulders on the floor where the reference supports itself on straight arms (cartwheel_2 r03:
  pelvis, torso, shoulders and elbows ~0.2 m below the reference's own minimum, head and forearms on the floor).
  Thresholds come from the reference (per body: min over all frames of its height - margin); bodies whose threshold
  would be below `min_clear` (the feet / hands that do touch the floor) are not checked. The reference passes by
  construction."""
  cmd = env.command_manager.get_term(command_name)
  key = (id(cmd), margin, min_clear)
  if key not in _below:
    thr = cmd.motion.body_pos_w[:, :, 2].min(0).values - margin
    _below[key] = (thr, thr > min_clear)
  thr, on = _below[key]
  z = cmd.robot_body_pos_w[:, :, 2] - env.scene.env_origins[:, None, 2]
  return ((z < thr[None]) & on[None]).any(-1)


def term_foot_lifted(env, labels: str, phases: list = ("stand",), max_lift: float = 0.05, planted_z: float = 0.06,
                     command_name: str = "motion"):
  """terminate (generic): in still-stance `phases`, a foot the REFERENCE has planted (its ankle below `planted_z`)
  is more than `max_lift` higher than the reference's ankle (cartwheel_2 r04-r05: left foot lifted 10 cm for 15
  steps in the first stand although the reference stands on both feet; the dyn_contact reward at weight 1 did not
  change it). The reference passes by construction."""
  cmd = env.command_manager.get_term(command_name)
  key = ("_ank_cmd", id(cmd))
  if key not in _cache:
    bn = list(cmd.cfg.body_names)
    _cache[key] = [bn.index("left_ankle_roll_link"), bn.index("right_ankle_roll_link")]
  i = _cache[key]
  zr = cmd.body_pos_w[:, i, 2] - env.scene.env_origins[:, None, 2]
  zz = cmd.robot_body_pos_w[:, i, 2] - env.scene.env_origins[:, None, 2]
  bad = ((zr < planted_z) & (zz - zr > max_lift)).any(-1)
  return phase_gate(env, labels, list(phases), command_name) & bad


def add_dyn_rewards(rewards, labels, dyn, family_module=None):
  """dyn: [{"name", "func", "weight", "params"}] from the diagnostic library / the decider; func is looked up in
  this module (generic templates) first, then in the family module (family-specific hand-written terms)."""
  from mjlab.managers.reward_manager import RewardTermCfg
  for d in dyn:
    f = globals().get(d["func"]) or getattr(family_module, d["func"])
    rewards[d["name"]] = RewardTermCfg(func=f, weight=d["weight"], params={"labels": labels, **d["params"]})
  return rewards


def hold_pad_npz(src, dst, extra_s, fps=50.0):
  """Copy a 50 fps reference npz to `dst` with `extra_s` seconds appended that hold its final frame (positions
  copied, velocities zero). Used by every evaluation (user 2026-10-23: playback must run >= 5 s past the reference
  so one can see whether the robot stays stable). Returns (frames before, frames after)."""
  z = dict(np.load(src))
  T = len(z["joint_pos"])
  n = int(round(extra_s * fps))
  for k, v in z.items():
    if k != "fps" and isinstance(v, np.ndarray) and v.ndim > 0 and len(v) == T:
      tail = np.zeros((n,) + v.shape[1:], v.dtype) if "vel" in k else np.repeat(v[-1:], n, axis=0)
      z[k] = np.concatenate([v, tail], 0)
  np.savez(dst, **z)
  return T, T + n


HAND_GEOMS = r"^(left|right)_hand_collision$"


def set_hand_friction(entity_cfg, mu=0.6):
  """Robot-model correction for hand-supported skills: in mjlab's G1 FULL_COLLISION every non-foot geom has condim 1
  (frictionless), so a hand planted on the floor slides freely; the real G1 rubber hands have friction. Hands get
  condim 3, priority 1 and friction mu (feet keep 0.6). First matching pattern wins (mjlab resolve_expr)."""
  import dataclasses
  feet = r"^(left|right)_foot[1-7]_collision$"
  out = []
  for c in entity_cfg.collisions:
    out.append(dataclasses.replace(
      c, condim={feet: 3, HAND_GEOMS: 3, ".*_collision": 1}, priority={feet: 1, HAND_GEOMS: 1},
      friction={feet: (0.6,), HAND_GEOMS: (mu,)}))
  entity_cfg.collisions = tuple(out)


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
