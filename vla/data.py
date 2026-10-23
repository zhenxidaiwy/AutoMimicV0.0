"""High-level (watch-the-human) dataset: human keypoint windows -> future robot reference chunk + aux labels.

Per clip (built by build_clip):
  human 30 fps: kp2d (V, T, 17, 3)  view 0 = real ViTPose on the real video, views 1.. = synthetic projections of
                GVHMR 3D joints from perturbed cameras (yaw around the person, distance, height, focal).
  robot 50 fps: joint_pos (T50, 29), torso rot (T50, 3, 3) from the clip's g1_lock_vlm_50fps.npz
  labels 30 fps: dance id, phase id, contact L/R (1 / 0 / -1 ignore)
Samples (make on the fly in the Dataset): window of W human frames ending at t, target = H robot steps starting at
the robot frame aligned with t (+ lead steps for latency compensation).

Feature normalisation (per window): centre on the mid-hip of the LAST frame, scale by the window's median torso
length (mid-shoulder to mid-hip), image y down. Confidence kept as 3rd channel.
Target torso orientation: rot6d of R_yaw(t)^T R(t+k), i.e. roll/pitch absolute, yaw relative to the current yaw.
"""
import json
from pathlib import Path

import numpy as np
import torch
from scipy.spatial.transform import Rotation as Rot

HOME = Path.home()
DS = HOME / "projects/dance/dataset"
KP = HOME / "projects/dance/vla/kp"
TORSO = 15  # torso_link index in the mjlab G1 body order (= motion npz body axis)
PHASES = ["ready", "stand", "prep", "flash", "hold", "recover", "settle", "shake", "other"]
DANCES = {"闪身步": 0, "狗熊哆嗦毛": 1}
TRAIN_CLIPS = ["bda_zhao_sss", "tonyfu_sss_fast", "tonyfu_sss_slow", "tonyfu_sss_single", "street_sss_a",
               "street_sss_b", "street_sss_c", "street_sss_d", "street_sss_e", "bda2_gxdsm_full"]
TEST_CLIPS = ["gym_sss", "hoodie_sss", "bda_ming_gxdsm_a", "bda_ming_gxdsm_b"]  # unseen performers


def rot6d(R):
  return R[..., :, :2].reshape(*R.shape[:-2], 6)


def synth_views(j3d_cam, K, wh, n, rng):
  """Project camera-frame 3D joints from n perturbed cameras. Returns (n, T, 17, 3) pixels + conf=1 (noise added later)."""
  out = []
  pelvis = (j3d_cam[:, 11] + j3d_cam[:, 12]).mean(0) / 2  # mean mid-hip over the clip (camera frame)
  for _ in range(n):
    yaw = np.deg2rad(rng.uniform(-50, 50))
    pitch = np.deg2rad(rng.uniform(-12, 12))
    R = Rot.from_euler("yx", [yaw, pitch]).as_matrix()  # camera y is (approximately) vertical
    p = (j3d_cam - pelvis) @ R.T  # rotate the person around their mean pelvis
    dist = pelvis[2] * rng.uniform(0.7, 1.6)
    p = p + np.array([rng.uniform(-0.3, 0.3), rng.uniform(-0.25, 0.25), dist])
    f = K[0, 0] * rng.uniform(0.7, 1.4)
    uv = p[..., :2] / p[..., 2:3] * f + wh / 2
    out.append(np.concatenate([uv, np.ones((*uv.shape[:-1], 1))], -1))
  return np.stack(out)


