"""Plan B: the SuperMimic online loop (Fig. 2, Alg. A.1) from scratch, laptop-sized. Every iteration:
  1. collect: the current policy runs in mjlab with action noise N(0, 0.1^2); the executed action and the true state
     go into a replay buffer of `cap` steps per env on the GPU (oldest out);
  2. fit: `wm_steps` updates of the world model on k = 8 autoregressive windows from the buffer (state + root-step
     loss, Adam 2e-4, global clip 1.0); the model starts from random weights;
  3. improve: `pi_steps` SuperMimic policy updates (shac_paper.Updater) from buffer start states through the model,
     frozen during the policy backward pass.
The policy (rsl_rl actor layout, running obs normaliser like rsl_rl) starts from random weights and is exported into
an rsl_rl checkpoint every `export_min` minutes, so e1.sh eval scores it unchanged. Wall time runs from the first
collection (env construction excluded) and includes collection, model fit and policy update.
Resets: return-based sampling as in App. D.1 (ReturnSampler, on mjlab's 1 s bins).
Deviations beyond shac_paper.py: a short warm-up (collect + fit before the first policy update), no pushes / CoM /
encoder-bias randomisation (as the world-model data collection), reward / termination heads analytic, no body head,
the model norms fixed from the warm-up data, 3 x 1024 model (paper 3 x 2048), constant lr, G_b normalised per frame
(attainable return to the clip end) instead of one G_max.
Usage (unitree_rl_mjlab env): python online.py --spec <dir with spec.json> --template <rsl_rl model.pt>
  --motion <clip.npz> --out <dir> [--envs 2048] [--minutes 60]"""
import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
REPO = Path.home() / "projects" / "unitree_rl_mjlab"
TERMS = ("motion_global_root_pos", "motion_global_root_ori", "motion_body_pos", "motion_body_ori",
         "motion_body_lin_vel", "motion_body_ang_vel")


def make_env(a):
  """harness mode (--harness-args): the PPO harness env itself, train_dance.build_args with the round's knobs, only
  the env count set here. Otherwise the tracking env as in record.py / collect.py with sensor noise and mjlab's RSI
  ranges kept (the E1 / Plan B experiments)."""
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import RslRlVecEnvWrapper
  if a.harness_args:
    import train_dance
    ours, args, _ = train_dance.build_args(json.loads(Path(a.harness_args).read_text()))
    a.hand_friction, a.knee_limit = ours.hand_friction, ours.knee_limit
    env_cfg, agent_cfg = args.env, args.agent
    env_cfg.commands["motion"].motion_file = str(Path(args.motion_file).expanduser().resolve())  # as train.py does
    env_cfg.scene.num_envs = a.envs
    a.motion = env_cfg.commands["motion"].motion_file
    env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
    return env, RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
  env_cfg, agent_cfg = load_env_cfg(a.task), load_rl_cfg(a.task)
  env_cfg.scene.num_envs = a.envs
  cmd_cfg = env_cfg.commands["motion"]
  cmd_cfg.motion_file = str(Path(a.motion).resolve())
  cmd_cfg.sampling_mode = "uniform"
  for k in ("push_robot", "base_com", "encoder_bias"):
    env_cfg.events.pop(k, None)
  for k in ("anchor_pos", "ee_body_pos"):
    p = env_cfg.terminations[k].params
    p["threshold"] = max(p["threshold"], 0.6)
  from mimic_generic import set_hand_friction
  set_hand_friction(env_cfg.scene.entities["robot"], a.hand_friction)
  from flip_rewards import set_knee_limit
  set_knee_limit(env_cfg.scene.entities["robot"].articulation, a.knee_limit)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
  return env, RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)


