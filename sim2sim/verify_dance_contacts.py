"""Contact-set check at identical states: mujoco_warp (mjlab sim.forward) vs native mj_forward on models/dance.mjb.
States: every 3rd qpos/qvel... qvel is not stored in traj npz, so states are re-created by an mjlab rollout here.
Writes verify_dance_contacts.json."""
import json
import sys
from collections import Counter
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_dance as nd  # noqa: E402


def main():
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  from dataclasses import asdict

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  info = json.loads((HERE / "models" / "dance_info.json").read_text())
  m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
  g = nd.NativeG1(m, info)
  de = mujoco.MjData(m)
  gname = lambda i: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(i)) or f"g{int(i)}"
  out = {}
  for clip in ("sss", "gxdsm"):
    tag = nd.CLIPS[clip][0]
    pdir = nd.ROOT / "policies" / tag
    cfg = load_env_cfg(nd.TASK, play=True)
    cfg.scene.num_envs = 1
    mc = cfg.commands["motion"]
    mc.motion_file = str(pdir / "reference_motion.npz")
    mc.pose_range, mc.velocity_range, mc.joint_position_range = {}, {}, (0.0, 0.0)
    for k in ("base_com", "encoder_bias", "foot_friction", "push_robot"):
      cfg.events.pop(k, None)
    for k in [k for k in list(cfg.terminations) if k != "time_out"]:
      cfg.terminations.pop(k)
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
    agent_cfg = load_rl_cfg(nd.TASK)
    venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = (load_runner_cls(nd.TASK) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
    runner.load(str(pdir / "policy.pt"), load_cfg={"actor": True}, strict=True, map_location="cuda:0")
    policy = runner.get_inference_policy(device="cuda:0")
    npy = lambda x: torch.as_tensor(x).detach().double().cpu().numpy()
    origin = env.scene.env_origins[0].double().cpu().numpy()
    env.reset()
    obs = venv.get_observations()
    T = int(env.command_manager.get_term("motion").motion.time_step_total)
    cnt_n, cnt_w, pair_only_n, pair_only_w, mism, n_states = [], [], Counter(), Counter(), 0, 0
    examples = []
    for k in range(T - 2):
      with torch.no_grad():
        obs, _, _, _ = venv.step(policy(obs))
      if k % 3:
        continue
      d = env.sim.data
      nac = int(npy(d.nacon).reshape(-1)[0])
      geoms = npy(d.contact.geom)[:nac].astype(int)
      dist = npy(d.contact.dist)[:nac]
      wset = Counter(tuple(sorted((gname(a), gname(b)))) for a, b in geoms)
      q, v = npy(d.qpos[0]).copy(), npy(d.qvel[0]).copy()
      q[:3] -= origin
      g.set_state(de, q, v)
      nset = Counter(tuple(sorted((gname(c.geom1), gname(c.geom2)))) for c in de.contact[:de.ncon])
      ndist = np.array([c.dist for c in de.contact[:de.ncon]])
      cnt_n.append(de.ncon)
      cnt_w.append(nac)
      n_states += 1
      if nset != wset:
        mism += 1
        pair_only_n.update(nset - wset)
        pair_only_w.update(wset - nset)
        if len(examples) < 5:
          examples.append(dict(step=k, native=dict(nset), warp=dict(wset),
                               native_dist=np.round(np.sort(ndist), 5).tolist(),
                               warp_dist=np.round(np.sort(dist), 5).tolist()))
    out[clip] = dict(states=n_states, native_ncon_mean=float(np.mean(cnt_n)), warp_nacon_mean=float(np.mean(cnt_w)),
                     ncon_equal_frac=float(np.mean(np.array(cnt_n) == np.array(cnt_w))),
                     pairset_mismatch_states=mism, pairs_only_native=dict(pair_only_n.most_common(8)),
                     pairs_only_warp=dict(pair_only_w.most_common(8)), examples=examples)
    print(clip, json.dumps(out[clip])[:3000], flush=True)
    env.close()
  (HERE / "verify_dance_contacts.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
  main()
