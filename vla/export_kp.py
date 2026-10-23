"""Export per-clip human keypoints for the high-level (watch-the-human) model.

Run in the gvhmr env from ~/projects/GVHMR:  python export_kp.py clip1 clip2 ...
Writes ~/projects/dance/vla/kp/<clip>.npz with
  kp2d_real   (T,17,3)  ViTPose COCO-17 on the real video (pixels x, y, confidence)
  img_wh      (2,)      video width, height
  j3d_world   (T,17,3)  COCO-17 joints from GVHMR global SMPL-X (gravity-aligned, y up, metres)
  j3d_cam     (T,17,3)  COCO-17 joints from GVHMR in-camera SMPL-X
  K           (3,3)     GVHMR camera intrinsics
and prints the reprojection error of j3d_cam vs ViTPose (sanity check, in % of image height).
"""
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path.home() / "projects" / "GVHMR"))
from hmr4d.utils.body_model.smplx_lite import SmplxLiteCoco17  # noqa: E402

if __name__ == "__main__":
    D = Path.home() / "projects" / "dance" / "data"
    out_dir = Path.home() / "projects" / "dance" / "vla" / "kp"
    out_dir.mkdir(parents=True, exist_ok=True)
    model = SmplxLiteCoco17()
    for cid in sys.argv[1:]:
        g = D / "gvhmr" / cid
        pred = torch.load(g / "hmr4d_results.pt", weights_only=False)
        vit = torch.load(g / "preprocess" / "vitpose.pt", weights_only=False).numpy()
        with torch.no_grad():
            pw = {k: v.float() for k, v in pred["smpl_params_global"].items()}
            pc = {k: v.float() for k, v in pred["smpl_params_incam"].items()}
            jw = model(pw["body_pose"], pw["betas"], pw["global_orient"], pw["transl"]).numpy()
            jc = model(pc["body_pose"], pc["betas"], pc["global_orient"], pc["transl"]).numpy()
        K = pred["K_fullimg"][0].numpy()
        import cv2
        cap = cv2.VideoCapture(str(D / "clips" / f"{cid}.mp4"))
        wh = np.array([cap.get(3), cap.get(4)])
        uv = jc @ K.T
        uv = uv[..., :2] / uv[..., 2:3]
        T = min(len(uv), len(vit))
        m = vit[:T, :, 2] > 0.5
        err = np.linalg.norm(uv[:T] - vit[:T, :, :2], axis=-1)[m].mean() / wh[1] * 100
        np.savez(out_dir / f"{cid}.npz", kp2d_real=vit[:T], img_wh=wh, j3d_world=jw[:T], j3d_cam=jc[:T], K=K)
        print(f"{cid:<20} T={T:4d}  reproj err vs ViTPose {err:4.1f}% of image height  "
              f"height span {jw[:, :, 1].max() - jw[:, :, 1].min():.2f} m")
