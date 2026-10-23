"""Print robot ankle height / horizontal speed over time next to the VLM contact labels.
Usage: python feet_debug.py <clip_id> [step]"""
import json
import os
import sys

import numpy as np

if __name__ == "__main__":
    cid, step = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 6
    H = os.path.expanduser("~")
    f = np.load(f"{H}/projects/dance/data/g1/{cid}/feet_xyz.npy")
    ann = json.load(open(f"{H}/dance_win/data/annotations/{cid}.json", encoding="utf-8"))
    v = np.zeros(f.shape[:2])
    v[1:] = np.linalg.norm(np.diff(f[..., :2], axis=0), axis=-1) * 30
    print("frame  zL     zR     vL    vR    | vlm L R | phase")
    for t in range(0, len(f), step):
        print(f"{t:4d}  {f[t,0,2]:.3f}  {f[t,1,2]:.3f}  {v[t,0]:.2f}  {v[t,1]:.2f}  |  {ann['contact_L'][t]:2d} {ann['contact_R'][t]:2d}  | {ann['phase'][t]}")
    # linear trend of the stance-foot height: does the reconstructed floor tilt over the clip?
    zmin = f[..., 2].min(axis=1)
    a, b = np.polyfit(np.arange(len(zmin)), zmin, 1)
    print(f"min-ankle-z trend: {a * len(zmin) * 100:+.1f} cm over the clip (start {b:.3f})")