def env_spec(env, a):
  """task constants for imagine.py read from the running env (as record.py writes spec.json)"""
  robot, cmd_cfg, cfg = env.scene["robot"], env.cfg.commands["motion"], env.cfg
  terms = TERMS + ("action_rate_l2", "joint_limit")
  thr = {k: (cfg.terminations[k].params["threshold"] if k in cfg.terminations else 1e3)
         for k in ("anchor_pos", "anchor_ori", "ee_body_pos")}
  ee = cfg.terminations["ee_body_pos"].params["body_names"] if "ee_body_pos" in cfg.terminations else []
  return {
    "joint_names": list(robot.joint_names), "robot_body_names": list(robot.body_names),
    "tracked_bodies": list(cmd_cfg.body_names), "anchor_body": cmd_cfg.anchor_body_name, "ee_bodies": list(ee),
    "default_joint_pos": robot.data.default_joint_pos[0].tolist(),
    "soft_joint_pos_limits": robot.data.soft_joint_pos_limits[0].tolist(),
    "reward_weights": {n: cfg.rewards[n].weight for n in terms if n in cfg.rewards},
    "reward_std": {n: cfg.rewards[n].params["std"] for n in terms if n in cfg.rewards and "std" in cfg.rewards[n].params},
    "term_thresholds": thr, "task": a.task, "motion": a.motion, "ckpt": a.template}


class Heads(torch.nn.Module):
  """learned reward / termination heads (paper: each head learned or analytic): from (x_t, a_t) -> the step's reward
  residual (mjlab's total step reward minus the analytic tracking reward, unscaled) and its termination logit. They
  carry every term the harness adds (flip / library rewards, extra terminations) into the imagination."""
  def __init__(self, dim, mean, std):
    super().__init__()
    self.mean, self.std = mean, std
    self.mlp = torch.nn.Sequential(torch.nn.Linear(dim + 29, 256), torch.nn.ELU(), torch.nn.Linear(256, 256),
                                   torch.nn.ELU(), torch.nn.Linear(256, 2))

  def forward(self, x, act):
    y = self.mlp(torch.cat([(x - self.mean) / (self.std + 1e-2), act], -1))
    return y[..., 0], y[..., 1]


class ScratchPolicy(torch.nn.Module):
  """rsl_rl actor layout 154-512-256-128-29 (ELU), random init, running obs normaliser (count-weighted, as rsl_rl)"""
  def __init__(self, dev):
    super().__init__()
    dims, layers = [154, 512, 256, 128, 29], []
    for i in range(len(dims) - 1):
      layers += [torch.nn.Linear(dims[i], dims[i + 1])] + ([torch.nn.ELU()] if i < len(dims) - 2 else [])
    self.mlp = torch.nn.Sequential(*layers).to(dev)
    self.mean, self.var, self.count = torch.zeros(154, device=dev), torch.ones(154, device=dev), 0

  @property
  def std(self):
    return self.var.sqrt()

  @torch.no_grad()
  def observe(self, o):
    o = o[torch.isfinite(o).all(-1)]  # an exploded env must not poison the running statistics
    if o.shape[0] < 2:
      return
    n, m, v = o.shape[0], o.mean(0), o.var(0, unbiased=False)
    tot = self.count + n
    d = m - self.mean
    self.mean = self.mean + d * n / tot
    self.var = (self.var * self.count + v * n + d * d * self.count * n / tot) / tot
    self.count = tot

  def forward(self, obs):
    return self.mlp((obs - self.mean) / (self.std + 1e-2))

  def export(self, path, template_ckpt):
    ck = torch.load(template_ckpt, map_location="cpu", weights_only=False)
    sd = ck["actor_state_dict"]
    lins = [m for m in self.mlp if isinstance(m, torch.nn.Linear)]
    for li, lin in zip((0, 2, 4, 6), lins):
      sd[f"mlp.{li}.weight"], sd[f"mlp.{li}.bias"] = lin.weight.detach().cpu().clone(), lin.bias.detach().cpu().clone()
    sd["obs_normalizer._mean"] = self.mean.cpu()[None].clone()
    sd["obs_normalizer._var"] = self.var.cpu()[None].clone()
    sd["obs_normalizer._std"] = self.std.cpu()[None].clone()
    sd["obs_normalizer.count"] = torch.tensor(self.count)
    ck["iter"], ck["infos"] = 0, {"source": "online.py (SuperMimic loop, from scratch)"}
    torch.save(ck, path)


