"""Differentiable forward kinematics of the G1 in torch, built from the mjlab g1.xml MjModel: root pose + 29 joint
angles -> world position / rotation of every body. Lets the imagined env compute the tracking observation and
reward exactly (no learned body head).
Check: python fk.py <collected wm_data file.npz>  (compares with the logged body poses)"""
import sys

import numpy as np
import torch


def quat_to_mat(q):
  w, x, y, z = q.unbind(-1)
  return torch.stack([
    1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
    2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
    2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1).reshape(q.shape[:-1] + (3, 3))


def axis_angle_mat(axis, ang):
  """axis (3,) unit, ang (...) -> (..., 3, 3) Rodrigues"""
  x, y, z = axis
  K = torch.tensor([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=ang.dtype, device=ang.device)
  s, c = torch.sin(ang)[..., None, None], torch.cos(ang)[..., None, None]
  return torch.eye(3, dtype=ang.dtype, device=ang.device) + s * K + (1 - c) * (K @ K)


class G1FK:
  def __init__(self, joint_names, device="cpu"):
    import mujoco
    from mjlab.asset_zoo.robots.unitree_g1.g1_constants import get_spec
    m = get_spec().compile()
    self.names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) for b in range(m.nbody)]
    self.parent = m.body_parentid.copy()
    self.pos = torch.tensor(m.body_pos, dtype=torch.float32, device=device)
    self.rot = quat_to_mat(torch.tensor(m.body_quat, dtype=torch.float32, device=device))
    jn = list(joint_names)
    self.hinges = {}  # body -> list of (index in the 29-vector, axis, anchor)
    for j in range(m.njnt):
      if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
        continue
      n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
      self.hinges.setdefault(int(m.jnt_bodyid[j]), []).append(
        (jn.index(n), tuple(float(v) for v in m.jnt_axis[j]), torch.tensor(m.jnt_pos[j], dtype=torch.float32, device=device)))
    self.root = int(np.nonzero(m.jnt_type == mujoco.mjtJoint.mjJNT_FREE)[0][0])
    self.root_body = int(m.jnt_bodyid[self.root])
    self._levels(device)

  def _levels(self, device):
    """robot bodies grouped by tree depth below the root, for the batched pass (with_vel); one hinge per body at most"""
    nb, depth = len(self.names), {self.root_body: 0}
    for b in range(nb):
      if b != self.root_body and int(self.parent[b]) in depth:
        depth[b] = depth[int(self.parent[b])] + 1
    self.robot = sorted(depth)  # = self.kept of __call__ (ascending body id)
    lv = {}
    for b, d in depth.items():
      if d > 0:
        lv.setdefault(d, []).append(b)
    f = lambda x: torch.tensor(np.array(x), dtype=torch.float32, device=device)
    self.lv = []
    for d in sorted(lv):
      bs = lv[d]
      assert all(len(self.hinges.get(b, [])) <= 1 for b in bs)
      h = [self.hinges.get(b, [(0, (0.0, 0.0, 0.0), torch.zeros(3))])[0] for b in bs]
      self.lv.append({"bodies": bs, "parent": [int(self.parent[b]) for b in bs],
                      "qi": torch.tensor([x[0] for x in h], device=device),
                      "has": f([[1.0 if self.hinges.get(b) else 0.0] for b in bs]),
                      "axis": f([x[1] for x in h]), "anc": torch.stack([x[2].to(device) for x in h]),
                      "pos": self.pos[bs], "rot": self.rot[bs]})

  def with_vel(self, root_pos, root_R, v_root, w_root, q, qd):
    """batched by tree depth, velocities propagated analytically (no jvp): root pose / world twist (..., 3),
    q, qd (..., 29) -> P, V, W (..., nrobot, 3), R (..., nrobot, 3, 3) in the order of self.robot (= __call__)"""
    slot = {self.root_body: 0}
    P, R, V, W = [root_pos[..., None, :]], [root_R[..., None, :, :]], [v_root[..., None, :]], [w_root[..., None, :]]
    n = 1
    for L in self.lv:
      pidx = [slot[p] for p in L["parent"]]
      Pa, Ra, Va, Wa = (torch.cat(x, -3 if x is R else -2) for x in (P, R, V, W))
      pp, Rp, vp, wp = Pa[..., pidx, :], Ra[..., pidx, :, :], Va[..., pidx, :], Wa[..., pidx, :]
      Rf = Rp @ L["rot"]                                    # frame before the hinge
      ang = q[..., L["qi"]] * L["has"][:, 0]
      ax = L["axis"]
      K = torch.zeros(ax.shape[0], 3, 3, device=ax.device)
      K[:, 0, 1], K[:, 0, 2], K[:, 1, 0], K[:, 1, 2], K[:, 2, 0], K[:, 2, 1] = -ax[:, 2], ax[:, 1], ax[:, 2], -ax[:, 0], -ax[:, 1], ax[:, 0]
      s, c = torch.sin(ang)[..., None, None], torch.cos(ang)[..., None, None]
      Rh = torch.eye(3, device=ax.device) + s * K + (1 - c) * (K @ K)
      Rb = Rf @ Rh
      anc_w = pp + (Rp @ L["pos"].unsqueeze(-1)).squeeze(-1) + (Rf @ L["anc"].unsqueeze(-1)).squeeze(-1)
      pb = anc_w - (Rb @ L["anc"].unsqueeze(-1)).squeeze(-1)
      axw = (Rf @ ax.unsqueeze(-1)).squeeze(-1) * (qd[..., L["qi"]] * L["has"][:, 0])[..., None]
      wb = wp + axw
      vb = vp + torch.cross(wp, pb - pp, dim=-1) + torch.cross(axw, pb - anc_w, dim=-1)
      for i, b in enumerate(L["bodies"]):
        slot[b] = n + i
      n += len(L["bodies"])
      P.append(pb); R.append(Rb); V.append(vb); W.append(wb)
    order = [slot[b] for b in self.robot]
    return (torch.cat(P, -2)[..., order, :], torch.cat(R, -3)[..., order, :, :], torch.cat(V, -2)[..., order, :],
            torch.cat(W, -2)[..., order, :])

  def index(self, body_names):
    return [self.names.index(n) for n in body_names]

  def __call__(self, root_pos, root_R, q):
    """root_pos (..., 3), root_R (..., 3, 3), q (..., 29) -> pos (..., nbody, 3), R (..., nbody, 3, 3)"""
    P, Rs = [None] * len(self.names), [None] * len(self.names)
    for b in range(1, len(self.names)):
      if b == self.root_body:
        p, R = root_pos, root_R
      else:
        pp, Rp = P[self.parent[b]], Rs[self.parent[b]]
        if pp is None:  # a static body under the world: not part of the robot
          continue
        p = pp + (Rp @ self.pos[b].unsqueeze(-1)).squeeze(-1)
        R = Rp @ self.rot[b]
        for qi, ax, anc in self.hinges.get(b, []):
          R2 = R @ axis_angle_mat(ax, q[..., qi])
          p = p + ((R - R2) @ anc.unsqueeze(-1)).squeeze(-1)
          R = R2
      P[b], Rs[b] = p, R
    keep = [b for b in range(len(self.names)) if P[b] is not None]
    self.kept = [self.names[b] for b in keep]
    return torch.stack([P[b] for b in keep], -2), torch.stack([Rs[b] for b in keep], -3)


