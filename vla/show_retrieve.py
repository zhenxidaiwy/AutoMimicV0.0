"""Print retrieve_loop results whose file name contains a tag. Usage: python show_retrieve.py <tag-substring>"""
import glob
import json
import os
import sys

if __name__ == "__main__":
  tag = sys.argv[1]
  for p in sorted(glob.glob(os.path.expanduser(f"~/projects/dance/vla/retrieve_loop/*{tag}*.json"))):
    r = json.load(open(p))["result"]
    print(f"{r['clip']:<18} kp={r.get('kp', 'vit'):<4} watch={r['watch']:<14} "
          f"{'done' if r['completed'] else 'fell %.2fs' % r['fell_at_s']:<10} sss_frac={r['dance_pred_frac_sss']:.2f} "
          f"sync={r['phase_sync']:.2f} flashes {r['flash_onsets_matched']}/{r['flash_onsets_human']} "
          f"track_err={r['track_err_mean']:.3f}")
