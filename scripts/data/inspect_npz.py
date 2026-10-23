"""Print keys/shapes and sanity stats of mjlab motion npz files. Usage: python inspect_npz.py <npz> [...]"""
import sys

import numpy as np

if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = np.load(p)
        print(p.split("/")[-1], {k: d[k].shape for k in d.files})
        jp, bp = d["joint_pos"], d["body_pos_w"]
        print(f"  frames {len(jp)} ({len(jp) / 50:.2f}s @50fps) | pelvis z {bp[:, 0, 2].min():.3f}..{bp[:, 0, 2].max():.3f}"
              f" | min body z {bp[:, :, 2].min():.3f} | max |joint_vel| {np.abs(d['joint_vel']).max():.2f} rad/s")