class Ring:
  """replay buffer on the GPU: (cap, E) per field, step n written at row n % cap.
  done[t] = the step t -> t+1 ended in a reset or a clip-end teleport (frame jump)."""
  def __init__(self, cap, E, dev, wm):
    self.cap, self.E, self.n, self.wm = cap, E, 0, wm
    h = torch.float16
    self.s = torch.zeros(cap, E, wm.NS, device=dev, dtype=h)
    self.a = torch.zeros(cap, E, wm.NJ, device=dev, dtype=h)
    self.last = torch.zeros(cap, E, wm.NJ, device=dev, dtype=h)
    self.xy = torch.zeros(cap, E, 2, device=dev)
    self.yaw = torch.zeros(cap, E, device=dev)
    self.fr = torch.zeros(cap, E, dtype=torch.long, device=dev)
    self.done = torch.zeros(cap, E, dtype=torch.bool, device=dev)
    self.r = torch.zeros(cap, E, device=dev)  # real tracking reward of the step t -> t+1 (x dt)
    # harness mode: the step's reward residual (valid if the next state is not a reset / teleport) and its
    # real termination (mjlab's terminated, time-outs excluded)
    self.rres = torch.zeros(cap, E, device=dev)
    self.rval = torch.zeros(cap, E, dtype=torch.bool, device=dev)
    self.term = torch.zeros(cap, E, dtype=torch.bool, device=dev)
    self.bad = torch.zeros(cap, E, dtype=torch.bool, device=dev)  # non-finite / fp16-overflow state (zeroed)

  def push(self, s, xy, yaw, fr, act, last, done, r, rres=None, rval=None, term=None, bad=None):
    i = self.n % self.cap
    if self.n > 0:
      p = (self.n - 1) % self.cap
      self.done[p] |= fr != self.fr[p] + 1
      if bad is not None:  # the step into a bad state is not a valid transition either
        self.done[p] |= bad; self.rval[p] &= ~bad
    if bad is not None:
      self.bad[i] = bad
    self.s[i], self.a[i], self.last[i] = s.half(), act.half(), last.half()
    self.xy[i], self.yaw[i], self.fr[i], self.done[i], self.r[i] = xy, yaw, fr, done, r
    if rres is not None:
      self.rres[i], self.rval[i], self.term[i] = rres, rval, term
    self.n += 1

  def transitions(self, env, B, gen):
    """B logged steps (state t with its frame and previous action, the executed action, residual, termination)"""
    lo = max(0, self.n - self.cap)
    dev = self.s.device
    t = torch.randint(lo, self.n, (B,), device=dev, generator=gen) % self.cap
    e = torch.randint(0, self.E, (B,), device=dev, generator=gen)
    fr = self.fr[t, e].clamp(max=env.ref.T - 1)
    st = env.make_state(self.s[t, e].float(), self.xy[t, e], self.yaw[t, e], fr, last_act=self.last[t, e].float())
    return st, self.a[t, e].float(), self.rres[t, e], self.rval[t, e], self.term[t, e], ~self.bad[t, e]

  def recent(self, L):
    """rows of the last L steps in time order (oldest first)"""
    L = min(L, self.n, self.cap)
    return (torch.arange(self.n - L, self.n, device=self.s.device)) % self.cap

  @property
  def size(self):
    return min(self.n, self.cap) * self.E

  def windows(self, B, k, gen, xi):
    lo = max(0, self.n - self.cap)
    dev = self.s.device
    t = torch.randint(lo, self.n - k - 1, (2 * B,), device=dev, generator=gen)  # state t + k is complete
    e = torch.randint(0, self.E, (2 * B,), device=dev, generator=gen)
    idx = (t[:, None] + torch.arange(k + 1, device=dev)) % self.cap
    ok = ~self.done[idx[:, :k], e[:, None]].any(1)
    idx, e = idx[ok], e[ok]
    j = torch.arange(B, device=dev) % len(e)  # always exactly B (compiled model step: one shape)
    idx, e = idx[j], e[j]
    ee = e[:, None]
    root = torch.cat([self.yaw[idx, ee][..., None], self.xy[idx, ee]], -1)
    return {"s": self.s[idx, ee].float(), "a": self.a[idx[:, :k], ee].float(),
            "droot": self.wm.root_step(root[:, :-1], root[:, 1:]), "xi": xi.expand(len(e), 3)}

  def starts(self, env, B, gen):
    lo = max(0, self.n - self.cap)
    dev = self.s.device
    t = torch.randint(lo, self.n, (2 * B,), device=dev, generator=gen)
    e = torch.randint(0, self.E, (2 * B,), device=dev, generator=gen)
    ok = (self.fr[t % self.cap, e] < env.ref.T - 1) & ~self.bad[t % self.cap, e]
    r, e = (t % self.cap)[ok], e[ok]
    j = torch.arange(B, device=dev) % len(r)  # always exactly B (compiled kinematics: one shape)
    r, e = r[j], e[j]
    return env.make_state(self.s[r, e].float(), self.xy[r, e], self.yaw[r, e], self.fr[r, e],
                          last_act=self.last[r, e].float())


