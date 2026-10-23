"""Headless GVHMR -> Unitree G1 (29 DoF) retargeting with GMR, plus QA render and metrics.

Usage (gmr env, MUJOCO_GL=egl):
  python retarget_headless.py <hmr4d_results.pt> <out_dir> [--clip <clip.mp4>] [--no_render]
Writes to <out_dir>:
  g1.pkl        GMR format: fps, root_pos, root_rot (xyzw), dof_pos
  g1.csv        unitree_rl_mjlab / BeyondMimic format: root pos(3), root quat xyzw(4), 29 joints; 30 fps
  qa.mp4        side by side: source clip | G1 render (if --clip given)
  metrics.json  foot slide / penetration / joint-limit statistics
"""
import argparse
import json
import os
import pathlib

import numpy as np

GMR_ROOT = pathlib.Path.home() / "projects" / "GMR"
FOOT_BODIES = ("left_ankle_roll_link", "right_ankle_roll_link")


def retarget(pred_file):
    from general_motion_retargeting import GeneralMotionRetargeting as GMR
    from general_motion_retargeting.utils.smpl import load_gvhmr_pred_file, get_gvhmr_data_offline_fast

    smplx_data, body_model, smplx_output, height = load_gvhmr_pred_file(pred_file, GMR_ROOT / "assets" / "body_models")
    frames, fps = get_gvhmr_data_offline_fast(smplx_data, body_model, smplx_output, tgt_fps=30)
    gmr = GMR(actual_human_height=height, src_human="smplx", tgt_robot="unitree_g1")
    qpos = np.array([gmr.retarget(f) for f in frames])
    return qpos, fps, float(height)


def foot_metrics(model, qpos, fps):
    import mujoco

    data = mujoco.MjData(model)
    ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, b) for b in FOOT_BODIES]
    feet = np.zeros((len(qpos), 2, 3))
    for t, q in enumerate(qpos):
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        feet[t] = data.xpos[ids]
    z = feet[..., 2]
    ground = np.percentile(z.min(axis=1), 5)  # robust floor estimate
    vxy = np.linalg.norm(np.diff(feet[..., :2], axis=0), axis=-1) * fps  # (T-1, 2)
    low = (z[1:] - ground) < 0.03  # foot within 3 cm of floor = treated as contact
    lo, hi = model.jnt_range[1:, 0], model.jnt_range[1:, 1]  # skip free joint
    dof = qpos[:, 7:]
    viol = np.maximum(lo - dof, 0) + np.maximum(dof - hi, 0)
    return feet, {
        "frames": int(len(qpos)), "fps": float(fps), "seconds": round(len(qpos) / fps, 2),
        "ankle_floor_z": round(float(ground), 4),
        "ankle_z_min": round(float(z.min()), 4),
        "contact_ratio": round(float(low.mean()), 3),
        "foot_slide_mps_in_contact_mean": round(float(vxy[low].mean()) if low.any() else 0.0, 4),
        "root_z_mean": round(float(qpos[:, 2].mean()), 3), "root_z_min": round(float(qpos[:, 2].min()), 3),
        "root_xy_travel_m": round(float(np.linalg.norm(qpos[-1, :2] - qpos[0, :2])), 3),
        "joint_limit_violation_max_rad": round(float(viol.max()), 4),
    }


def render_qa(model, qpos, fps, clip, out_mp4, h=480):
    import cv2
    import imageio.v2 as imageio
    import mujoco

    data = mujoco.MjData(model)
    r = mujoco.Renderer(model, height=h, width=h)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 3.0, -10.0, 90.0  # robot faces +x; camera looks from +y side-front
    cap = cv2.VideoCapture(clip) if clip else None
    w = imageio.get_writer(out_mp4, fps=fps, macro_block_size=1, quality=7)
    for q in qpos:
        data.qpos[:] = q
        mujoco.mj_forward(model, data)
        cam.lookat[:] = [q[0], q[1], 0.8]
        r.update_scene(data, camera=cam)
        robot = r.render()
        if cap is not None:
            ok, frame = cap.read()
            if ok:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                fw = int(frame.shape[1] * h / frame.shape[0]) // 2 * 2  # libx264 needs even width
                frame = cv2.resize(frame, (fw, h))
                robot = np.concatenate([frame, robot], axis=1)
        w.append_data(robot)
    w.close()
    r.close()  # free the EGL context before interpreter teardown


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pred_file")
    ap.add_argument("out_dir")
    ap.add_argument("--clip", default=None)
    ap.add_argument("--no_render", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    import mujoco
    import pickle

    qpos, fps, height = retarget(a.pred_file)
    model = mujoco.MjModel.from_xml_path(str(GMR_ROOT / "assets" / "unitree_g1" / "g1_mocap_29dof.xml"))
    assert qpos.shape[1] == 7 + 29 and model.nq == 36, (qpos.shape, model.nq)

    root_xyzw = qpos[:, [4, 5, 6, 3]]  # GMR qpos quat is wxyz
    with open(f"{a.out_dir}/g1.pkl", "wb") as f:
        pickle.dump({"fps": fps, "root_pos": qpos[:, :3], "root_rot": root_xyzw, "dof_pos": qpos[:, 7:],
                     "local_body_pos": None, "link_body_list": None}, f)
    np.savetxt(f"{a.out_dir}/g1.csv", np.concatenate([qpos[:, :3], root_xyzw, qpos[:, 7:]], 1).astype(np.float32),
               delimiter=",")
    feet, m = foot_metrics(model, qpos, fps)
    m["human_height_est_m"] = round(height, 3)
    np.save(f"{a.out_dir}/feet_xyz.npy", feet)
    json.dump(m, open(f"{a.out_dir}/metrics.json", "w"), indent=1)
    print(json.dumps(m))
    if not a.no_render:
        render_qa(model, qpos, fps, a.clip, f"{a.out_dir}/qa.mp4")
        print("qa video:", f"{a.out_dir}/qa.mp4")
