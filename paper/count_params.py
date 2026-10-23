"""Parameter counts of every network in the pipeline (from the actual checkpoint files)."""
import sys
from pathlib import Path

import torch

H = Path.home()


def count_sd(sd, prefix=None):
  return sum(v.numel() for k, v in sd.items() if torch.is_tensor(v) and (prefix is None or k.startswith(prefix)))


def show(name, path, keys=None):
  p = Path(path)
  if not p.exists():
    print(f"{name:<44} (missing: {p})")
    return
  ck = torch.load(p, map_location="cpu", weights_only=False)
  sd = ck
  for k in (keys or []):
    if isinstance(sd, dict) and k in sd:
      sd = sd[k]
  if hasattr(sd, "state_dict"):
    sd = sd.state_dict()
  if not isinstance(sd, dict):
    print(f"{name:<44} (unrecognised format)")
    return
  tot = count_sd(sd)
  extra = ""
  if any(k.startswith("actor") for k in sd):
    extra = f"  actor {count_sd(sd, 'actor') / 1e6:.3f} M, critic {count_sd(sd, 'critic') / 1e6:.3f} M"
  print(f"{name:<44} {tot / 1e6:9.3f} M params  ({p.stat().st_size / 1e6:.1f} MB file){extra}")
  if "actor" in "".join(sd) and "--layers" in sys.argv:
    for k, v in sd.items():
      if k.startswith("actor") and k.endswith("weight"):
        print("   ", k, tuple(v.shape))


show("backflip tracker (round 4 best)", H / "dance_win/policies/backflip_r04_best/policy.pt", ["model_state_dict"])
show("dance tracker sss_bda_v1", H / "dance_win/policies/sss_bda_v1/policy.pt", ["model_state_dict"])
show("get-up policy auto_r08", H / "dance_win/policies/getup_auto_r08/policy.pt", ["model_state_dict"])
show("recogniser RetrieveNet (closed set)", H / "projects/dance/vla/runs/ret_lead0_s0/model.pt", ["model"])
show("veto recogniser OpenNet (open_s6)", H / "projects/dance/vla/runs/open_s6/model.pt", ["model"])
show("YOLOv8n-pose (live 2D keypoints)", H / "dance_win/live/yolov8n-pose.pt", ["model"])
G = H / "projects/GVHMR/inputs/checkpoints"
for p in sorted(G.rglob("*.ckpt")) + sorted(G.rglob("*.pth")) + sorted(G.rglob("*.pt")):
  show(f"GVHMR stack: {p.relative_to(G)}", p, ["state_dict", "model"])
