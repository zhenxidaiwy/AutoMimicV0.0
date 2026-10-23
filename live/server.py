"""WSL side of the live demo: receive webcam keypoints over TCP, run skill retrieval (10 Hz) + one-brain tracker
(50 Hz, wall-clock paced) in simulation, stream rendered robot frames back.
Falls: the robot state is handed to the learned get-up policy (a second env with the same robot: same step dt,
joint order, default pose and action scale), which gets it up; after 1 s of stable standing the state is handed
back to the dancer (yaw re-centred onto the reference, with a display transform so the rendered robot does not
jump). --no_getup restores the old behaviour (teleport back to a standing frame). --push_at injects test pushes.

Protocol (single TCP connection, client = Windows cam_client.py):
  client -> server : newline-delimited JSON  {"t": float_seconds, "wh": [w, h], "kp": [[x, y, conf] * 17] or null}
  server -> client : repeated [4-byte big-endian length][JSON header] [4-byte length][JPEG bytes]
                     header: {"dance", "dance_p", "phase", "loop_ms", "rt_factor", "fell_count"}
Usage (unitree_rl_mjlab env):
  python server.py --ckpt <tracker.pt> --watch ret_lead0_s0 [--port 5577]
  python server.py --ckpt <tracker.pt> --bench gym_sss       # no network: replay a clip's keypoints, report timing
"""
import argparse
import dataclasses
import json
import socket
import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(HERE.parent / "vla"))
sys.path.insert(0, str(HERE.parent / "rl"))

DANCE_EN = {0: "Shan Shen Bu", 1: "Gou Xiong Duo Suo Mao"}


