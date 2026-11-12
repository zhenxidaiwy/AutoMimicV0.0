"""Adapter: the pretrained world model of CuboiLeo/SuperMimic-Reproduced (MIT; release e8-boneseed-100k, 3 x 2048
SiLU MLP trained on BONES-SEED, 100 k iterations) behind the wm.WorldModel interface used by imagine.py / online.py:
step(s, a, xi) -> s', droot with our 71-d heading-invariant state.
Their code is not imported: the network and the integration are re-implemented from their
src/supermimic/world_model/{dynamics.py, state_spec.py} (HEAD ba61053), weights loaded from their checkpoint.
Conversion: our state is heading-invariant, so the step is computed in the heading frame of s (yaw = 0, xy = 0):
their raw state = [p (0, 0, z), R = R_rel, joint pos, v_world = R_rel v_b, w_b, joint vel]; features
[z, rot6d (first two matrix columns, row-major), v in the heading frame, w_b / 2, q, qd / 5]; xi (33) = foot friction,
encoder bias (29), torso CoM offset (3), normalised by (xi - offset) / scale. Output (70, times out_scale):
dv_h, dw_b, dqd, dp_h, dth_b, dq; v' = v + dv_h, w' = w + dw_b, qd' = qd + dqd, p' = p + dt v' + dp_h,
R' = R Exp(dt w' + dth_b), q' = q + dt qd' + dq. Then back to ours: yaw' = heading of R', R_rel' = Rz(yaw')^T R',
v_b' = R'^T v', droot = (yaw', p'_x, p'_y) (heading frame of s).
Their termination head is not used (imagine.py has analytic soft terminations). Their xi has no kp scale or hand
friction: our xi is mapped to (foot friction, zero bias, zero CoM).
Usage: m = load(ckpt, device); s1, dr = m.step(s, a, xi)"""
import pathlib

import torch
import torch.nn as nn

import imagine as im

wm = im.wm
DT = 0.02
IN_SCALE = (1.0, 1.0, 1.0, 2.0, 1.0, 5.0)        # z, rot6d, v_h, w_b, q, qd
OUT_SCALE = (0.3, 0.5, 2.0, 0.01, 0.02, 0.02)    # dv_h, dw_b, dqd, dp_h, dth_b, dq
XI_OFFSET = (0.75,) + (0.0,) * 29 + (0.0,) * 3
XI_SCALE = (0.45,) + (0.01,) * 29 + (0.05,) * 3


def rep(scales, sizes):
  return torch.cat([torch.full((n,), float(s)) for s, n in zip(scales, sizes)])


def exp_so3(r):
  th = r.norm(dim=-1, keepdim=True)[..., None]
  K = im.skew(r)
  small = th < 1e-6
  ths = torch.where(small, torch.ones_like(th), th)
  A = torch.where(small, 1 - th ** 2 / 6, torch.sin(ths) / ths)
  B = torch.where(small, 0.5 - th ** 2 / 24, (1 - torch.cos(ths)) / ths ** 2)
  return torch.eye(3, device=r.device) + A * K + B * (K @ K)


class Fixed:
  """stand-in for wm.Norm (online.py's fit loss): x / sd with mu = 0"""
  def __init__(self, sd):
    self.mu, self.sd = torch.zeros_like(sd), sd

  def __call__(self, x):
    return (x - self.mu) / self.sd


class CuboiWM(nn.Module):
  def __init__(self, hidden=(2048, 2048, 2048)):
    super().__init__()
    layers, d = [], 71 + 29 + 33
    for h in hidden:
      layers += [nn.Linear(d, h), nn.SiLU()]
      d = h
    layers.append(nn.Linear(d, 70))
    self.net = nn.Sequential(*layers)
    self.register_buffer("in_scale", rep(IN_SCALE, (1, 6, 3, 3, 29, 29)))
    self.register_buffer("out_scale", rep(OUT_SCALE, (3, 3, 29, 3, 3, 29)))
    self.register_buffer("xi_off", torch.tensor(XI_OFFSET))
    self.register_buffer("xi_sc", torch.tensor(XI_SCALE))
    # loss scales for online.py's fit (their nominal error scales: pos 0.05, rot 0.1, v 0.5, w 1, q 0.1, qd 2)
    self.ns = Fixed(rep((0.05, 0.1, 0.5, 1.0, 0.1, 2.0), (1, 6, 3, 3, 29, 29)))
    self.nroot = Fixed(torch.tensor([0.1, 0.05, 0.05]))
    self.nb = 0

  def to(self, *args, **kw):
    super().to(*args, **kw)
    dev = self.in_scale.device
    self.ns, self.nroot = Fixed(self.ns.sd.to(dev)), Fixed(self.nroot.sd.to(dev))
    return self

  def xi_map(self, xi):
    """our xi (foot friction, kp scale, hand friction) -> theirs (foot friction, bias 0 x 29, CoM 0 x 3)"""
    z = torch.zeros(xi.shape[:-1] + (32,), device=xi.device)
    return (torch.cat([xi[..., :1], z], -1) - self.xi_off) / self.xi_sc

  def step(self, s, a, xi):
    z, Rrel = s[..., :1], wm.six_to_mat(s[..., 1:7])
    vb, w, q, qd = s[..., 7:10], s[..., 10:13], s[..., 13:42], s[..., 42:71]
    v = (Rrel @ vb.unsqueeze(-1)).squeeze(-1)               # world = heading frame here
    rot6d = Rrel[..., :, :2].reshape(Rrel.shape[:-2] + (6,))
    feat = torch.cat([z, rot6d, v, w, q, qd], -1) / self.in_scale
    d = self.net(torch.cat([feat, a, self.xi_map(xi)], -1)) * self.out_scale
    dv, dw, dqd, dp, dth, dq = d[..., 0:3], d[..., 3:6], d[..., 6:35], d[..., 35:38], d[..., 38:41], d[..., 41:70]
    v1, w1, qd1 = v + dv, w + dw, qd + dqd
    p1 = torch.cat([torch.zeros_like(z), torch.zeros_like(z), z], -1) + DT * v1 + dp
    R1 = Rrel @ exp_so3(DT * w1 + dth)
    q1 = q + DT * qd1 + dq
    yaw1 = wm.yaw_of(R1)
    Rrel1 = wm.rot_z(yaw1).transpose(-1, -2) @ R1
    vb1 = (R1.transpose(-1, -2) @ v1.unsqueeze(-1)).squeeze(-1)
    s1 = torch.cat([p1[..., 2:3], wm.mat_to_six(Rrel1), vb1, w1, q1, qd1], -1)
    return s1, torch.stack([yaw1, p1[..., 0], p1[..., 1]], -1)

  def rollout(self, s0, acts, xi):
    S, R, s = [s0], [], s0
    for t in range(acts.shape[1]):
      s, dr = self.step(s, acts[:, t], xi)
      S.append(s); R.append(dr)
    return torch.stack(S, 1), torch.stack(R, 1)


def load(ckpt, device="cpu"):
  torch.serialization.add_safe_globals([pathlib.PosixPath])  # the pickled config holds paths; nothing else
  sd = torch.load(ckpt, map_location="cpu", weights_only=True)["wm"]
  m = CuboiWM()
  m.net.load_state_dict({k[len("dynamics.mlp.net."):]: v for k, v in sd.items() if k.startswith("dynamics.mlp.net.")})
  return m.to(device)
