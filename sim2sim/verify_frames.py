"""Video check: frame count / fps / size, frames at a few times, per-half motion, and provenance:
 - a FRESH native rollout from frame 0 (native_dance.native_rollout on models/dance.mjb) is compared with
   traj_dance_<clip>.npz['native_0'] (the trajectory the right half was rendered from)
 - the side-by-side video is re-rendered here from (mjlab_0, fresh native) and compared pixel-wise with the
   published video, and also against a re-render with the halves swapped (sanity of the comparison)."""
import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_dance as nd  # noqa: E402

OUT = HERE / "verify_frames"
OUT.mkdir(exist_ok=True)
VID = HERE.parent / "videos" / "sim2sim"
torch.set_num_threads(1)
info = json.loads((HERE / "models" / "dance_info.json").read_text())
m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
g = nd.NativeG1(m, info)


def read(p):
  rd = imageio.get_reader(str(p))
  meta = rd.get_meta_data()
  fr = [np.asarray(f) for f in rd]
  rd.close()
  return fr, meta


res = {}
for clip in ("sss", "gxdsm"):
  tag = nd.CLIPS[clip][0]
  pdir = nd.ROOT / "policies" / tag
  mot = nd.Motion(pdir / "reference_motion.npz")
  pol = nd.Policy(pdir / "policy.pt")
  frames, meta = read(VID / f"{clip}_side_by_side.mp4")
  n = len(frames)
  H, W = frames[0].shape[:2]
  L = np.array([f[:, : W // 2].astype(np.float32) for f in frames[::5]])
  R = np.array([f[:, W // 2:].astype(np.float32) for f in frames[::5]])
  z = np.load(HERE / f"traj_dance_{clip}.npz")
  fresh, _ = nd.native_rollout(g, pol, mot, 0, mot.T - 1)
  ta, tb = z["mjlab_0"], z["native_0"]
  r = dict(frames=n, fps=meta.get("fps"), size=[W, H], duration=meta.get("duration"),
           traj_len_mjlab0=int(ta.shape[0]), traj_len_native0=int(tb.shape[0]), motion_T=mot.T,
           fresh_native_vs_npz_native0_max_abs=float(np.abs(fresh - tb).max()) if fresh.shape == tb.shape else
           f"shape {fresh.shape} vs {tb.shape}",
           npz_native0_vs_mjlab0_max_abs_qpos=float(np.abs(ta - tb).max()),
           npz_native0_vs_mjlab0_pelvis_xy_end_m=float(np.linalg.norm(ta[-1][:2] - tb[-1][:2])),
           mean_abs_frame_diff_left=float(np.mean(np.abs(np.diff(L, axis=0)))),
           mean_abs_frame_diff_right=float(np.mean(np.abs(np.diff(R, axis=0)))))
  # re-render (no labels difference: same function) and compare
  tmp = OUT / f"{clip}_rerender.mp4"
  nd.render_side_by_side(g, mot, 0, ta, fresh, ("mjlab (mujoco_warp 3.5, GPU)", "native MuJoCo 3.5 (CPU)"), tmp)
  rf, _ = read(tmp)
  idx = list(range(0, min(n, len(rf)), 10))
  r["rerender_frames"] = len(rf)
  r["pub_vs_rerender_mae_left"] = float(np.mean([np.abs(frames[i][:, :W // 2].astype(float) -
                                                         rf[i][:, :W // 2].astype(float)).mean() for i in idx]))
  r["pub_vs_rerender_mae_right"] = float(np.mean([np.abs(frames[i][:, W // 2:].astype(float) -
                                                          rf[i][:, W // 2:].astype(float)).mean() for i in idx]))
  r["pub_left_vs_rerender_right_mae"] = float(np.mean([np.abs(frames[i][:, :W // 2].astype(float) -
                                                               rf[i][:, W // 2:].astype(float)).mean() for i in idx]))
  # per-frame divergence: where both halves differ most
  dif = [float(np.abs(frames[i][:, :W // 2].astype(float) - frames[i][:, W // 2:].astype(float))[40:440].mean())
         for i in range(n)]
  r["left_right_body_region_mae_mean"] = float(np.mean(dif))
  r["left_right_body_region_mae_max_frame"] = int(np.argmax(dif))
  tmp.unlink()
  for k in (0, n // 3, 2 * n // 3, n - 1):
    imageio.imwrite(OUT / f"{clip}_f{k:04d}.png", frames[k])
  res[clip] = r
  print(clip, json.dumps(r), flush=True)
(OUT / "video_stats.json").write_text(json.dumps(res, indent=1))
