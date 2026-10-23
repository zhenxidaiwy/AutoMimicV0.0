"""Print the trigger-rule table of one or more trigger_eval runs, best first (fewest negative triggers among the
rules that keep the most positives triggered with the right dance)."""
import json
import sys
from pathlib import Path

for w in sys.argv[1:]:
  res = json.load(open(Path.home() / "projects/dance/vla/trigger_eval" / w / "rules.json", encoding="utf-8"))
  print(f"== {w}")
  print(f"{'rule':<46} negTrig negClips negDance_s | posHit firstRight wrong firstT_med")
  key = lambda r: (-r["pos_first_right"], r["neg_triggers"], r["neg_robot_dance_s"], r["pos_first_t_median"] or 99)
  for r in [res[0]] + sorted(res[1:], key=key)[:int(sys.argv[0] and 15)]:
    print(f"{r['name']:<46} {r['neg_triggers']:>7} {r['neg_clips_triggered']:>8} {r['neg_robot_dance_s']:>10} | "
          f"{r['pos_hit']:>6} {r['pos_first_right']:>10} {r['pos_wrong_dance_replays']:>5} {r['pos_first_t_median']}")
