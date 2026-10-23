"""Parameter counts of the GVHMR checkpoints (run in the gvhmr env)."""
from pathlib import Path

import torch

G = Path.home() / "projects/GVHMR/inputs/checkpoints"
for p in sorted(list(G.rglob("*.ckpt")) + list(G.rglob("*.pth")) + list(G.rglob("*.pt"))):
  try:
    ck = torch.load(p, map_location="cpu", weights_only=False)
  except Exception as e:  # noqa: BLE001
    print(f"{str(p.relative_to(G)):<55} load failed: {type(e).__name__}")
    continue
  sd = ck
  for k in ("state_dict", "model"):
    if isinstance(sd, dict) and k in sd and isinstance(sd[k], dict):
      sd = sd[k]
  if hasattr(sd, "state_dict"):
    sd = sd.state_dict()
  n = sum(v.numel() for v in sd.values() if torch.is_tensor(v)) if isinstance(sd, dict) else 0
  print(f"{str(p.relative_to(G)):<55} {n / 1e6:9.1f} M params  ({p.stat().st_size / 1e6:.0f} MB)")
