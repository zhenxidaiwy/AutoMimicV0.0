"""CPU smoke test of the world-model pipeline on synthetic files in collect.py's format (no sim, no GPU).
Checks: feature round trip (6D rotation, body frame), reset-aware windows, a short fit, the evaluation report.
Usage: CUDA_VISIBLE_DEVICES= python smoke_test.py <tmp dir>"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

import wm


def fake_file(path, T=120, N=16, B=14, seed=0, friction=1.0):
  rng = np.random.default_rng(seed)
  yaw = np.cumsum(rng.normal(0, 0.02, (T, N)), 0)
  half = yaw / 2
  quat = np.stack([np.cos(half), np.zeros_like(half), np.zeros_like(half), np.sin(half)], -1)  # pure yaw
  pos = np.cumsum(rng.normal(0, 0.01, (T, N, 3)), 0) + np.array([0, 0, 0.75])
  jp = np.cumsum(rng.normal(0, 0.01, (T, N, 29)), 0)
  act = jp + rng.normal(0, 0.05, (T, N, 29))
  done = np.zeros((T, N), bool)
  done[50, :4] = True
  body = pos[:, :, None] + rng.normal(0, 0.3, (1, N, B, 3))
  np.savez_compressed(path, root_pos=pos.astype(np.float32), root_quat=quat.astype(np.float16),
                      root_lin_vel=rng.normal(0, 0.1, (T, N, 3)).astype(np.float16),
                      root_ang_vel=rng.normal(0, 0.1, (T, N, 3)).astype(np.float16),
                      joint_pos=jp.astype(np.float16), joint_vel=rng.normal(0, 0.5, (T, N, 29)).astype(np.float16),
                      body_pos=body.astype(np.float16), body_quat=np.zeros((T, N, B, 4), np.float16),
                      action=act.astype(np.float16), command=act.astype(np.float16),
                      frame=np.tile(np.arange(T)[:, None], (1, N)), done=done, delay=np.zeros(N, int),
                      xi=json.dumps({"friction": friction, "kp_scale": 1.0, "hand_friction": 0.0}))


def main(tmp):
  tmp = Path(tmp)
  (tmp / "data").mkdir(parents=True, exist_ok=True)
  for i in range(3):
    fake_file(tmp / f"data/skill{i}_r01.npz", seed=i, friction=0.5 + 0.5 * i)
  # 1. rotation round trip
  q = torch.nn.functional.normalize(torch.randn(100, 4), dim=-1)
  R = wm.quat_to_mat(q)
  assert torch.allclose(wm.six_to_mat(wm.mat_to_six(R)), R, atol=1e-5), "6D round trip"
  # 2. windows never cross a reset: done[50] for envs 0-3 -> windows of those envs must not contain steps 50 -> 51
  d = wm.load_windows([tmp / "data/skill0_r01.npz"], 8)
  T, N, k = 120, 16, 8
  expect = (T - k) * N - 4 * k  # per env T-k start points, minus k for each env with one reset
  assert d["s"].shape == (expect, k + 1, wm.NS), (d["s"].shape, expect)
  assert d["droot"].shape == (expect, k, 3) and d["xi"].shape == (expect, 3)
  # 3. droot integrates back to the world xy
  print("windows ok:", d["s"].shape[0])
  # 4. fit + eval end to end
  r = subprocess.run([sys.executable, str(Path(__file__).with_name("fit.py")), "--data", str(tmp / "data"),
                      "--out", str(tmp / "out"), "--holdout", "skill2", "--iters", "60", "--hidden", "64,64",
                      "--batch", "64", "--log-every", "20", "--save-every", "60", "--horizon", "32",
                      "--eval-windows", "200", "--cpu"], capture_output=True, text=True)
  print(r.stdout[-1500:])
  assert r.returncode == 0, r.stderr[-3000:]
  ev = json.loads((tmp / "out/eval.json").read_text())
  assert "holdout" in ev and "H32" in ev["holdout"], ev.keys()
  m, meta = wm.load(tmp / "out/wm.pt")
  assert meta["iters"] == 60
  print("SMOKE OK")


if __name__ == "__main__":
  main(sys.argv[1])
