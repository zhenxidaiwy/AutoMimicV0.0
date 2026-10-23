"""Top-level keys of an rsl_rl checkpoint and parameter counts per state dict."""
import sys

import torch

ck = torch.load(sys.argv[1], map_location="cpu", weights_only=False)
for k, v in ck.items():
  if isinstance(v, dict):
    n = sum(t.numel() for t in v.values() if torch.is_tensor(t))
    shapes = [(kk, tuple(t.shape)) for kk, t in v.items() if torch.is_tensor(t) and kk.endswith("weight")]
    print(k, f"{n / 1e6:.3f} M", shapes[:8])
  else:
    print(k, type(v).__name__)