def build_clip(cid, n_synth, seed=0, causal=False, source="vit"):
  """causal=True: strictly causal ViTPose keypoints if available. source="yolo": YOLOv8n-pose keypoints (live client),
  source="both": view 0 = ViTPose, view 1 = YOLO, then synthetic views."""
  rng = np.random.default_rng(seed + hash(cid) % 1000)
  f = KP / f"{cid}_causal.npz"
  k = np.load(f if causal and f.exists() else KP / f"{cid}.npz")
  if source == "yolo":
    k = np.load(KP / f"{cid}_yolo.npz")
  views = [k["kp2d_real"]]
  if source == "both":
    yk = np.load(KP / f"{cid}_yolo.npz")["kp2d_real"]
    T0 = min(len(views[0]), len(yk))
    views = [views[0][:T0], yk[:T0]]
  if n_synth:
    views += list(synth_views(k["j3d_cam"], k["K"], k["img_wh"], n_synth, rng))
  kp = np.stack(views).astype(np.float32)  # (V, T, 17, 3)
  m = np.load(DS / cid / "g1_lock_vlm_50fps.npz")
  R = Rot.from_quat(m["body_quat_w"][:, TORSO][:, [1, 2, 3, 0]]).as_matrix()  # wxyz -> xyzw
  ann = json.load(open(DS / cid / "annotation.json", encoding="utf-8"))
  T = kp.shape[1]
  lab = {"dance": np.full(T, DANCES[ann["move"]]),
         "phase": np.array([PHASES.index(p) for p in ann["phase"][:T]]),
         "cL": np.array(ann["contact_L"][:T]), "cR": np.array(ann["contact_R"][:T])}
  return {"id": cid, "kp": kp, "jpos": m["joint_pos"].astype(np.float32), "R": R.astype(np.float32), **lab}


def normalise(win):
  """win (W, 17, 3) pixels -> (W, 17, 3) normalised (x, y, conf)."""
  hip = (win[:, 11, :2] + win[:, 12, :2]) / 2
  sho = (win[:, 5, :2] + win[:, 6, :2]) / 2
  torso = np.median(np.linalg.norm(sho - hip, axis=-1)) + 1e-6
  out = win.copy()
  out[..., :2] = (win[..., :2] - hip[-1]) / torso
  return out


class WindowDataset(torch.utils.data.Dataset):
  def __init__(self, clips, W=30, H=25, lead=0, augment=False, views=None, seed=0):
    self.clips, self.W, self.H, self.lead, self.aug = clips, W, H, lead, augment
    self.rng = np.random.default_rng(seed)
    self.index = [(ci, v, t) for ci, c in enumerate(clips)
                  for v in (range(c["kp"].shape[0]) if views is None else views) for t in range(c["kp"].shape[1])]

  def __len__(self):
    return len(self.index)

  def __getitem__(self, i):
    ci, v, t = self.index[i]
    c = self.clips[ci]
    T = c["kp"].shape[1]
    idx = np.clip(np.arange(t - self.W + 1, t + 1), 0, T - 1)
    win = c["kp"][v, idx].copy()
    if self.aug:
      win = self._augment(win)
    x = normalise(win)
    # robot target: steps r0 .. r0+H-1 at 50 fps, r0 aligned with human frame t (+lead)
    T50 = len(c["jpos"])
    r0 = int(round(t / 30 * 50)) + self.lead
    ridx = np.clip(np.arange(r0, r0 + self.H), 0, T50 - 1)
    Rc = c["R"][min(int(round(t / 30 * 50)), T50 - 1)]
    yaw = np.arctan2(Rc[1, 0], Rc[0, 0])  # z-up world: yaw of the current torso
    Ry = Rot.from_euler("z", yaw).as_matrix().astype(np.float32)
    rel = np.einsum("ij,kjl->kil", Ry.T, c["R"][ridx])
    y = np.concatenate([c["jpos"][ridx], rot6d(rel)], -1)  # (H, 29+6)
    return (torch.from_numpy(x.reshape(self.W, -1)), torch.from_numpy(y.astype(np.float32)),
            torch.tensor(c["dance"][t]), torch.tensor(c["phase"][t]),
            torch.tensor([c["cL"][t], c["cR"][t]], dtype=torch.long))

  def _augment(self, win):
    r = self.rng
    tor = np.median(np.linalg.norm((win[:, 5, :2] + win[:, 6, :2]) / 2 - (win[:, 11, :2] + win[:, 12, :2]) / 2, axis=-1))
    win[..., :2] += r.normal(0, 0.03 * tor, win[..., :2].shape)  # keypoint jitter
    drop = r.random(win.shape[:2]) < 0.05  # random joint dropout
    drop[:, [5, 6, 11, 12]] = False  # shoulders / hips anchor the normalisation
    if r.random() < 0.2:  # knee/ankle occlusion for a stretch of frames
      s = r.integers(0, len(win))
      drop[s:s + r.integers(3, 15), 13:] = True
    win[drop, 2] = 0.0
    win[drop, :2] = win[drop, :2] * 0  # zeroed (model sees conf=0)
    return win
