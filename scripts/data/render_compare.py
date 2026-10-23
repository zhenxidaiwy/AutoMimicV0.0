"""Render several G1 csv variants of one clip side by side (same camera), optionally with the source clip.

Usage (gmr env, MUJOCO_GL=egl): python render_compare.py <clip_id> <variant> [<variant> ...] [--src]
  variant: "raw" (g1.csv) or a suffix like "ground_vlm", "lock_vlm" (g1_<suffix>.csv)
Output: ~/dance_win/data/qa/<clip_id>/compare_<variants>.mp4 ; a red floor line marks z=0 contact.
"""
import argparse
import os

import cv2
import imageio.v2 as imageio
import mujoco
import numpy as np

H = os.path.expanduser("~")
XML = f"{H}/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"


def load(clip, v):
    p = f"{H}/projects/dance/data/g1/{clip}/" + ("g1.csv" if v == "raw" else f"g1_{v}.csv")
    c = np.loadtxt(p, delimiter=",")
    return np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("variants", nargs="+")
    ap.add_argument("--src", action="store_true")
    ap.add_argument("--h", type=int, default=400)
    a = ap.parse_args()
    model = mujoco.MjModel.from_xml_path(XML)
    data = mujoco.MjData(model)
    r = mujoco.Renderer(model, height=a.h, width=a.h)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 2.6, -5.0, 90.0
    qs = [load(a.clip_id, v) for v in a.variants]
    T = min(len(q) for q in qs)
    cap = cv2.VideoCapture(f"{H}/projects/dance/data/clips/{a.clip_id}.mp4") if a.src else None
    out = f"{H}/dance_win/data/qa/{a.clip_id}/compare_{'_'.join(a.variants)}.mp4"
    w = imageio.get_writer(out, fps=30, macro_block_size=1, quality=7)
    look = qs[0][:, :2].mean(axis=0)
    for t in range(T):
        tiles = []
        if cap is not None:
            ok, fr = cap.read()
            if ok:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
                fr = cv2.resize(fr, (int(fr.shape[1] * a.h / fr.shape[0]) // 2 * 2, a.h))
                tiles.append(fr)
        for v, q in zip(a.variants, qs):
            data.qpos[:] = q[t]
            mujoco.mj_forward(model, data)
            cam.lookat[:] = [look[0], look[1], 0.6]
            r.update_scene(data, camera=cam)
            img = r.render().copy()
            cv2.putText(img, v, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(img, f"{t}", (8, a.h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            tiles.append(img)
        w.append_data(np.concatenate(tiles, 1))
    w.close()
    r.close()
    print(out)