class ReturnSampler:
  """SuperMimic return-based reset sampling (App. D.1) on mjlab's 1 s bins: 50 % uniform, 40 %
  softmax(-25 G_b / G_max), 10 % in proportion to the running mean of past softmax weights. G_b = running mean of
  the discounted real return from states in bin b, divided by the largest return attainable from that frame to the
  clip end (the episode is cut at a reset or the clip-end teleport). Steps whose return is still open (the last
  `tail` steps) are not used."""
  def __init__(self, cmd, T, gamma, rmax, dev, ema=0.1, tail=100):
    self.cmd, self.T, self.g, self.rmax, self.ema, self.tail = cmd, T, gamma, rmax, ema, tail
    self.nb = cmd.bin_count
    self.G = torch.full((self.nb,), 0.5, device=dev)
    self.past = torch.full((self.nb,), 1.0 / self.nb, device=dev)
    self.p = torch.full((self.nb,), 1.0 / self.nb, device=dev)
    cmd.cfg.sampling_mode = "adaptive"
    cmd._adaptive_sampling = self.sample

  def sample(self, env_ids):
    c = self.cmd
    b = torch.multinomial(self.p, len(env_ids), replacement=True)
    u = torch.rand(len(env_ids), device=self.p.device)
    c.time_steps[env_ids] = ((b + u) / self.nb * (c.motion.time_step_total - 1)).long()

  @torch.no_grad()
  def update(self, ring, L):
    rows = ring.recent(L)
    if len(rows) <= self.tail + 1:
      return
    r, dn, fr = ring.r[rows], ring.done[rows], ring.fr[rows]
    G = torch.zeros_like(r)
    nxt = torch.zeros_like(r[0])
    for t in reversed(range(len(rows))):
      nxt = r[t] + self.g * (~dn[t]).float() * nxt
      G[t] = nxt
    rem = (self.T - 1 - fr).clamp(min=1).float()
    Gmax = self.rmax * (1 - self.g ** rem) / (1 - self.g)
    Gn, fr = (G / Gmax)[: -self.tail].flatten(), fr[: -self.tail].flatten()
    bins = (fr * self.nb // max(self.cmd.motion.time_step_total, 1)).clamp(0, self.nb - 1)
    cnt = torch.bincount(bins, minlength=self.nb).float()
    mean = torch.bincount(bins, weights=Gn, minlength=self.nb) / cnt.clamp(min=1)
    self.G = torch.where(cnt > 0, (1 - self.ema) * self.G + self.ema * mean, self.G)
    w = torch.softmax(-25 * self.G, 0)
    self.past = (1 - self.ema) * self.past + self.ema * w
    self.p = 0.5 / self.nb + 0.4 * w + 0.1 * self.past / self.past.sum()


def run(a):
  import imagine as im
  import shac_paper as sp
  wm = im.wm
  dev = "cuda"
  torch.manual_seed(a.seed)
  if a.tf32:  # TF32 matmuls, as the paper's training (§4.2)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
  out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
  env_mj, venv = make_env(a)
  robot, cmd, rm = env_mj.scene["robot"], env_mj.command_manager.get_term("motion"), env_mj.reward_manager
  ti = [list(rm._term_names).index(n) for n in TERMS]
  d = robot.data
  xi = torch.tensor([1.0, 1.0, a.hand_friction], device=dev)
  if a.wm_init.startswith("cuboi:"):  # CuboiLeo e8 pretrained model (cuboi_wm.py adapter), fixed loss scales
    import cuboi_wm
    model = cuboi_wm.load(a.wm_init[len("cuboi:"):], dev)
  elif a.wm_init:  # pretrained (e.g. v1b): weights and norms kept, continual fit on the online buffer
    model, _ = wm.load(a.wm_init, dev)
  else:
    model = wm.WorldModel(3, tuple(int(x) for x in a.hidden.split(","))).to(dev)  # body head unused (FK is exact)
  opt_m = torch.optim.Adam(model.parameters(), lr=a.lr_wm)
  spec_path = Path(a.spec) / "spec.json" if a.spec else out / "spec.json"
  if not a.spec:  # constants of the env actually running (harness knobs: thresholds, scaled tracking weights)
    spec_path.write_text(json.dumps(env_spec(env_mj, a), indent=1))
  ienv = im.ImaginedTracking(model, spec_path, a.motion, xi.tolist(), dev)
  if a.compile:  # same math, fused kernels (profile_update.py: 2.0 -> 0.9 s per update at 4096 x 32)
    ienv.fk.with_vel = torch.compile(ienv.fk.with_vel)
    ienv.reward_terms = torch.compile(ienv.reward_terms)
  if a.compile_model:  # the dynamics step too (matters for the 3 x 2048 CuboiLeo model)
    model.step = torch.compile(model.step)
  pol = ScratchPolicy(dev)
  ring = Ring(a.cap, a.envs, dev, wm)
  gen = torch.Generator(device=dev).manual_seed(a.seed)
  wsum = sum(env_mj.cfg.rewards[n].weight for n in TERMS if n in env_mj.cfg.rewards)  # largest tracking reward
  # resets: the paper's return-based sampling, or (harness mode) the harness's own phase prior left untouched
  rbs = ReturnSampler(cmd, ienv.ref.T, a.gamma, wsum * im.DT, dev) if a.resets == "return" else None
  tm = env_mj.termination_manager
  ep_len, ep_done = torch.zeros(a.envs, device=dev), []
  guard = {"bad_state": 0, "skip_wm": 0, "skip_heads": 0}  # numerical guards (counts since start)

  def state():
    R = wm.quat_to_mat(d.root_link_quat_w)
    yaw = wm.yaw_of(R)
    Rt = R.transpose(-1, -2)
    v = (Rt @ d.root_link_lin_vel_w.unsqueeze(-1)).squeeze(-1)
    w = (Rt @ d.root_link_ang_vel_w.unsqueeze(-1)).squeeze(-1)
    pos = d.root_link_pos_w - env_mj.scene.env_origins
    s = torch.cat([pos[:, 2:3], wm.mat_to_six(wm.rot_z(yaw).transpose(-1, -2) @ R), v, w, d.joint_pos, d.joint_vel], -1)
    return s, pos[:, :2], yaw

  env_mj.reset()
  obs = venv.get_observations()
  with torch.no_grad():  # the first step after reset reports done for every env
    obs, _, _, _ = venv.step(torch.zeros(a.envs, wm.NJ, device=dev))
  o = obs["actor"]
  last = torch.zeros(a.envs, wm.NJ, device=dev)
  stats = {"track": 0.0, "done": 0.0, "n": 0}
  term_names = list(rm._term_names)
  term_sum = torch.zeros(len(term_names), device=dev)  # real per-term step rewards (for the harness config audit)

  def collect(n):
    nonlocal obs, o, last
    with torch.no_grad():
      for _ in range(n):
        pol.observe(o)
        act = pol(torch.nan_to_num(o, 0.0, 0.0, 0.0)) + a.action_noise * torch.randn(o.shape[0], wm.NJ, device=dev, generator=gen)
        act = torch.nan_to_num(act, 0.0, 0.0, 0.0)
        s, xy, yaw = state()
        bad = ~(torch.isfinite(s).all(-1) & (s.abs() < 6e4).all(-1))  # the ring stores fp16 (max 65504)
        if bad.any():
          guard["bad_state"] += int(bad.sum())
          s = torch.where(bad[:, None], torch.zeros_like(s), s)
          xy, yaw = torch.nan_to_num(xy), torch.nan_to_num(yaw)
        fr = cmd.time_steps.clone().long()
        obs, _, dones, _ = venv.step(act)
        dn = dones.bool()
        tr = rm._step_reward[:, ti].sum(-1)
        if a.heads:  # residual = total step reward - analytic reward on the next state (if it is not a reset)
          s1, xy1, yaw1 = state()
          fr1 = cmd.time_steps.clone().long()
          ok = ~dn & (fr1 == fr + 1)
          st1 = ienv.make_state(s1, xy1, yaw1, fr1.clamp(max=ienv.ref.T - 1), last_act=act)
          ana = sum(ienv.reward_terms(st1, act, last).values())
          res = rm._step_reward.sum(-1) - ana
          ok = ok & ~bad & torch.isfinite(res) & torch.isfinite(s1).all(-1) & (s1.abs() < 6e4).all(-1)
          ring.push(s, xy, yaw, fr, act, last, dn | bad, torch.nan_to_num(tr) * im.DT, torch.nan_to_num(res) * ok,
                    ok, tm.terminated.clone(), bad)
        else:
          ring.push(s, xy, yaw, fr, act, last, dn | bad, torch.nan_to_num(tr) * im.DT, bad=bad)
        ep_len.add_(1)
        if dn.any():
          ep_done.extend(ep_len[dn].tolist()); ep_len[dn] = 0
        term_sum.add_(rm._step_reward.mean(0))
        stats["track"] += tr.mean().item()
        stats["done"] += dn.float().mean().item()
        stats["n"] += 1
        last = act * (~dn).float()[:, None]
        o = obs["actor"]

  def fit(n):
    for p in model.parameters():
      p.requires_grad_(True)
    ls = torch.zeros(())
    for _ in range(n):
      b = ring.windows(a.wm_batch, a.k, gen, xi)
      S, R = model.rollout(b["s"][:, 0], b["a"], b["xi"])
      ls = ((model.ns(S[:, 1:]) - model.ns(b["s"][:, 1:])) ** 2).mean() + ((model.nroot(R) - model.nroot(b["droot"])) ** 2).mean()
      opt_m.zero_grad(set_to_none=True); ls.backward()
      if torch.isfinite(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)) and torch.isfinite(ls):
        opt_m.step()
      else:
        guard["skip_wm"] += 1
    for p in model.parameters():
      p.requires_grad_(False)
    return ls.item()

  heads, opt_h = None, None

  def fit_heads(n):
    """reward residual (MSE on valid steps) + termination (BCE) heads on logged transitions"""
    for p in heads.parameters():
      p.requires_grad_(True)
    lr_, lt_ = torch.zeros(()), torch.zeros(())
    for _ in range(n):
      st, act, res, val, term, good = ring.transitions(ienv, a.head_batch, gen)
      with torch.no_grad():
        x = up.critic_in(st, ienv.obs(st))
      r_hat, logit = heads(x, act)
      lr_ = ((r_hat - res) ** 2 * val).sum() / val.sum().clamp(min=1)
      lt_ = (torch.nn.functional.binary_cross_entropy_with_logits(logit, term.float(), reduction="none") * good).sum() \
            / good.sum().clamp(min=1)
      opt_h.zero_grad(set_to_none=True); (lr_ + lt_).backward()
      if torch.isfinite(torch.nn.utils.clip_grad_norm_(heads.parameters(), 1.0)) and torch.isfinite(lr_ + lt_):
        opt_h.step()
      else:
        guard["skip_heads"] += 1
    for p in heads.parameters():
      p.requires_grad_(False)
    return lr_.item(), lt_.item()

  t0 = time.time()
  st0 = torch.load(a.resume, map_location=dev, weights_only=False) if a.resume else None
  if st0 is not None:  # continue the previous round: policy, model, critic, heads, optimisers
    pol.mlp.load_state_dict(st0["policy"]); pol.mean, pol.var, pol.count = st0["obs_mean"], st0["obs_var"], st0["obs_count"]
    model.load_state_dict(st0["model"]); opt_m.load_state_dict(st0["opt_m"])
  # warm-up: fresh data (the replay buffer is not carried over between runs); from scratch also the model norms
  collect(a.warm_collect)
  if st0 is None and not a.wm_init:
    b = ring.windows(min(ring.size // 2, 50000), a.k, gen, xi)
    model.ns.fit(b["s"]); model.na.fit(b["a"]); model.nx.fit(b["xi"])
    model.nds.fit(b["s"][:, 1:] - b["s"][:, :-1]); model.nroot.fit(b["droot"])
    del b
  lw = fit(a.warm_fit)
  up = sp.Updater(ienv, pol, a, gen, ring.starts(ienv, a.rollouts, gen))
  if st0 is not None:
    up.critic.mean, up.critic.std = st0["critic_mean"], st0["critic_std"]
    up.critic.load_state_dict(st0["critic"], strict=False)
    up.opt_a.load_state_dict(st0["opt_a"]); up.opt_c.load_state_dict(st0["opt_c"])
  if a.heads:
    heads = Heads(up.critic.mean.shape[0], up.critic.mean, up.critic.std).to(dev)
    opt_h = torch.optim.Adam(heads.parameters(), lr=a.lr_wm)
    if st0 is not None and st0.get("heads"):
      heads.load_state_dict(st0["heads"], strict=False); opt_h.load_state_dict(st0["opt_h"])
    lh = fit_heads(a.warm_fit)
    up.heads = heads
  it0 = st0["it"] if st0 is not None else 0

  def save_state(path, it_g):
    torch.save({"it": it_g, "policy": pol.mlp.state_dict(), "obs_mean": pol.mean, "obs_var": pol.var,
                "obs_count": pol.count, "model": model.state_dict(), "opt_m": opt_m.state_dict(),
                "critic": up.critic.state_dict(), "critic_mean": up.critic.mean, "critic_std": up.critic.std,
                "opt_a": up.opt_a.state_dict(), "opt_c": up.opt_c.state_dict(),
                "heads": heads.state_dict() if heads else None, "opt_h": opt_h.state_dict() if opt_h else None,
                "args": vars(a)}, path)

  def export(mins):
    """harness mode: rsl_rl-named checkpoint model_<global it>.pt + the full trainer state state_<global it>.pt"""
    if a.harness_args:
      pol.export(out / f"model_{it0 + it}.pt", a.template)
      save_state(out / f"state_{it0 + it}.pt", it0 + it)
    else:
      pol.export(out / f"model_wm_{mins:05.1f}min.pt", a.template)
  log, it, next_export = [], 0, a.export_min if a.harness_args else 0.0
  print(json.dumps({"warmup_min": round((time.time() - t0) / 60, 2), "wm_loss": round(lw, 5), "buffer": ring.size}),
        flush=True)
  tc = tf = tu = 0.0
  while (time.time() - t0) / 60 < a.minutes:
    it += 1
    t1 = time.time(); collect(a.collect)
    if rbs is not None and it % a.rbs_every == 0:
      rbs.update(ring, a.rbs_window)
    t2 = time.time()
    lw = fit(a.wm_steps)
    if heads is not None:
      lh = fit_heads(a.head_steps)
    t3 = time.time()
    rec = {}
    for _ in range(a.pi_steps):
      rec = up.update(ring.starts(ienv, a.rollouts, gen))
    t4 = time.time()
    tc, tf, tu = tc + t2 - t1, tf + t3 - t2, tu + t4 - t3
    mins = (time.time() - t0) / 60
    if it % a.log_every == 0:
      stats_n = stats["n"]
      rec = {"it": it, "min": round(mins, 2), "real_track_step": round(stats["track"] / max(stats["n"], 1), 4),
             "real_done_per_step": round(stats["done"] / max(stats["n"], 1), 5), "wm_loss": round(lw, 5),
             **rec, "buffer": ring.size, "s_collect": round(tc, 1), "s_fit": round(tf, 1), "s_update": round(tu, 1)}
      if rbs is not None:
        rec["bin_G"], rec["bin_p"] = [round(x, 3) for x in rbs.G.tolist()], [round(x, 3) for x in rbs.p.tolist()]
      if heads is not None:
        rec["head_rew_mse"], rec["head_term_bce"] = round(lh[0], 5), round(lh[1], 5)
      rec.update(guard); rec.update(up.guard)
      stats.update(track=0.0, done=0.0, n=0)
      log.append(rec)
      print(json.dumps(rec), flush=True)
      if ep_done:  # same line as rsl_rl, read by the harness (ep_len)
        print(f"Mean episode length: {sum(ep_done) / len(ep_done):.2f}", flush=True)
        ep_done.clear()
      # rsl_rl-style term lines for the harness config audit (quant_report F); value = mean step reward x dt
      for n, v in zip(term_names, (term_sum / max(stats_n, 1) * im.DT).tolist()):
        print(f"Episode_Reward/{n}: {v:.4f}", flush=True)
      term_sum.zero_()
    if mins >= next_export:
      export(mins)
      next_export = mins + a.export_min
  export((time.time() - t0) / 60)
  if hasattr(model, "trunk"):
    hidden = [m.out_features for m in model.trunk if isinstance(m, torch.nn.Linear)]
    wm.save(model, out / "wm.pt", {"hidden": hidden, "k": a.k, "online": True, "init": a.wm_init})
  else:
    torch.save({"state_dict": model.state_dict(), "init": a.wm_init}, out / "wm_cuboi.pt")
  (out / "log.json").write_text(json.dumps({"args": vars(a), "log": log}))
  print(json.dumps({"done": True, "iters": it, "min": round((time.time() - t0) / 60, 1), "s_collect": round(tc),
                    "s_fit": round(tf), "s_update": round(tu),
                    "peak_mem_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)}), flush=True)
  env_mj.close()


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--spec", default="", help="dir with spec.json; default: written from the running env")
  ap.add_argument("--template", required=True, help="any rsl_rl checkpoint of this task (layout for the export)")
  ap.add_argument("--motion", default="", help="reference clip (harness mode: taken from the harness env)")
  ap.add_argument("--harness-args", default="", help="json file: the train_dance.py argv of a harness round")
  ap.add_argument("--resume", default="", help="state_<it>.pt of a previous run (harness: the warm start)")
  ap.add_argument("--resets", choices=("return", "harness"), default="return",
                  help="return: the paper's return-based sampling; harness: the env's own reset prior")
  ap.add_argument("--heads", type=int, default=0, help="learned reward-residual / termination heads")
  ap.add_argument("--head-steps", type=int, default=2)
  ap.add_argument("--head-batch", type=int, default=4096)
  ap.add_argument("--out", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--envs", type=int, default=4096)
  ap.add_argument("--cap", type=int, default=1000, help="replay steps per env")
  ap.add_argument("--minutes", type=float, default=60)
  ap.add_argument("--export-min", type=float, default=5)
  ap.add_argument("--action-noise", type=float, default=0.1)
  ap.add_argument("--collect", type=int, default=3, help="vector env steps per iteration")
  ap.add_argument("--wm-steps", type=int, default=10, help="paper: 10 batches of 2048 windows per update")
  ap.add_argument("--rbs-every", type=int, default=10, help="iterations between return-based sampler updates")
  ap.add_argument("--rbs-window", type=int, default=400, help="recent steps per env used for the bin returns")
  ap.add_argument("--wm-batch", type=int, default=2048)
  ap.add_argument("--k", type=int, default=8)
  ap.add_argument("--lr-wm", type=float, default=2e-4)
  ap.add_argument("--hidden", default="1024,1024,1024")
  ap.add_argument("--wm-init", default="", help="pretrained world model (wm.py format) to start from")
  ap.add_argument("--pi-steps", type=int, default=1)
  ap.add_argument("--rollouts", type=int, default=4096)
  ap.add_argument("--compile", type=int, default=1)
  ap.add_argument("--compile-model", type=int, default=0)
  ap.add_argument("--tf32", type=int, default=0)
  ap.add_argument("--warm-collect", type=int, default=50)
  ap.add_argument("--warm-fit", type=int, default=500)
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--log-every", type=int, default=10)
  ap.add_argument("--seed", type=int, default=0)
  sys.path.insert(0, str(HERE))
  import shac_paper
  shac_paper.add_update_args(ap)
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  sys.path.insert(0, str(HERE.parents[1]))
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  run(a)
