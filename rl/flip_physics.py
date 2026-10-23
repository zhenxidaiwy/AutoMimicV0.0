"""Back-of-the-envelope physics of a standing backflip for the G1, with the real model (sim2sim/models/dance.mjb,
the mjlab runtime model) and the poses of the backflip reference (dataset/<clip>/g1_<variant>_50fps.npz + labels).

1. flight time needed: the reference rotates `air_rot` deg while airborne at the tucked inertia -> with angular
   momentum L conserved, t_f = air_rot / omega_air. Done for a range of t_f (human: 0.47 s).
2. vertical: v0 = g t_f / 2, apex rise h = v0^2 / 2g; push stroke d = CoM rise from the crouch bottom to take-off
   (reference poses) -> mean push acceleration a = v0^2 / 2d, push time t_p = 2d / v0, mean ground force
   F = m (g + a), peak ~ pi/2 F (half-sine).
3. joint torques at the crouch-bottom pose for F/2 per foot (static J^T F, gravity of the legs ignored) vs the
   actuator effort limits; mean joint speeds over the push vs the velocity limits; PD damping torque at that speed.
4. rotation: L = I_tuck * omega_air (CoM pitch inertia at the mid-flight pose); during the push the ground force
   must pass behind the CoM by e = L / (F t_p).
Usage (unitree_rl_mjlab env): python flip_physics.py [clip=backflip_3] [variant=ballistic]
"""
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

H = Path.home()
clip = sys.argv[1] if len(sys.argv) > 1 else "backflip_3"
var = sys.argv[2] if len(sys.argv) > 2 else "ballistic"
m_ = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
d_ = mujoco.MjData(m_)
g = 9.81
ref = np.load(H / f"projects/dance/dataset/{clip}/g1_{var}_50fps.npz")
lab = np.load(H / f"projects/dance/dataset/{clip}/labels_50fps.npz")
names = [str(x) for x in lab["phase_names"]]
ph = lab["phase"]
jnames = [m_.joint(i).name for i in range(m_.njnt)]
hinge = [i for i in range(m_.njnt) if m_.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]


def set_pose(f):
  d_.qpos[:3] = ref["body_pos_w"][f, 0]
  d_.qpos[3:7] = ref["body_quat_w"][f, 0]
  d_.qpos[7:7 + len(hinge)] = ref["joint_pos"][f]
  d_.qvel[:] = 0
  mujoco.mj_forward(m_, d_)


PELVIS = mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_BODY, "robot/pelvis")  # body 1 is the terrain
mass = float(m_.body_subtreemass[PELVIS])  # subtree of the free-floating pelvis = whole robot
idx = {n: np.where(ph == names.index(n))[0] for n in ("crouch", "takeoff", "flight", "land")}
t_lo, t_off = idx["crouch"][0], idx["takeoff"][-1] + 1  # take-off = first frame after the takeoff phase
com = []
for f in range(len(ph)):
  set_pose(f)
  com.append(d_.subtree_com[PELVIS].copy())
com = np.array(com)
f_bottom = t_lo + int(np.argmin(com[t_lo:t_off, 2]))
d_stroke = float(com[t_off, 2] - com[f_bottom, 2])
stand_com = float(com[:t_lo, 2].mean())
# reference rotation while airborne and tucked inertia at mid-flight
fl = idx["flight"]
from scipy.spatial.transform import Rotation as R
q = R.from_quat(ref["body_quat_w"][:, 0][:, [1, 2, 3, 0]])
inc = (q[:-1].inv() * q[1:]).as_rotvec()
ax_b = inc[fl[0]:fl[-1]].sum(0)
air_rot = float(np.degrees(np.linalg.norm(ax_b)))
pre_rot = float(np.degrees(np.linalg.norm(inc[t_lo:fl[0]].sum(0))))
mid = fl[len(fl) // 2]
set_pose(mid)
# CoM inertia of the whole robot about the world axis of the flip (pitch), at the tucked mid-flight pose
axis = q[mid].apply(ax_b / np.linalg.norm(ax_b))
I = 0.0
for b in range(PELVIS, m_.nbody):
  mb = m_.body_mass[b]
  R_b = d_.ximat[b].reshape(3, 3)
  Ib = R_b @ np.diag(m_.body_inertia[b]) @ R_b.T
  r = d_.xipos[b] - d_.subtree_com[PELVIS]
  I += axis @ Ib @ axis + mb * (r @ r - (r @ axis) ** 2)
set_pose(t_off - 1)
I_stand = 0.0
for b in range(PELVIS, m_.nbody):
  R_b = d_.ximat[b].reshape(3, 3)
  r = d_.xipos[b] - d_.subtree_com[PELVIS]
  I_stand += axis @ (R_b @ np.diag(m_.body_inertia[b]) @ R_b.T) @ axis + m_.body_mass[b] * (r @ r - (r @ axis) ** 2)

# joint torques at the crouch bottom for F/2 vertical per foot (J^T F, static)
set_pose(f_bottom)
feet = [mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_BODY, n) for n in ("robot/left_ankle_roll_link", "robot/right_ankle_roll_link")]
legj = ["left_hip_pitch_joint", "left_knee_joint", "left_ankle_pitch_joint", "left_hip_roll_joint"]
lim = {"left_hip_pitch_joint": (88, 32), "left_knee_joint": (139, 20), "left_ankle_pitch_joint": (50, 37),
       "left_hip_roll_joint": (139, 20)}
