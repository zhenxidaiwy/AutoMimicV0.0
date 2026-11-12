"""Elbow bend (0 deg = straight arm) of the human (GVHMR SMPL-X joints) vs the retargeted G1 (forward kinematics of
shoulder -> elbow -> wrist bodies), per frame. Two steps because SMPL-X lives in the gvhmr env and MuJoCo in gmr:
  python elbow_check.py smpl <clip>          (gvhmr env) -> data/gvhmr/<clip>/smpl_elbow_bend.npy
  python elbow_check.py g1 <clip> [every=2]  (gmr env)   -> prints SMPL vs G1 (g1.csv and every repaired variant)"""
import sys
from pathlib import Path

import numpy as np

H = Path.home()
mode, clip = sys.argv[1], sys.argv[2]
G = H / f"projects/dance/data/gvhmr/{clip}"


def bend(J, s, e, w):
  a, b = J[:, s] - J[:, e], J[:, w] - J[:, e]
  c = (a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))
  return 180 - np.degrees(np.arccos(np.clip(c, -1, 1)))


if mode == "smpl":
  import smplx
  import torch
  p = torch.load(G / "hmr4d_results.pt", map_location="cpu")["smpl_params_global"]
  n = p["body_pose"].shape[0]
  bm = smplx.create(str(H / "projects/dance/body_models"), model_type="smplx", gender="neutral", use_pca=False,
                    num_betas=10)
  z = lambda k: torch.zeros(n, k)  # noqa: E731
  out = bm(global_orient=p["global_orient"], body_pose=p["body_pose"], betas=p["betas"][:, :10], transl=p["transl"],
           jaw_pose=z(3), leye_pose=z(3), reye_pose=z(3), left_hand_pose=z(45), right_hand_pose=z(45), expression=z(10))
  J = out.joints.detach().numpy()  # SMPL-X: 16/17 shoulders, 18/19 elbows, 20/21 wrists (L/R)
  np.save(G / "smpl_elbow_bend.npy", np.stack([bend(J, 16, 18, 20), bend(J, 17, 19, 21)], 1))
  print("saved", G / "smpl_elbow_bend.npy", n, "frames")
else:
  import mujoco
  every = int(sys.argv[3]) if len(sys.argv) > 3 else 2
  m = mujoco.MjModel.from_xml_path(str(H / "projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"))
  d = mujoco.MjData(m)
  ids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{s}_{b}") for s in ("left", "right")
         for b in ("shoulder_yaw_link", "elbow_link", "wrist_roll_link")]
  sm = np.load(G / "smpl_elbow_bend.npy")
  cols = []
  for v in ("g1", "g1_contact_vlm"):
    f = H / f"projects/dance/data/g1/{clip}/{v}.csv"
    if f.exists():
      c = np.loadtxt(f, delimiter=",")
      q = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)
      P = []
      for x in q:
        d.qpos[:] = x
        mujoco.mj_kinematics(m, d)
        P.append(d.xpos[ids].copy())
      P = np.array(P)
      cols.append((v, bend(P, 0, 1, 2), bend(P, 3, 4, 5), c[:, 7 + 18], c[:, 7 + 25]))
  print("frame  human bend L R | " + " | ".join(f"{v}: bend L R (deg), elbow q L R (rad)" for v, *_ in cols))
  for t in range(0, len(sm), every):
    print(f"{t:5d}  {sm[t, 0]:5.0f} {sm[t, 1]:5.0f}   | " + " | ".join(
      f"{bl[t]:5.0f} {br[t]:5.0f}  {ql[t]:+.2f} {qr[t]:+.2f}" for _, bl, br, ql, qr in cols if t < len(bl)))