def check(path):
  import json
  z = np.load(path)
  xi = json.loads(str(z["xi"]))
  T = 50
  fk = G1FK(xi["joint_names"])
  rp = torch.tensor(z["root_pos"][:T], dtype=torch.float32)
  rq = torch.tensor(z["root_quat"][:T].astype(np.float32))
  rq = rq / rq.norm(dim=-1, keepdim=True)
  q = torch.tensor(z["joint_pos"][:T].astype(np.float32))
  P, R = fk(rp, quat_to_mat(rq), q)
  idx = [fk.kept.index(n) for n in xi["body_names"]]
  bp = torch.tensor(z["body_pos"][:T].astype(np.float32))
  bq = torch.tensor(z["body_quat"][:T].astype(np.float32))
  bR = quat_to_mat(bq / bq.norm(dim=-1, keepdim=True))
  ep = (P[..., idx, :] - bp).norm(dim=-1)
  ang = torch.rad2deg(torch.arccos((((R[..., idx, :, :].transpose(-1, -2) @ bR).diagonal(dim1=-2, dim2=-1).sum(-1) - 1) / 2).clamp(-1, 1)))
  # the step right after a reset (incl. a clip-end teleport: frame jump) logs the new root but stale body poses
  done = torch.tensor(z["done"][:T])
  fr = torch.tensor(z["frame"][:T].astype(np.int64))
  done[:-1] |= (fr[1:] != fr[:-1] + 1) & (fr[:-1] >= 0)
  ok = torch.cat([torch.ones(1, done.shape[1], dtype=torch.bool), ~done[:-1]])
  bad = torch.nonzero((ep > 0.005) & ok[..., None])
  if len(bad):
    print(json.dumps({"bad_frac": round(len(bad) / ep[ok].numel(), 5), "bad_t": sorted(set(bad[:, 0].tolist()))[:10],
                      "bad_envs": len(set(bad[:, 1].tolist())), "bad_bodies": sorted(set(xi["body_names"][i] for i in bad[:, 2].tolist()))}))
  ep, ang = ep[ok], ang[ok]
  print(json.dumps({"bodies_kept": len(fk.kept), "steps_left_out": int((~ok).sum()),
                    "pos_err_mm_mean": round(ep.mean().item() * 1000, 3), "pos_err_mm_max": round(ep.max().item() * 1000, 3),
                    "ang_err_deg_mean": round(ang.mean().item(), 3), "ang_err_deg_max": round(ang.max().item(), 3)}))


if __name__ == "__main__":
  check(sys.argv[1])