# real G1 spec sheets: knee 90 N.m (base) / 120 N.m (EDU); other joints not published -> sim value
REAL = {"left_knee_joint": "90 (base) / 120 (EDU)"}
kv = {"left_hip_pitch_joint": None, "left_knee_joint": None, "left_ankle_pitch_joint": None, "left_hip_roll_joint": None}
for j in kv:
  a = [i for i in range(m_.nu) if m_.actuator_trnid[i, 0] == mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_JOINT, "robot/" + j)]
  kv[j] = float(-m_.actuator_biasprm[a[0], 2]) if a else None
jacp = np.zeros((3, m_.nv))
mujoco.mj_jacBody(m_, d_, jacp, None, feet[0])
q_bottom = {j: float(d_.qpos[m_.jnt_qposadr[mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_JOINT, "robot/" + j)]]) for j in legj}
set_pose(t_off)
q_off = {j: float(d_.qpos[m_.jnt_qposadr[mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_JOINT, "robot/" + j)]]) for j in legj}

rows = []
for tf in (0.30, 0.35, 0.40, 0.47, 0.55):
  v0 = g * tf / 2
  h = v0 ** 2 / (2 * g)
  a = v0 ** 2 / (2 * d_stroke)
  tp = 2 * d_stroke / v0
  F = mass * (g + a)
  w_air = np.radians(air_rot) / tf
  L = I * w_air
  e = L / (F * tp)
  tau = {}
  for j in legj:
    dof = m_.jnt_dofadr[mujoco.mj_name2id(m_, mujoco.mjtObj.mjOBJ_JOINT, "robot/" + j)]
    t = float(jacp[:, dof] @ np.array([0, 0, F / 2]))
    t_pk = t * np.pi / 2
    speed = abs(q_off[j] - q_bottom[j]) / tp
    tau[j.replace("left_", "").replace("_joint", "")] = {
      "mean_Nm": round(abs(t), 1), "peak_Nm": round(abs(t_pk), 1), "limit_Nm": lim[j][0], "real_G1_limit_Nm": REAL.get(j),
      "mean_speed_rad_s": round(speed, 1), "speed_limit": lim[j][1],
      "pd_damping_at_2x_mean_speed_Nm": round(kv[j] * 2 * speed, 1) if kv[j] else None}
  rows.append({"flight_s": tf, "takeoff_vz_m_s": round(v0, 2), "com_rise_m": round(h, 3), "push_time_s": round(tp, 3),
               "mean_push_acc_g": round(a / g, 2), "mean_ground_force_N": round(F), "bodyweights": round(F / (mass * g), 2),
               "peak_ground_force_N(half-sine)": round(F * np.pi / 2), "omega_air_rad_s": round(w_air, 1),
               "ang_momentum": round(L, 1), "force_offset_behind_com_cm": round(e * 100, 1), "torques_per_leg": tau})
out = {"clip": clip, "variant": var, "mass_kg": round(mass, 2), "stand_com_m": round(stand_com, 3),
       "crouch_bottom_com_m": round(float(com[f_bottom, 2]), 3), "takeoff_com_m": round(float(com[t_off, 2]), 3),
       "push_stroke_m": round(d_stroke, 3), "ref_rotation_before_flight_deg": round(pre_rot, 1),
       "ref_rotation_in_flight_deg": round(air_rot, 1), "I_pitch_tucked_kgm2": round(float(I), 3),
       "I_pitch_extended_kgm2": round(float(I_stand), 3), "per_flight_time": rows}
Path(H / "dance_win/rl/flip_physics.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in out.items() if k != "per_flight_time"}, ensure_ascii=False))
for r in rows:
  t = r["torques_per_leg"]
  print(f"t_f {r['flight_s']:.2f}s v0 {r['takeoff_vz_m_s']} m/s rise {r['com_rise_m']} m push {r['push_time_s']} s "
        f"F {r['mean_ground_force_N']} N ({r['bodyweights']} BW, peak {r['peak_ground_force_N(half-sine)']} N) "
        f"omega {r['omega_air_rad_s']} rad/s offset {r['force_offset_behind_com_cm']} cm | " +
        " ".join(f"{k} {v['mean_Nm']}/{v['peak_Nm']}/{v['limit_Nm']}Nm {v['mean_speed_rad_s']}/{v['speed_limit']}rad/s "
                 f"damp {v['pd_damping_at_2x_mean_speed_Nm']}" for k, v in t.items()))
