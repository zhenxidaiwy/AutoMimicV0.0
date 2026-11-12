"""Which success condition fails in a robustness json (eval_flip_robust.py)? Percentiles per scenario.
Usage: python robust_why.py <robust_*.json>"""
import json
import sys

for r in json.load(open(sys.argv[1])):
  print(f"{r['scenario']:8s} success {r['success']:.3f} fell {r['fell']:.3f} | rot p5/50/95 {r['rotation_deg_p5_50_95']} "
        f"(need >= {0.9 * r['ref_rotation_deg']:.0f}) | end tilt max {r['end_tilt_deg_p5_50_95']} (need < 30) | "
        f"pelvis min {r['end_pelvis_min_m_p5_50_95']} (need > 0.6) | drift {r['post_drift_m_p5_50_95']} (need < 0.3)")
