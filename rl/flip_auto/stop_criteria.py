"""Stop criteria of a skill (layered like the diagnostic library: generic + family + task; config
stop_criteria.json). Evaluated automatically after every round (quant_report section S) and written to
analysis/rNN_stop.json; the harness refuses to train a finished skill further unless the decision gives a
continue_reason, and stops a skill over budget unless it gives a budget_override.
Usage: python stop_criteria.py K   (prints the table, writes analysis/rKK_stop.json)"""
import json
import operator
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import library as libm  # noqa: E402

H = Path.home()
LOGS = H / "projects/dance/runs/logs/rsl_rl/g1_tracking"
OPS = {"<=": operator.le, ">=": operator.ge, "==": operator.eq, "<": operator.lt, ">": operator.gt}


def waivers():
  out = []
  for p in sorted((HERE / "decisions").glob("r*.json")):
    out += json.loads(p.read_text()).get("waive", [])
  return out


def task_gates_added():
  out = []
  for p in sorted((HERE / "decisions").glob("r*.json")):
    out += json.loads(p.read_text()).get("stop_gates_add", [])
  return out


def evaluate(k, task="backflip_3", ds=None):
  cfg = json.loads((HERE / "stop_criteria.json").read_text())
  lib = libm.load()
  fam = libm.family_of(lib, task)
  st = json.loads((HERE / "state.json").read_text())
  rd = st["rounds"][k - 1]
  best = max(rd["evals"], key=lambda e: e.get("score", -1))
  ck = best["ckpt"][:-3]
  ev = LOGS / rd["run"] / "eval"
  ds = ds or H / "projects/dance/dataset" / task
  L = np.load(ds / "labels_50fps.npz")
  names = [str(x) for x in L["phase_names"]]
  ref_flight_s = float((L["phase"] == names.index("flight")).sum()) / 50.0 if "flight" in names else 0.0
  M = {f"eval.{a}": b for a, b in best.items() if not isinstance(b, (list, dict))}
  rp = ev / f"robust_{ck}.json"
  if rp.exists():
    for r in json.loads(rp.read_text()):
      M[f"robust.{r['scenario']}"] = r["success"]
  sp = ev / f"sim2sim_{ck}.json"  # written by the sim2sim exam (native_flip.py) when it is run on this checkpoint
  if sp.exists():
    for name, v in json.loads(sp.read_text()).get("success", {}).items():
      M[f"sim2sim.{name}"] = v
  rec = ev / f"flip_auto_{ck}_record.npz"
  if rec.exists():
    R = np.load(rec, allow_pickle=True)
    ph = libm.phase_names({"phase_names": L["phase_names"], "phase": L["phase"][:len(R["q"])]})
    after = np.array([i for i, n in enumerate(ph) if n.endswith("_after")])
    if len(after):
      M["after.feet_off_steps"] = int((R["foot_z"][after] > 0.06).any(-1).sum())
  cj = ev / f"flip_auto_{ck}_critic.json"
  W = waivers()
  if cj.exists():
    checks = json.loads(cj.read_text()).get("checks", [])
    un = [c for c in checks if not libm.waived(c["id"], W)]
    M["critic.max_unwaived_severity"] = max([c["severity"] for c in un], default=0.0)
    M["critic.worst_unwaived"] = un[0]["id"] if un else None
  gates = cfg.get("generic", []) + cfg.get(f"family:{fam}", []) + cfg.get(f"task:{task}", []) + task_gates_added()
  rows = []
  for g in gates:
    v = M.get(g["metric"])
    thr = g.get("value")
    if "value_ref" in g:
      thr = eval(g["value_ref"], {}, {"ref_flight_s": ref_flight_s})  # noqa: S307 (own config)
    status = "pending" if v is None else ("pass" if OPS[g["op"]](v, thr) else "FAIL")
    rows.append({"id": g["id"], "metric": g["metric"], "value": v, "op": g["op"], "threshold": thr, "status": status})
  # convergence over the last rounds
  c = cfg["convergence"]
  hist = []
  for r in st["rounds"][:k]:
    b = max(r["evals"], key=lambda e: e.get("score", -1))
    if c["metric"].split(".", 1)[1] in b:
      hist.append(b[c["metric"].split(".", 1)[1]])
  rel = [(hist[i - 1] - hist[i]) / max(abs(hist[i - 1]), 1e-9) for i in range(len(hist) - c["rounds"], len(hist))
         if i >= 1] if len(hist) > c["rounds"] else []
  converged = bool(rel) and all(x < c["rel_improvement"] for x in rel)
  rounds_used = k
  gpu_h = sum(r.get("minutes", 0) or 0 for r in st["rounds"][:k]) / 60.0
  b = cfg["budget"]
  over = rounds_used >= b["rounds"] or gpu_h >= b["gpu_hours"]
  done = all(r["status"] == "pass" for r in rows) and converged
  out = {"round": k, "task": task, "family": fam, "done": done, "converged": converged,
         "convergence_rel_improvement": [round(x, 4) for x in rel], "rounds_used": rounds_used,
         "gpu_hours": round(gpu_h, 1), "over_budget": over and not done, "gates": rows,
         "n_waivers": len(W), "worst_unwaived_check": M.get("critic.worst_unwaived")}
  (HERE / "analysis" / f"r{k:02d}_stop.json").write_text(json.dumps(out, indent=1))
  return out


def markdown(out):
  L = ["## S. Stop criteria (generic + family:%s + task; stop_criteria.json)" % out["family"], "",
       f"**{'DONE' if out['done'] else 'not done'}** - converged: {out['converged']} "
       f"(rel. improvement of the last rounds {out['convergence_rel_improvement']}), rounds used {out['rounds_used']}, "
       f"GPU {out['gpu_hours']} h, over budget: {out['over_budget']}, waivers in force: {out['n_waivers']}", "",
       "| gate | metric | value | threshold | status |", "|---|---|---|---|---|"]
  for r in out["gates"]:
    v = r["value"] if not isinstance(r["value"], float) else round(r["value"], 3)
    L.append(f"| {r['id']} | {r['metric']} | {v} | {r['op']} {r['threshold']} | {r['status']} |")
  if out.get("worst_unwaived_check"):
    L.append(f"\nworst unwaived library check: {out['worst_unwaived_check']}")
  return L


if __name__ == "__main__":
  o = evaluate(int(sys.argv[1]))
  print("\n".join(markdown(o)))
