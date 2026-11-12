"""Side-by-side sim2sim video for a tracking skill (first user: cartwheel_r11, README media): left = the mjlab eval
trajectory of the policy (policies/<p>/flip_auto_model_*_record.npz, mujoco_warp on the GPU), right = the native
MuJoCo (CPU) closed-loop rollout of the same policy from the same reference start (native_skill.py's model, observation,
actor and flip_rollout, unchanged). Rendered with native_dance.render_side_by_side (green ghost = reference).
Usage: python video_skill.py --policy cartwheel_r11 --model cartwheel --out ../videos/sim2sim/cartwheel_r11_side_by_side.mp4"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parent / "rl"))  # appended: import only, never shadows
from native_dance import Motion, Policy, render_side_by_side  # noqa: E402
from native_flip import FlipG1, flip_rollout  # noqa: E402
from mimic_generic import hold_pad_npz  # noqa: E402
from native_skill import POST_S  # noqa: E402


def main(a):
  m = mujoco.MjModel.from_binary_path(str(HERE / "models" / f"{a.model}.mjb"))
  info = json.loads((HERE / "models" / f"{a.model}_info.json").read_text())
  g = FlipG1(m, info)
  pdir = HERE.parent / "policies" / a.policy
  pol = Policy(pdir / "policy.pt")
  padded = Path(tempfile.gettempdir()) / f"video_{a.policy}_post.npz"
  hold_pad_npz(pdir / "reference_motion.npz", padded, POST_S)
  mot = Motion(padded)
  traj_n = flip_rollout(g, pol, mot, 0, mot.T - 1)["traj"]
  rec = np.load(next(pdir.glob("flip_auto_model_*_record.npz")), allow_pickle=False)
  bn = [str(x) for x in rec["body_names"]]
  jn = [str(x) for x in rec["joint_names"]]
  # the record's joint order must be the motion's (both are mjlab's); map it onto the native qpos layout
  assert jn == [str(x) for x in info["joint_names"]], "record joint order differs from the exported model's"
  p = bn.index("pelvis")
  traj_m = np.zeros((len(rec["q"]), m.nq))
  traj_m[:, g.rq:g.rq + 3] = rec["bp"][:, p]
  traj_m[:, g.rq + 3:g.rq + 7] = rec["bq"][:, p]
  traj_m[:, g.qadr] = rec["q"]
  n = min(len(traj_m), len(traj_n))
  out = Path(a.out)
  out.parent.mkdir(parents=True, exist_ok=True)
  render_side_by_side(g, mot, 0, traj_m[:n], traj_n[:n], ("mjlab (mujoco_warp, GPU)", "native MuJoCo (CPU)"), out)
  print(f"{a.policy}: {n} steps -> {out}")


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--policy", required=True)
  ap.add_argument("--model", default="cartwheel")
  ap.add_argument("--out", required=True)
  main(ap.parse_args())
