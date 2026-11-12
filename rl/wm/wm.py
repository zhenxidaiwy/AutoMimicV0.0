"""G1 world model (SuperMimic idea): a deterministic MLP s' = f(s, a, xi) fit on logged mjlab transitions.

State features are translation- and yaw-invariant (like the policy observation):
  root height (1), root orientation relative to its heading as a 6D rotation (6), root linear / angular velocity in
  the body frame (3 + 3), joint position / velocity (29 + 29)                                  -> 71
The model predicts the normalised change of the state plus the root motion in the current heading frame (yaw change,
xy step) so a world trajectory can be rebuilt, and as a head the tracked body positions in the root frame.
a = the executed joint command (after delay and noise): with it the dynamics are Markov; delay is applied outside
the model, exactly as in the collector. xi = foot friction, PD stiffness scale, hand friction."""
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

NJ = 29
NS = 1 + 6 + 3 + 3 + NJ + NJ  # 71
NROOT = 3  # dyaw, dx, dy (heading frame of step t)


# ---------- rotations (wxyz) ----------
def quat_to_mat(q):
  w, x, y, z = q.unbind(-1)
  return torch.stack([
    1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
    2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
    2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1).reshape(q.shape[:-1] + (3, 3))


def yaw_of(R):
  return torch.atan2(R[..., 1, 0], R[..., 0, 0])


def rot_z(yaw):
  c, s = torch.cos(yaw), torch.sin(yaw)
  o, z = torch.ones_like(c), torch.zeros_like(c)
  return torch.stack([c, -s, z, s, c, z, z, z, o], -1).reshape(yaw.shape + (3, 3))


def six_to_mat(d6):
  a, b = d6[..., 0:3], d6[..., 3:6]
  e1 = a / a.norm(dim=-1, keepdim=True).clamp_min(1e-6)
  b = b - (e1 * b).sum(-1, keepdim=True) * e1
  e2 = b / b.norm(dim=-1, keepdim=True).clamp_min(1e-6)
  e3 = torch.cross(e1, e2, dim=-1)
  return torch.stack([e1, e2, e3], -1)  # columns


def mat_to_six(R):
  return torch.cat([R[..., :, 0], R[..., :, 1]], -1)


# ---------- features from a collected file ----------
def features(rec):
  """rec: dict of torch tensors (T, N, ...) from collect.py -> s (T, N, 71), root (T, N, 3: yaw, x, y),
  body (T, N, B*3) tracked body positions in the root frame."""
  R = quat_to_mat(rec["root_quat"].float())
  yaw = yaw_of(R)
  Rrel = rot_z(yaw).transpose(-1, -2) @ R
  Rt = R.transpose(-1, -2)
  v_b = (Rt @ rec["root_lin_vel"].float().unsqueeze(-1)).squeeze(-1)
  w_b = (Rt @ rec["root_ang_vel"].float().unsqueeze(-1)).squeeze(-1)
  pos = rec["root_pos"].float()
  s = torch.cat([pos[..., 2:3], mat_to_six(Rrel), v_b, w_b, rec["joint_pos"].float(), rec["joint_vel"].float()], -1)
  rel = rec["body_pos"].float() - pos.unsqueeze(-2)
  body = (Rt.unsqueeze(-3) @ rel.unsqueeze(-1)).squeeze(-1).flatten(-2)
  root = torch.stack([yaw, pos[..., 0], pos[..., 1]], -1)
  return s, root, body


def root_step(root_t, root_t1):
  """world (yaw, x, y) at t and t+1 -> (dyaw, dx, dy) in the heading frame of t."""
  dyaw = torch.atan2(torch.sin(root_t1[..., 0] - root_t[..., 0]), torch.cos(root_t1[..., 0] - root_t[..., 0]))
  c, s = torch.cos(root_t[..., 0]), torch.sin(root_t[..., 0])
  dx, dy = root_t1[..., 1] - root_t[..., 1], root_t1[..., 2] - root_t[..., 2]
  return torch.stack([dyaw, c * dx + s * dy, -s * dx + c * dy], -1)


class Sequences:
  """Collected files stored once as flat per-env time series (fp16 on the device); windows are gathered on demand.
  Row i of a flat array = one (env, t); `starts` are the rows from which k steps follow without a reset."""

  def __init__(self, files, k, device="cpu", dtype=torch.float16):
    S, A, B, D, X, ST, F = [], [], [], [], [], [], []
    off = 0
    for f in files:
      z = np.load(f, allow_pickle=False)
      rec = {key: torch.from_numpy(z[key]) for key in ("root_pos", "root_quat", "root_lin_vel", "root_ang_vel",
                                                         "joint_pos", "joint_vel", "body_pos")}
      xi = json.loads(str(z["xi"]))
      s, root, body = features(rec)
      act = torch.from_numpy(z["action"]).float()
      done = torch.from_numpy(z["done"])  # done[t]: the step t -> t+1 ended in a reset
      # at the clip end mjlab's motion command resamples a start frame and teleports the robot WITHOUT done
      # (0.5-1 % of the v1 tracking transitions): a frame jump is a reset too
      fr = torch.from_numpy(z["frame"]).long()
      if (fr >= 0).any():
        done = done.clone()
        done[:-1] |= fr[1:] != fr[:-1] + 1
      T, N = done.shape
      droot = torch.cat([root_step(root[:-1], root[1:]), torch.zeros(1, N, 3)])  # last row unused
      # env-major flat layout: row = n * T + t
      S.append(s.transpose(0, 1).reshape(N * T, -1))
      A.append(act.transpose(0, 1).reshape(N * T, -1))
      B.append(body.transpose(0, 1).reshape(N * T, -1))
      D.append(droot.transpose(0, 1).reshape(N * T, -1))
      X.append(torch.tensor([xi["friction"], xi["kp_scale"], xi["hand_friction"]]).expand(N * T, 3))
      F.append(torch.from_numpy(z["frame"]).transpose(0, 1).reshape(N * T).int())  # reference frame (-1: none)
      # bad[t] = 1 if a reset happens in steps t .. t+k-1 (sliding max over k along time)
      bad = torch.nn.functional.max_pool2d(done.float().T.unsqueeze(0), (1, k), stride=1)[0].T  # (T-k+1, N)
      t0, n0 = torch.nonzero(bad[: T - k] == 0, as_tuple=True)
      ST.append(off + n0 * T + t0)
      off += N * T
    self.k = k
    self.s = torch.cat(S).to(device, dtype)
    self.a = torch.cat(A).to(device, dtype)
    self.body = torch.cat(B).to(device, dtype)
    self.droot = torch.cat(D).to(device, torch.float32)
    self.xi = torch.cat(X).to(device, torch.float32)
    self.starts = torch.cat(ST).to(device)
    self.frame = torch.cat(F).to(device)

  def __len__(self):
    return len(self.starts)

  def windows(self, sel, k=None):
    """windows at the given start indices (into self.starts): dict s/body (W, k+1, .), a/droot (W, k, .), xi."""
    k = k or self.k
    r = self.starts[sel].unsqueeze(1) + torch.arange(k + 1, device=self.starts.device)
    return {"s": self.s[r].float(), "body": self.body[r].float(), "a": self.a[r[:, :k]].float(),
            "droot": self.droot[r[:, :k]], "xi": self.xi[r[:, 0]]}

  def sample(self, bs, gen):
    return self.windows(torch.randint(0, len(self), (bs,), generator=gen, device=self.starts.device))

  def stats_sample(self, n=200000):
    sel = torch.randperm(len(self), device=self.starts.device)[:n]
    return self.windows(sel)


def load_windows(files, k, device="cpu"):
  """All length-(k+1) windows that do not cross a reset, materialised (small sets: tests and evaluation)."""
  seq = Sequences(files, k, device, torch.float32)
  return seq.windows(torch.arange(len(seq), device=seq.starts.device))


# ---------- model ----------
class Norm(nn.Module):
  def __init__(self, dim):
    super().__init__()
    self.register_buffer("mu", torch.zeros(dim))
    self.register_buffer("sd", torch.ones(dim))

  def fit(self, x):
    x = x.reshape(-1, x.shape[-1])
    self.mu.copy_(x.mean(0))
    self.sd.copy_(x.std(0).clamp_min(1e-3))

  def __call__(self, x):
    return (x - self.mu) / self.sd


class WorldModel(nn.Module):
  def __init__(self, nb, hidden=(1024, 1024, 1024)):
    super().__init__()
    self.nb = nb
    self.ns, self.na, self.nx = Norm(NS), Norm(NJ), Norm(3)
    self.nds, self.nbody, self.nroot = Norm(NS), Norm(nb), Norm(NROOT)
    layers, d = [], NS + NJ + 3
    for h in hidden:
      layers += [nn.Linear(d, h), nn.SiLU()]
      d = h
    self.trunk = nn.Sequential(*layers)
    self.head_ds = nn.Linear(d, NS)
    self.head_root = nn.Linear(d, NROOT)
    self.body_head = nn.Sequential(nn.Linear(NS, 512), nn.SiLU(), nn.Linear(512, 512), nn.SiLU(), nn.Linear(512, nb))

  def fit_norms(self, data):
    s, a = data["s"], data["a"]
    self.ns.fit(s)
    self.na.fit(a)
    self.nx.fit(data["xi"])
    self.nds.fit(s[:, 1:] - s[:, :-1])
    self.nbody.fit(data["body"])
    self.nroot.fit(data["droot"])

  def step(self, s, a, xi):
    """one control step: s (.., 71), a (.., 29), xi (.., 3) -> s', droot (dyaw, dx, dy)."""
    h = self.trunk(torch.cat([self.ns(s), self.na(a), self.nx(xi)], -1))
    ds = self.head_ds(h) * self.nds.sd + self.nds.mu
    s1 = s + ds
    s1 = torch.cat([s1[..., :1], mat_to_six(six_to_mat(s1[..., 1:7])), s1[..., 7:]], -1)  # keep a valid rotation
    droot = self.head_root(h) * self.nroot.sd + self.nroot.mu
    return s1, droot

  def body(self, s):
    return self.body_head(self.ns(s)) * self.nbody.sd + self.nbody.mu

  def rollout(self, s0, acts, xi):
    """open loop on given actions: s0 (W, 71), acts (W, H, 29) -> states (W, H+1, 71), droot (W, H, 3)."""
    S, R = [s0], []
    s = s0
    for t in range(acts.shape[1]):
      s, dr = self.step(s, acts[:, t], xi)
      S.append(s)
      R.append(dr)
    return torch.stack(S, 1), torch.stack(R, 1)


def save(model, path, meta):
  torch.save({"state_dict": model.state_dict(), "nb": model.nb, "meta": meta}, path)


def load(path, device="cpu"):
  ck = torch.load(path, map_location=device)
  hidden = tuple(ck["meta"].get("hidden", (1024, 1024, 1024)))
  m = WorldModel(ck["nb"], hidden).to(device)
  m.load_state_dict(ck["state_dict"])
  return m, ck["meta"]