class KpBuffer:
  """Thread-safe buffer of (t, kp(17,3)); window() resamples the last W seconds onto a 30 fps grid."""

  def __init__(self):
    self.q = deque(maxlen=300)
    self.lock = threading.Lock()

  def push(self, t, kp):
    with self.lock:
      self.q.append((t, kp))

  def latest_t(self):
    with self.lock:
      return self.q[-1][0] if self.q else -1e9

  def clear(self):
    with self.lock:
      self.q.clear()

  def window(self, now, n=30, span=1.0):
    import numpy as np
    with self.lock:
      items = list(self.q)
    if len(items) < 2:
      return None
    ts = np.array([t for t, _ in items])
    kps = np.stack([k for _, k in items])
    grid = np.linspace(now - span + span / n, now, n)
    out = np.empty((n, 17, 3), np.float32)
    for j in range(17):
      for c in range(3):
        out[:, j, c] = np.interp(grid, ts, kps[:, j, c])
    return out


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--watch", default="ret_lead0_s0")
  ap.add_argument("--motion", default=str(Path.home() / "projects/dance/multi/canon_v1.npz"))
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--port", type=int, default=5577)
  ap.add_argument("--bench", default=None, help="clip id: replay its causal keypoints instead of the network")
  ap.add_argument("--bench_seconds", type=float, default=0, help="bench: loop the clip for at least this long")
  ap.add_argument("--render_every", type=int, default=2)
  ap.add_argument("--size", type=int, default=480)
  ap.add_argument("--jpeg", action="store_true", help="render on the server and send JPEGs (slow under WSL)")
  ap.add_argument("--getup_ckpt", default=str(HERE.parent / "policies" / "getup_auto_r08" / "policy.pt"))
  ap.add_argument("--getup_task", default="Dance-Recovery-G1-auto")
  ap.add_argument("--no_getup", action="store_true", help="old behaviour: teleport back to a standing frame")
  ap.add_argument("--push_at", default="", help="comma-separated sim times (s) of a test push while dancing")
  ap.add_argument("--trace", action="store_true", help="log the retrieval output twice a second")
  ap.add_argument("--dance_ckpts", default="",
                  help="per-dance specialist trackers, e.g. '0=<sss policy.pt>,1=<gxdsm policy.pt>' (same obs as --ckpt; "
                       "they track the same canonical clips); dances not listed use --ckpt")
  # default "routine" (user's design): recognise the start of a learned dance, replay the whole learned clip with
  # the specialist tracker, only then look at the person again. ("commit" did not raise the step amplitude and
  # lowered the agreement with the person's state from 88% to 73%; "snap" = the original per-prediction jumps.)
  # trigger (live/trigger_eval.py, robust_eval.py): one recognition at conf 0.7 -> 19 false triggers on 8/9 negative
  # videos; requiring 0.5 s of CONSECUTIVE recognitions was too brittle online (positives 1/6), hence the time vote
  # robust_eval (4 jitter seeds x 9 negative / 12 positive videos): 1 tick @0.7 -> 86 false triggers, 36/48 right;
  # this vote + open_s0 window veto -> 5 false triggers (广场舞 4, jumping jacks 1), 48/48 right, median 1.6 s
  ap.add_argument("--trigger_conf", type=float, default=0.9, help="routine: min dance confidence of a vote")
  ap.add_argument("--trigger_win", type=float, default=0.8, help="routine: vote window (s, wall clock)")
  ap.add_argument("--trigger_frac", type=float, default=0.7, help="routine: min fraction of votes in the window")
  # open_s6 = AIST++ + real negatives batch 1 + 7 extra dancers (POS_ANY): held-out batch 2 @0.5 -> 5 false
  # triggers / 48 runs (5.9 s of wrong dancing), positives 48/48 (open_s0: 12 and 47/48)
  ap.add_argument("--veto_watch", default="open_s6",
                  help="open-set recogniser ('other motion' class) used only to veto triggers; '' = none")
  # held-out negatives batch 2 (12 videos x 4 jitter seeds): open_s0 @0.5 -> 12 false triggers, positives 47/48
  # (old rule: 117, 36/48); recognisers trained with real negatives reach 0 but lose 狗熊哆嗦毛 performers
  ap.add_argument("--other_mean", type=float, default=0.5,
                  help="veto a trigger if the mean 'other' probability over the vote window is >= this")
  ap.add_argument("--trigger_span", type=float, default=0.5, help="routine: min time between first and last vote (s)")
  ap.add_argument("--trigger_adv", type=float, default=0.3,
                  help="routine: the recognised canonical frame must advance >= this x real time over the votes")
  ap.add_argument("--trace_ticks", action="store_true", help="log every recognition tick of the trigger")
  ap.add_argument("--trigger_back", type=float, default=6.0,
                  help="routine: max backwards jump of the recognised canonical frame between ticks (30 fps frames)")
  ap.add_argument("--other_max", type=float, default=1.01,
                  help="max per-recognition 'other motion' probability of a vote (1.01 = off; the window veto is used)")
  ap.add_argument("--min_idle", type=float, default=0.2,
                  help="routine: the robot must have been standing this long before a new replay starts (s)")
  ap.add_argument("--stop_after", type=float, default=0.85,
                  help="routine: stop a person-started replay after the person has not been doing that dance this long (s)")
  ap.add_argument("--playback", choices=("routine", "commit", "snap", "oracle"), default="routine",
                  help="commit: play a recognised move's whole canonical segment; snap: jump to every prediction; "
                       "oracle (bench): ignore the person, play the canonical clip continuously (tracker ceiling)")
  ap.add_argument("--rec", default="", help="bench: save a per-tick timeline (npz) for latency / amplitude analysis")
  ap.add_argument("--push_force", type=float, default=600.0,
                  help="push: force (N) on the side of the torso at shoulder height, for 0.2 s")
  a = ap.parse_args()

  from dataclasses import asdict

  import cv2
  import numpy as np
  import torch
  from scipy.spatial.transform import Rotation as Rot

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  from data import build_clip, normalise
  from phase_rsi import PhaseMotionCommandCfg
  from train_retrieve import CANON_PHASE, STATE_DANCE, STATE_FRAME, RetrieveNet

  dev = "cuda:0"
  mfile = np.load(a.motion)
  names = [str(x) for x in mfile["clip_names"]]
  starts = {n: int(np.where(mfile["clip_id"] == i)[0][0]) for i, n in enumerate(names)}
  lens = {n: int((mfile["clip_id"] == i).sum()) for i, n in enumerate(names)}
  dance_clip = {0: "bda_zhao_sss", 1: "bda2_gxdsm_full"}
  dance_name = {0: "闪身步", 1: "狗熊哆嗦毛"}
  STAND = {(0, 60.0), (0, 34.0), (1, 5.0), (1, 225.0)}

  env_cfg = load_env_cfg(a.task, play=True)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = 1
  env_cfg.terminations = {}
  env_cfg.viewer.height = env_cfg.viewer.width = a.size
  old = env_cfg.commands["motion"]
  kw = {f.name: getattr(old, f.name) for f in dataclasses.fields(old) if f.init}
  kw.update(motion_file=a.motion, sampling_mode="start")
  env_cfg.commands["motion"] = PhaseMotionCommandCfg(**kw)
  env = ManagerBasedRlEnv(cfg=env_cfg, device=dev, render_mode="rgb_array" if a.jpeg else None)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  dance_policy = {0: policy, 1: policy}
  for item in filter(None, a.dance_ckpts.split(",")):  # specialists: one runner per checkpoint, same env
    dk, path = item.split("=", 1)
    r = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
    r.load(path, load_cfg={"actor": True}, strict=True, map_location=dev)
    dance_policy[int(dk)] = r.get_inference_policy(device=dev)
    print(f"[server] dance {dk} tracker: {path}", flush=True)
  cmd = env.command_manager.get_term("motion")
  ws = torch.load(Path.home() / "projects/dance/vla/runs" / a.watch / "model.pt", weights_only=False)
  if ws.get("open"):  # open-set recogniser: one extra "other motion" class
    from train_retrieve_open import OpenNet
    net = OpenNet().to(dev).eval()
  else:
    net = RetrieveNet().to(dev).eval()
  net.load_state_dict(ws["model"])
  print(f"[server] recogniser {a.watch} ({'open-set' if ws.get('open') else 'closed-set'})", flush=True)
  vnet = None
  if a.veto_watch:
    from train_retrieve_open import OpenNet
    vws = torch.load(Path.home() / "projects/dance/vla/runs" / a.veto_watch / "model.pt", weights_only=False)
    vnet = OpenNet().to(dev).eval()
    vnet.load_state_dict(vws["model"])
    print(f"[server] trigger veto recogniser {a.veto_watch}", flush=True)
  sd = {d: torch.tensor(STATE_DANCE == d, device=dev) for d in (0, 1)}

  def segments(ph):  # contiguous non-"stand" runs of a canonical clip's phase list (30 fps frames)
    out, i = [], 0
    while i < len(ph):
      if ph[i] != "stand":
        j = i
        while j < len(ph) and ph[j] != "stand":
          j += 1
        out.append((i, j - 1))
        i = j
      else:
        i += 1
    return out
  segs = {d: segments(CANON_PHASE[dance_name[d]]) for d in (0, 1)}

  def seg_of(d, f30):
    for k, (s0, s1) in enumerate(segs[d]):
      if s0 <= f30 <= s1:
        return k
    return None
  commit = None  # (dance, segment index, end frame at 50 fps) of the move being played
  routine = None  # (dance, end frame at 50 fps) of the full learned clip being replayed
  print(f"[server] playback={a.playback}; canonical move segments (30 fps): {segs}", flush=True)

  def to50(dance, f30):
    c = dance_clip[dance]
    return float(np.clip(starts[c] + f30 * 50 / 30, starts[c], starts[c] + lens[c] - 2))

  def place_at(p):
    T = int(cmd.motion.time_step_total)
    onehot = torch.zeros(T, device=dev)
    onehot[int(p)] = 1
    saved = cmd.cfg.sampling_mode, cmd.frame_prior_eff
    cmd.cfg.sampling_mode, cmd.frame_prior_eff = "uniform", onehot
    cmd._resample_command(torch.arange(1, device=dev))
    cmd.cfg.sampling_mode, cmd.frame_prior_eff = saved

  n_states = len(STATE_DANCE)
  other_p = [0.0]  # "other motion" probability of the last prediction (0 for the closed-set recogniser)

  def predict(win):
    x = torch.tensor(normalise(win).reshape(1, 30, -1), device=dev)
    with torch.no_grad():
      pr = net(x).softmax(-1)[0]
      own_other = float(pr[n_states:].sum())  # 0 for the closed-set recogniser
      other_p[0] = own_other if vnet is None else float(vnet(x).softmax(-1)[0, n_states:].sum())
    # renormalise by the recogniser's OWN 'other' mass (dividing by the veto net's gave confidences > 1)
    pr = pr[:n_states] / max(1e-9, 1.0 - own_other)
    pd = [float(pr[sd[d]].sum()) for d in (0, 1)]
    d = int(np.argmax(pd))
    m = pr.clone()
    m[~sd[d]] = 0
    return int(m.argmax()), pd[d]

  buf = KpBuffer()
  conn_ref, send_lock = [None], threading.Lock()  # current client (the web app reconnects for every new source)
  commands = deque()  # "push" / "reset" from the client

  def send(header, jpeg=b""):
    conn = conn_ref[0]
    if conn is None:
      return
    h = json.dumps(header).encode()
    try:
      with send_lock:
        conn.sendall(struct.pack(">I", len(h)) + h + struct.pack(">I", len(jpeg)) + jpeg)
    except OSError:
      conn_ref[0] = None

  robot = cmd.robot
  origin = env.scene.env_origins[0]

  # ---- learned get-up: a second env with the same robot, the state is handed over on a fall and back when stable
  from mjlab.utils.lab_api.math import quat_apply, quat_apply_inverse, quat_mul
  genv = grobot = gpolicy = gvenv = None
  if not a.no_getup:
    import os
    os.environ.setdefault("GETUP_KNOBS", str(Path(a.getup_ckpt).parent / "knobs.json"))
    import getup  # noqa: F401  (registers the get-up tasks)
    gcfg = load_env_cfg(a.getup_task, play=True)
    gcfg.scene.num_envs = 1
    gcfg.terminations = {}
    genv = ManagerBasedRlEnv(cfg=gcfg, device=dev)
    gagent = load_rl_cfg(a.getup_task)
    gvenv = RslRlVecEnvWrapper(genv, clip_actions=gagent.clip_actions)
    grunner = (load_runner_cls(a.getup_task) or MjlabOnPolicyRunner)(gvenv, asdict(gagent), device=dev)
    grunner.load(a.getup_ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
    gpolicy = grunner.get_inference_policy(device=dev)
    genv.reset()
    grobot = genv.scene["robot"]
    assert list(grobot.joint_names) == list(robot.joint_names), "dancer / get-up joint order differ"
    print(f"[server] get-up policy {a.getup_ckpt}", flush=True)
  i_anchor = list(robot.body_names).index(cmd.cfg.anchor_body_name)

  def yaw_of(q):  # wxyz -> yaw (rad)
    w, x, y, z = [float(v) for v in q]
    return float(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))

  def hand_over(src, dst_env, dyaw=0.0):
    """Copy the robot state src -> dst_env's robot (optionally rotated by dyaw about the root), reset dst's action
    history, refresh its derived quantities."""
    sd, dst = src.data, dst_env.scene["robot"]
    pos, quat = sd.root_link_pos_w.clone(), sd.root_link_quat_w.clone()
    lin, ang = sd.root_link_lin_vel_w.clone(), sd.root_link_ang_vel_w.clone()
    if dyaw:
      qz = torch.tensor([[np.cos(dyaw / 2), 0.0, 0.0, np.sin(dyaw / 2)]], device=dev, dtype=quat.dtype)
      quat, lin, ang = quat_mul(qz, quat), quat_apply(qz, lin), quat_apply(qz, ang)
    dst.write_root_link_pose_to_sim(torch.cat([pos, quat], -1))
    dst.write_root_link_velocity_to_sim(torch.cat([lin, ang], -1))
    dst.write_joint_state_to_sim(sd.joint_pos.clone(), sd.joint_vel.clone())
    am = dst_env.action_manager
    for t in (am._action, am._prev_action, am._prev_prev_action):
      t.zero_()
    dst_env.sim.forward()

  # display transform (2D rigid, homogeneous 3x3): what the client sees = disp @ simulation; re-centring the yaw
  # when the dancer takes over again changes the simulation pose, disp absorbs it so the rendered robot is continuous
  disp = np.eye(3)

  def show(pos, quat, joints):
    th = np.arctan2(disp[1, 0], disp[0, 0])
    xy = disp @ np.array([pos[0], pos[1], 1.0])
    qz = np.array([np.cos(th / 2), 0, 0, np.sin(th / 2)])
    w1, x1, y1, z1 = qz
    w2, x2, y2, z2 = quat
    q = [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
         w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]
    return [float(xy[0]), float(xy[1]), float(pos[2])] + [float(v) for v in q] + list(joints)

  def robot_qpos(r=None):
    if r is None:
      r = robot
    pos = (r.data.body_link_pos_w[0, 0] - origin).tolist()
    quat = r.data.body_link_quat_w[0, 0].tolist()  # wxyz
    return show(pos, quat, r.data.joint_pos[0].tolist())

  def ref_qpos():
    pos = (cmd.body_pos_w[0, 0] - origin).tolist()  # body 0 of the tracked list = pelvis
    return show(pos, cmd.body_quat_w[0, 0].tolist(), cmd.joint_pos[0].tolist())

  if a.bench:
    clip = build_clip(a.bench, 0, causal=True)
    kp_all = clip["kp"][0]
    t_start = time.time()

    duration = max(len(kp_all) / 30, a.bench_seconds)

    def feeder():  # replays the clip's keypoints in real time, looping until the bench duration is over
      i = 0
      while time.time() - t_start < duration:
        while time.time() - t_start < i / 30:
          time.sleep(0.002)
        buf.push(time.time(), kp_all[i % len(kp_all)])
        i += 1
    threading.Thread(target=feeder, daemon=True).start()
  else:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", a.port))
    srv.listen(1)
    print(f"[server] waiting for the camera client on port {a.port} ...", flush=True)

    def receiver(conn):
      t_off = [None]  # client clock -> server clock offset (first message of this connection)
      try:
        for line in conn.makefile("r"):
          try:
            m = json.loads(line)
          except json.JSONDecodeError:
            continue
          if "cmd" in m:
            commands.append(m["cmd"])
            continue
          if m.get("kp") is None:
            continue
          if t_off[0] is None:
            t_off[0] = time.time() - m["t"]
          buf.push(m["t"] + t_off[0], np.array(m["kp"], np.float32))
      except OSError:
        pass
      if conn_ref[0] is conn:
        conn_ref[0] = None
      print("[server] client disconnected", flush=True)

    def acceptor():  # one client at a time; a new connection replaces the old one
      while True:
        c, addr = srv.accept()
        c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        old = conn_ref[0]
        buf.clear()
        conn_ref[0] = c
        if old is not None:
          try:
            old.close()
          except OSError:
            pass
        print(f"[server] client connected from {addr}", flush=True)
        threading.Thread(target=receiver, args=(c,), daemon=True).start()
    threading.Thread(target=acceptor, daemon=True).start()
    duration = float("inf")

  env.reset()
  dance, p, rate = 0, to50(0, 60.0), 0.0
  place_at(p)
  obs = venv.get_observations()
  info = {"dance": 0, "dance_p": 0.0, "phase": "stand"}
  # routine playback: while waiting the robot stands under the get-up policy (trained to stand still, no stepping);
  # the dance specialists only ever run from a stand into a complete learned clip (their best case)
  idle_genv = a.playback == "routine" and genv is not None

  def to_dancer():
    """Hand the standing robot from the get-up env to the dancer env at the current reference frame p (yaw
    re-centred onto the reference, display transform absorbs it)."""
    nonlocal disp, obs
    pi = int(round(p))
    cmd.time_steps[:] = pi - 1
    cmd.cur_end[:] = cmd.clip_end[pi]
    dyaw = yaw_of(cmd.anchor_quat_w[0]) - yaw_of(grobot.data.body_link_quat_w[0, i_anchor])
    c0 = (grobot.data.root_link_pos_w[0, :2] - origin[:2]).cpu().numpy()
    T = np.array([[np.cos(dyaw), -np.sin(dyaw), 0], [np.sin(dyaw), np.cos(dyaw), 0], [0, 0, 1]])
    Tc = np.array([[1, 0, c0[0]], [0, 1, c0[1]], [0, 0, 1]]) @ T @ np.array([[1, 0, -c0[0]], [0, 1, -c0[1]], [0, 0, 1]])
    hand_over(grobot, env, dyaw)
    disp = disp @ np.linalg.inv(Tc)
    obs = venv.get_observations()
  dt = env.step_dt
  t0, s, fell_count, loop_ms = time.time(), 0, 0, deque(maxlen=50)
  prof = {k: deque(maxlen=100) for k in ("policy", "step", "render", "jpeg")}
  mode, g_t, g_stable, gobs, push_count = "dance", 0.0, 0, None, 0
  forced = None  # dance requested by a web button
  not_doing = 0.0  # how long the person has not been doing the replayed dance (s)
  trig_hist = []  # (wall time, dance, canonical frame, votes?) of the recognitions in the last trigger_win s
  idle_t = 0.0  # how long the robot has been standing under the stand controller (s)
  seen = "nobody"  # what the recogniser currently sees (shown in the web page)
  push_state, push_vis, push_tail = None, None, None
  rec, last_pred = ([] if a.rec else None), (0, -1.0)
  t_feed0 = t_start if a.bench else time.time()
  i_torso = list(robot.body_names).index("torso_link")
  push_times = sorted(float(x) for x in a.push_at.split(",") if x.strip())
  events, getup_times = [], []

  class _Events(list):  # print every event at once (in live mode the server is killed, never reaching the summary)
    def append(self, e):
      super().append(e)
      print(f"[server] event t={e[0]:.2f}s {e[1]}", flush=True)
  events = _Events()
  if idle_genv:  # start standing under the get-up policy
    hand_over(robot, genv)
    gobs = gvenv.get_observations()
    mode = "idle"

  def start_routine(d, why):
    """Replay dance d's whole learned clip from its first frame with its specialist tracker (from a stand)."""
    nonlocal p, rate, routine, mode, dance, info, not_doing
    c = dance_clip[d]
    # routine = (dance, end frame, started by the person?) - only person-started replays stop when the person stops
    dance, p, rate, routine = d, float(starts[c]), 1.0, (d, starts[c] + lens[c] - 3, not why.startswith("button"))
    not_doing = 0.0
    info = {**info, "dance": d, "dance_p": 1.0 if why.startswith("button") else info.get("dance_p", 0.0)}
    events.append((round(s * dt, 2), f"{why} {DANCE_EN[d]} -> full replay"))
    if mode == "idle":  # stand (get-up policy) -> dancer, from the clip's first frame
      to_dancer()
      mode = "dance"

  def apply_push(pr):
    """One step of the push on robot entity pr: approach 0.35 s -> contact (force on the torso side at shoulder
    height) 0.2 s -> release 0.4 s. Returns the arrow / contact point for the client (display frame)."""
    nonlocal push_state
    tp = push_state["t"]
    stage, u = (("approach", tp / 0.35) if tp < 0.35 else ("contact", (tp - 0.35) / 0.2) if tp < 0.55
                else ("release", (tp - 0.55) / 0.4))
    tq = pr.data.body_link_quat_w[0, i_torso:i_torso + 1]
    side = push_state["side"]
    pt = pr.data.body_link_pos_w[0, i_torso] + quat_apply(tq, torch.tensor([[0.0, 0.11 * side, 0.22]], device=dev))[0]
    lat = quat_apply(tq, torch.tensor([[0.0, side, 0.0]], device=dev))[0]
    dvec = -torch.cat([lat[:2], lat.new_zeros(1)])
    dvec = dvec / dvec.norm().clamp(min=1e-6)  # horizontal, from that side towards the body
    f = torch.zeros(1, 1, 3, device=dev)
    tau = torch.zeros(1, 1, 3, device=dev)
    if stage == "contact":
      f[0, 0] = dvec * a.push_force
      tau[0, 0] = torch.linalg.cross(pt - pr.data.body_com_pos_w[0, i_torso], f[0, 0])
    pr.write_external_wrench_to_sim(f, tau, body_ids=[i_torso])
    pd = disp @ np.array([float(pt[0] - origin[0]), float(pt[1] - origin[1]), 1.0])
    dd = disp[:2, :2] @ dvec[:2].cpu().numpy()
    push_state["t"] += dt
    if push_state["t"] >= 0.95:
      push_state = None
    return {"stage": stage, "u": round(min(u, 1.0), 3), "p": [float(pd[0]), float(pd[1]), float(pt[2] - origin[2])],
            "d": [float(dd[0]), float(dd[1]), 0.0]}
  print("[server] running", flush=True)
  while time.time() - t0 < duration:
    tick = time.time()
    while commands:  # from the client (web app buttons)
      c = commands.popleft()
      if c == "push" and mode in ("dance", "idle"):
        push_times.insert(0, 0.0)  # = now
      elif c in ("dance0", "dance1"):  # web button: dance this now (or right after the current replay / get-up)
        forced = int(c[-1])
        events.append((round(s * dt, 2), f"button: {DANCE_EN[forced]} requested"))
      elif c == "reset":  # new session: standing frame (teleport), display transform and counters cleared
        mode, p, rate, commit, routine = "dance", to50(dance, 60.0 if dance == 0 else 5.0), 0.0, None, None
        place_at(p)
        obs = venv.get_observations()
        disp = np.eye(3)
        if idle_genv:
          hand_over(robot, genv)
          gobs = gvenv.get_observations()
          mode = "idle"
        fell_count, push_count, getup_times = 0, 0, []
        push_state, push_vis = None, None
        robot.write_external_wrench_to_sim(torch.zeros(1, 1, 3, device=dev), torch.zeros(1, 1, 3, device=dev),
                                           body_ids=[i_torso])
        del events[:]
        events.append((round(s * dt, 2), "reset"))
    idle_t = idle_t + dt if mode == "idle" else 0.0  # time since the robot was handed to the stand controller
    if forced is not None and routine is None and ((mode == "idle" and idle_t >= a.min_idle)
                                                   or (mode == "dance" and not idle_genv)):
      start_routine(forced, "button:")
      forced = None
    if a.playback == "oracle":  # tracker ceiling: canonical clip played continuously, no retrieval
      c0 = dance_clip[dance]
      if s == 0 or p >= starts[c0] + lens[c0] - 3:
        p = float(starts[c0])
      rate = 1.0
    elif s % 5 == 0:
      now = time.time()
      if routine is not None and mode == "dance" and routine[2]:
        # replay started by the person: keep recognising (the motion is NOT refreshed); if the person has not been
        # doing this dance for stop_after s in a row (other dance, a stand state, nobody / no legs visible) -> stand
        doing = False
        if now - buf.latest_t() <= 0.5:
          win = buf.window(min(now, buf.latest_t()))
          if win is not None and float(win[:, 11:17, 2].mean()) >= 0.4:
            k, conf = predict(win)
            d_, f_ = int(STATE_DANCE[k]), float(STATE_FRAME[k])
            last_pred = (d_, f_)
            doing = (d_ == routine[0] and seg_of(d_, f_) is not None and (d_, f_) not in STAND
                     and other_p[0] < a.other_max)
            info = {**info, "dance_p": round(conf, 3)}
            ph_ = CANON_PHASE[dance_name[d_]][int(round(f_))]
            seen = ("stand" if not (seg_of(d_, f_) is not None and (d_, f_) not in STAND)
                    else f"{DANCE_EN[d_]}: {ph_}") + f" ({conf:.0%})"
          else:
            seen = "legs not visible"
        else:
          seen = "nobody"
        not_doing = 0.0 if doing else not_doing + 5 * dt
        if not_doing >= a.stop_after - 1e-6:
          events.append((round(s * dt, 2), f"person not doing {DANCE_EN[routine[0]]} for {a.stop_after:.2f} s -> stand"))
          routine, rate = None, 0.0
          p = to50(dance, 60.0 if dance == 0 else 5.0)
          if idle_genv:  # stand under the get-up policy and keep watching
            hand_over(robot, genv)
            gobs = gvenv.get_observations()
            mode = "idle"
          info = {**info, "phase": "watching (standing)"}
      elif routine is not None:  # replay started by a button (or not dancing): runs to the end
        pass
      elif now - buf.latest_t() > 0.5:  # nobody visible: stand
        p, rate, commit, trig_hist = to50(dance, 60.0 if dance == 0 else 5.0), 0.0, None, []
        info = {"dance": dance, "dance_p": 0.0, "phase": "waiting for a person"}
        seen = f"nobody (newest keypoints {min(now - buf.latest_t(), 99):.1f} s old)"
        if a.trace and s % 25 == 0:
          print(f"[trace] t={s * dt:6.2f} waiting: newest keypoints are {now - buf.latest_t():.2f} s old", flush=True)
      else:
        # the window ends at the newest keypoints (as in training), not at `now`: keypoints arrive 0.1-0.2 s late
        # (YOLO + transport), and np.interp would freeze the window's tail on the last pose (online flashes were
        # recognised for 3 ticks instead of 8)
        win = buf.window(min(now, buf.latest_t()))
        if win is not None and float(win[:, 11:17, 2].mean()) < 0.4:
          # legs not visible (e.g. sitting close to the laptop): the model was only trained on full-body views
          p, rate, commit, trig_hist = to50(dance, 60.0 if dance == 0 else 5.0), 0.0, None, []
          info = {"dance": dance, "dance_p": 0.0, "phase": "legs not visible - step back"}
          seen = "legs not visible"
          win = None
        if win is not None:
          k, conf = predict(win)
          d, f30 = int(STATE_DANCE[k]), float(STATE_FRAME[k])
          last_pred = (d, f30)
          q = to50(d, f30)
          if a.playback == "routine":
            # recognise the START of a learned dance, then replay its whole learned clip from the beginning with
            # the specialist tracker; the person is ignored until the clip is over, then recognition resumes
            settled = mode != "idle" or idle_t >= a.min_idle  # just handed back to the stand controller: settle first
            if routine is None and mode in ("idle", "dance"):  # never while getting up
              # trigger (vote over wall-clock time, = trigger_eval.py "vote"): over the recognitions of the last
              # trigger_win s, >= trigger_frac show a moving state of a dance (confident, not "other"), those span
              # >= trigger_span s, are all the same dance and their canonical frame runs forward
              good = (seg_of(d, f30) is not None and (d, f30) not in STAND and conf >= a.trigger_conf
                      and other_p[0] < a.other_max)
              trig_hist = [h for h in trig_hist + [(now, d, f30, good, other_p[0])] if now - h[0] <= a.trigger_win + 1e-6]
              votes = [h for h in trig_hist if h[3]]
              om = float(np.mean([h[4] for h in trig_hist]))
              ok = (good and settled and len(votes) >= 2 and len(votes) >= a.trigger_frac * len(trig_hist)
                    and votes[-1][0] - votes[0][0] >= a.trigger_span - 1e-6 and len({h[1] for h in votes}) == 1
                    and min(np.diff([h[2] for h in votes])) >= -a.trigger_back
                    and votes[-1][2] - votes[0][2] >= a.trigger_adv * 30 * (votes[-1][0] - votes[0][0])
                    and om < a.other_mean)
              if a.trace_ticks:
                print(f"[tick] t={s * dt:6.2f} d={d} f30={f30:5.1f} conf={conf:.2f} other={other_p[0]:.2f} "
                      f"good={int(good)} votes={len(votes)}/{len(trig_hist)} other_mean={om:.2f} ok={int(ok)}",
                      flush=True)
              if ok:
                trig_hist = []
                start_routine(d, "recognised")
              elif mode == "dance":
                p, rate = to50(d, 60.0 if d == 0 else 5.0), 0.0  # (no idle controller) stand frame
            elif routine is not None:
              d = routine[0]  # keep playing the recognised dance
          elif a.playback == "snap":  # original controller: jump to every new prediction
            if (d, f30) in STAND:
              p, rate = q, 0.0
            elif d != dance or abs(q - p) > 12:
              p, rate = q, 1.0
            else:
              rate = float(np.clip(1.0 + (q - p) / 10.0, 0.3, 2.0))
          else:  # "commit": once a move starts, play its whole canonical segment without jumps
            if commit is not None and commit[0] != d:  # the person switched dances
              commit = None
            sg = seg_of(d, f30)
            if commit is not None and commit[0] == d and (sg is None or sg == commit[1]
                                                          or len(segs[d]) == 1):
              # keep playing the committed segment; only the speed follows the person (no jumps)
              ahead = q - p if sg == commit[1] else 0.0
              if len(segs[d]) == 1 and abs(ahead) > 40:  # one long segment (狗熊哆嗦毛): re-sync if far off
                p = q
              rate = float(np.clip(1.0 + ahead / 25.0, 0.7, 1.6))
            elif sg is None or (d, f30) in STAND:
              if commit is None:
                p, rate = q, 0.0  # standing: hold the stand frame
            else:  # a new move starts: from (almost) where the person is in it, never past its middle
              s0, s1 = segs[d][sg]
              f_start = min(max(s0, f30 - 3), s0 + (s1 - s0) // 3)
              p, rate, commit = to50(d, f_start), 1.0, (d, sg, to50(d, s1))
          dance = d
          info = {"dance": d, "dance_p": round(conf, 3), "phase": CANON_PHASE[dance_name[d]][int(round(f30))]}
          seen = ("stand" if (d, f30) in STAND or seg_of(d, f30) is None
                  else f"{DANCE_EN[d]}: {info['phase']}") + f" ({conf:.0%})"
          if a.trace and s % 25 == 0:  # retrieval trace (2 Hz): what the model sees vs what the robot plays
            print(f"[trace] t={s * dt:6.2f} mode={mode} dance={d} f30={f30:5.1f} phase={info['phase']:<8} "
                  f"conf={conf:.2f} p={p:7.1f} rate={rate:.2f} stand_state={(d, f30) in STAND}", flush=True)
    if mode == "dance":
      if push_times and s * dt >= push_times[0] and push_state is None:  # start a push (alternating sides)
        push_times.pop(0)
        push_state = {"t": 0.0, "side": 1.0 if push_count % 2 == 0 else -1.0}
        push_count += 1
        events.append((round(s * dt, 2), "push " + ("from the left" if push_state["side"] > 0 else "from the right")))
      push_vis = apply_push(robot) if push_state is not None else None
      pi = int(round(p))
      cmd.time_steps[:] = pi - 1
      cmd.cur_end[:] = cmd.clip_end[pi]
      tp0 = time.time()
      with torch.no_grad():
        act = dance_policy[dance](obs)
        torch.cuda.synchronize()
        tp1 = time.time()
        obs, _, _, _ = venv.step(act)
        torch.cuda.synchronize()
      prof["policy"].append(tp1 - tp0)
      prof["step"].append(time.time() - tp1)
      c = dance_clip[dance]
      p = min(p + rate, starts[c] + lens[c] - 2)
      if commit is not None and p >= commit[2]:  # the committed move is finished: hold until the next one
        commit, rate = None, 0.0
      if routine is not None:
        ph = CANON_PHASE[dance_name[dance]]
        info = {**info, "dance": dance,
                "phase": "replay " + ph[int(np.clip((p - starts[c]) * 30 / 50, 0, len(ph) - 1))]}
        if p >= routine[1]:  # whole learned clip replayed: back to a stand frame, recognition resumes
          routine, rate = None, 0.0
          p = to50(dance, 60.0 if dance == 0 else 5.0)
          events.append((round(s * dt, 2), "replay finished, watching again"))
          if idle_genv:  # stand under the get-up policy while watching
            hand_over(robot, genv)
            gobs = gvenv.get_observations()
            mode = "idle"
      z = float(cmd.robot_anchor_pos_w[0, 2])
      qa = cmd.robot_anchor_quat_w[0].cpu().numpy()
      if z < 0.45 or Rot.from_quat(np.r_[qa[1:], qa[0]]).apply([0, 0, 1])[2] < 0.5:  # fell
        fell_count += 1
        routine = None  # a fall ends the replay; after getting up the robot watches the person again
        events.append((round(s * dt, 2), "fell"))
        robot.write_external_wrench_to_sim(torch.zeros(1, 1, 3, device=dev), torch.zeros(1, 1, 3, device=dev),
                                           body_ids=[i_torso])
        push_tail = None if push_vis is None else {"p": push_vis["p"], "d": push_vis["d"], "t": 0.0}
        push_state, push_vis = None, None
        if genv is None:  # old behaviour: teleport back to a standing frame
          p, rate = to50(dance, 60.0 if dance == 0 else 5.0), 0.0
          place_at(p)
          obs = venv.get_observations()
        else:  # hand the robot over to the get-up policy
          hand_over(robot, genv)
          gobs = gvenv.get_observations()
          mode, g_t, g_stable = "getup", 0.0, 0
    else:  # mode == "getup" or "idle" (both run the get-up policy)
      if mode == "idle" and push_times and s * dt >= push_times[0] and push_state is None:
        push_times.pop(0)
        push_state = {"t": 0.0, "side": 1.0 if push_count % 2 == 0 else -1.0}
        push_count += 1
        events.append((round(s * dt, 2), "push " + ("from the left" if push_state["side"] > 0 else "from the right")))
      push_vis = None
      if mode == "idle" and push_state is not None:
        push_vis = apply_push(grobot)
      tp0 = time.time()
      with torch.no_grad():
        gobs, _, _, _ = gvenv.step(gpolicy(gobs))
        torch.cuda.synchronize()
      prof["step"].append(time.time() - tp0)
      if mode == "idle":
        gz = float(grobot.data.root_link_pos_w[0, 2] - origin[2])
        up = float(-grobot.data.projected_gravity_b[0, 2])
        if gz < 0.45 or up < 0.5:  # knocked over while standing: it is already the get-up policy, just relabel
          fell_count += 1
          events.append((round(s * dt, 2), "fell"))
          push_tail = None if push_vis is None else {"p": push_vis["p"], "d": push_vis["d"], "t": 0.0}
          grobot.write_external_wrench_to_sim(torch.zeros(1, 1, 3, device=dev), torch.zeros(1, 1, 3, device=dev),
                                              body_ids=[i_torso])
          push_state, push_vis = None, None
          mode, g_t, g_stable = "getup", 0.0, 0
        info = {**info, "phase": "watching (standing)"}
        g_t = 0.0
    if mode == "getup":
      g_t += dt
      if push_tail is not None:  # finish the push arrow's retreat after the hand-over
        push_tail["t"] += dt
        if push_tail["t"] > 0.4:
          push_tail = None
      gz = float(grobot.data.root_link_pos_w[0, 2] - origin[2])
      up = float(-grobot.data.projected_gravity_b[0, 2])
      g_stable = g_stable + 1 if (gz > 0.70 and up > 0.966) else 0  # pelvis up, tilt < 15 deg
      if idle_genv and g_stable >= int(1.0 / dt):  # routine mode: stood up -> keep standing and watch again
        getup_times.append(g_t - 1.0)
        events.append((round(s * dt, 2), f"stood up in {g_t - 1.0:.1f} s"))
        mode = "idle"
      elif g_stable >= int(1.0 / dt) or g_t > 10.0:
        # back to dancing from a standing frame of the current dance, yaw re-centred onto the reference
        p, rate, commit, routine = to50(dance, 60.0 if dance == 0 else 5.0), 0.0, None, None
        pi = int(round(p))
        cmd.time_steps[:] = pi - 1
        cmd.cur_end[:] = cmd.clip_end[pi]
        if g_t > 10.0:  # get-up failed: fall back to the old teleport
          place_at(p)
          events.append((round(s * dt, 2), "get-up timeout"))
        else:
          dyaw = yaw_of(cmd.anchor_quat_w[0]) - yaw_of(grobot.data.body_link_quat_w[0, i_anchor])
          c0 = (grobot.data.root_link_pos_w[0, :2] - origin[:2]).cpu().numpy()
          T = np.array([[np.cos(dyaw), -np.sin(dyaw), 0], [np.sin(dyaw), np.cos(dyaw), 0], [0, 0, 1]])
          Tc = np.array([[1, 0, c0[0]], [0, 1, c0[1]], [0, 0, 1]]) @ T @ np.array([[1, 0, -c0[0]], [0, 1, -c0[1]], [0, 0, 1]])
          hand_over(grobot, env, dyaw)
          disp = disp @ np.linalg.inv(Tc)
          getup_times.append(g_t - 1.0)
          events.append((round(s * dt, 2), f"stood up in {g_t - 1.0:.1f} s"))
        obs = venv.get_observations()
        mode = "dance"
    if rec is not None and mode == "dance":  # per-tick timeline (bench)
      ia_l, ia_r = robot.body_names.index("left_ankle_roll_link"), robot.body_names.index("right_ankle_roll_link")
      yq = robot.data.root_link_quat_w[0:1]
      rel = quat_apply_inverse(yq, (robot.data.body_link_pos_w[0, ia_l] - robot.data.body_link_pos_w[0, ia_r])[None])[0]
      bl, br = cmd.cfg.body_names.index("left_ankle_roll_link"), cmd.cfg.body_names.index("right_ankle_roll_link")
      rq = cmd.body_quat_w[0, 0:1]
      rrel = quat_apply_inverse(rq, (cmd.body_pos_w[0, bl] - cmd.body_pos_w[0, br])[None])[0]
      rec.append([time.time() - t_feed0, last_pred[0], last_pred[1], p, float(rel[1]), float(rel[0]),
                  float(rrel[1]), float(rrel[0]), float(cmd.robot_anchor_pos_w[0, 1] - origin[1])])
    if s % a.render_every == 0:
      gl = mode in ("getup", "idle")  # the robot lives in the get-up env
      hdr = {**info, "dance_en": DANCE_EN[info["dance"]], "loop_ms": round(float(np.mean(loop_ms)) if loop_ms else 0, 1),
             "rt_factor": round(dt * 1000 / max(np.mean(loop_ms), 1e-3), 2) if loop_ms else 0, "fell_count": fell_count,
             "mode": mode, "push_count": push_count, "getups": len(getup_times),
             "events": [f"{t:.1f}s {msg}" for t, msg in events[-6:]], "seen": seen,
             "replaying": DANCE_EN[routine[0]] if routine is not None else "",
             "qpos": robot_qpos(grobot if gl else None)}
      if mode == "getup":
        hdr["phase"] = f"GETTING UP ({g_t:.1f} s)"
        if push_tail is not None:
          hdr["push_vis"] = {"stage": "release", "u": round(push_tail["t"] / 0.4, 3), "p": push_tail["p"],
                             "d": push_tail["d"]}
      elif mode == "idle":
        if push_vis is not None:
          hdr["push_vis"] = push_vis
      else:
        hdr["ref_qpos"] = ref_qpos()
        if push_vis is not None:
          hdr["push_vis"] = push_vis
      jpg = b""
      if a.jpeg:  # optional server-side rendering (slow under WSL: ~100 ms/frame)
        tr0 = time.time()
        img = env.render()
        prof["render"].append(time.time() - tr0)
        jpg = cv2.imencode(".jpg", img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()
      send(hdr, jpg)
    s += 1
    work = time.time() - tick
    loop_ms.append(work * 1000)
    if work < dt:
      time.sleep(dt - work)
    if a.bench and s % 50 == 0:
      print(f"[bench] t={s * dt:.1f}s loop {np.mean(loop_ms):.1f} ms (budget {dt * 1000:.0f} ms) "
            f"rt_factor {dt * 1000 / np.mean(loop_ms):.2f} | {mode} | {info} | falls {fell_count} | "
            + " ".join(f"{k} {1000 * np.mean(v):.1f}ms" for k, v in prof.items() if v), flush=True)
  if rec is not None:
    np.savez(a.rec, rec=np.array(rec, np.float32), clip_len=len(kp_all) / 30.0,
             columns=np.array(["t", "pred_dance", "pred_f30", "p", "robot_ankle_dy", "robot_ankle_dx",
                               "ref_ankle_dy", "ref_ankle_dx", "robot_anchor_y"]),
             starts=np.array([starts[dance_clip[0]], starts[dance_clip[1]]]))
    print(f"[server] timeline -> {a.rec}")
  print(f"[server] done: steps {s}, mean loop {np.mean(loop_ms):.1f} ms, falls {fell_count}, pushes {push_count}, "
        f"get-ups {len(getup_times)} (times {[round(x, 1) for x in getup_times]})")
  print(f"[server] events: {events}")


if __name__ == "__main__":
  main()
