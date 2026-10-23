"""Windows side of the live demo: webcam -> YOLOv8-pose (COCO-17) -> TCP to the WSL server; receive the robot
pose and render G1 natively (NVIDIA GPU) next to the camera image.

Usage:  <conda>\\envs\\dancecam\\python.exe cam_client.py [--host localhost] [--port 5577] [--record out.mp4]
        [--duration 0 (=until ESC)] [--cam 0]
Keys: ESC quits, M toggles mirrored camera preview (display only; the robot always copies your own left/right).
Stand ~2.5-3 m from the laptop so your whole body is in view.
"""
import argparse
import json
import os
import socket
import struct
import threading
import time
from pathlib import Path

import cv2
import mujoco
import numpy as np
from ultralytics import YOLO

from vis import draw_push, push_label

EDGES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]


class State:
  def __init__(self):
    self.lock = threading.Lock()
    self.frame, self.kp, self.hdr, self.cam_fps = None, None, {}, 0.0
    self.alive = True


def recv_exact(sock, n):
  b = b""
  while len(b) < n:
    chunk = sock.recv(n - len(b))
    if not chunk:
      raise ConnectionError("server closed")
    b += chunk
  return b


def camera_loop(st, sock, cam, model, video="", loops=1):
  if video:  # offline test: play a video file at its own frame rate, as if it were the camera
    cap = cv2.VideoCapture(video)
    vfps = cap.get(cv2.CAP_PROP_FPS) or 30
    ok, f0 = cap.read()  # warm the pose model up BEFORE the clock starts (first call takes ~1 s)
    if not ok:
      print(f"cannot open video {video}")
      st.alive = False
      return
    model.predict(f0, imgsz=480, conf=0.4, verbose=False)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    t_start, n = time.time(), 0
  else:
    cap = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
  times = []
  while st.alive:
    if video:
      # behave like a real camera: the frame shown is the one at the current wall-clock time; if processing is
      # slower than the video, frames are dropped (never played faster); timestamp = that frame's capture time
      target = int((time.time() - t_start) * vfps)
      while n < target:
        if not cap.grab():
          break
        n += 1
      while time.time() - t_start < n / vfps:
        time.sleep(0.002)
      ok, f = cap.read()
      n += 1
      t = t_start + (n - 1) / vfps
    else:
      ok, f = cap.read()
      t = time.time()
    if not ok:
      if video and loops > 1:  # play the clip again (the server just sees a person dancing on)
        loops -= 1
        cap.release()  # re-open instead of seeking (seeking back is unreliable for some files)
        cap = cv2.VideoCapture(video)
        t_start, n = time.time(), 0
        print(f"[client] video loop restart, {loops} left, t={time.time():.2f}", flush=True)
        continue
      if video:
        st.video_done = True
        break
      continue
    r = model.predict(f, imgsz=480, conf=0.4, verbose=False)[0]
    kp = None
    if r.keypoints is not None and len(r.keypoints) > 0 and r.boxes is not None and len(r.boxes) > 0:
      b = r.boxes.xyxy.cpu().numpy()
      i = int(np.argmax((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])))  # largest person
      xy = r.keypoints.xy[i].cpu().numpy()
      cf = r.keypoints.conf[i].cpu().numpy() if r.keypoints.conf is not None else np.ones(17)
      kp = np.concatenate([xy, cf[:, None]], 1)
    msg = {"t": t, "wh": [f.shape[1], f.shape[0]], "kp": None if kp is None else kp.round(2).tolist()}
    if video and n % 60 == 0:
      print(f"[client] frame {n} t={t:.2f} now={time.time():.2f} person={kp is not None}", flush=True)
    try:
      sock.sendall((json.dumps(msg) + "\n").encode())
    except OSError:
      st.alive = False
    times.append(t)
    times = times[-30:]
    with st.lock:
      st.frame, st.kp = f, kp
      st.cam_fps = (len(times) - 1) / max(times[-1] - times[0], 1e-3) if len(times) > 1 else 0
  cap.release()


def recv_loop(st, sock):
  try:
    while st.alive:
      h = json.loads(recv_exact(sock, struct.unpack(">I", recv_exact(sock, 4))[0]))
      n = struct.unpack(">I", recv_exact(sock, 4))[0]
      if n:
        recv_exact(sock, n)
      with st.lock:
        st.hdr = h
  except (ConnectionError, OSError):
    st.alive = False


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--host", default="localhost")
  ap.add_argument("--port", type=int, default=5577)
  ap.add_argument("--cam", type=int, default=0)
  ap.add_argument("--record", default="")
  ap.add_argument("--duration", type=float, default=0)
  ap.add_argument("--no_window", action="store_true")
  ap.add_argument("--video", default="", help="use a video file instead of the camera (played in real time)")
  ap.add_argument("--loops", type=int, default=1, help="play the video this many times")
  ap.add_argument("--push_at", default="", help="comma-separated times (s after the video starts) to push the robot")
  a = ap.parse_args()

  here = Path(__file__).resolve().parent
  model = YOLO(str(here / "yolov8n-pose.pt"))
  os.chdir(here / "g1")  # MuJoCo cannot open non-ASCII absolute paths on Windows
  m = mujoco.MjModel.from_xml_path("scene_live.xml")
  d, dref = mujoco.MjData(m), mujoco.MjData(m)
  H = 540
  ren = mujoco.Renderer(m, H, H)
  cam = mujoco.MjvCamera()
  cam.type = mujoco.mjtCamera.mjCAMERA_FREE
  cam.distance, cam.elevation, cam.azimuth = 3.2, -8.0, 180.0  # looking at the robot's front
  ghost = mujoco.MjvOption()

  sock = socket.create_connection((a.host, a.port), timeout=10)
  sock.settimeout(None)
  sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
  st = State()
  st.video_done = False
  threading.Thread(target=camera_loop, args=(st, sock, a.cam, model, a.video, a.loops), daemon=True).start()
  sock.sendall(b'{"cmd": "reset"}\n')  # fresh session on the (possibly long-running) server

  def pusher(times):  # same path as the web page's push button
    t0 = time.time()
    for tp in times:
      while time.time() - t0 < tp and st.alive:
        time.sleep(0.01)
      try:
        sock.sendall(b'{"cmd": "push"}\n')
      except OSError:
        return
  if a.push_at:
    threading.Thread(target=pusher, args=(sorted(float(x) for x in a.push_at.split(",")),), daemon=True).start()
  threading.Thread(target=recv_loop, args=(st, sock), daemon=True).start()
  mirror, t0, rec, rec_t = True, time.time(), [], []
  print("connected; ESC to quit")
  while st.alive:
    with st.lock:
      f, kp, h, cfps = (None if st.frame is None else st.frame.copy()), st.kp, dict(st.hdr), st.cam_fps
    if f is None:
      time.sleep(0.01)
      continue
    # --- camera panel ---
    if kp is not None:
      for i, j in EDGES:
        if kp[i, 2] > 0.3 and kp[j, 2] > 0.3:
          cv2.line(f, tuple(kp[i, :2].astype(int)), tuple(kp[j, :2].astype(int)), (120, 255, 0), 3)
    if mirror:
      f = cv2.flip(f, 1)
    f = cv2.resize(f, (int(f.shape[1] * H / f.shape[0]), H))
    # --- robot panel ---
    if "qpos" in h:
      d.qpos[:] = h["qpos"]
      mujoco.mj_kinematics(m, d)
      cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.75]
      w, x, y, z = d.qpos[3:7]
      yaw = np.degrees(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
      az = yaw + 180.0  # camera in front of the robot, looking back at it
      cam.azimuth = az if not hasattr(st, "az") else st.az + ((az - st.az + 180) % 360 - 180) * 0.1  # smooth
      st.az = cam.azimuth
      ren.update_scene(d, camera=cam)
      if "ref_qpos" in h:  # translucent reference ("what the robot is trying to play"), overlaid on the robot
        dref.qpos[:] = h["ref_qpos"]
        dref.qpos[:2] = d.qpos[:2]
        mujoco.mj_kinematics(m, dref)
        n0 = ren.scene.ngeom
        mujoco.mjv_addGeoms(m, dref, ghost, mujoco.MjvPerturb(), mujoco.mjtCatBit.mjCAT_DYNAMIC, ren.scene)
        for k in range(n0, ren.scene.ngeom):
          ren.scene.geoms[k].rgba[:] = [0.3, 1.0, 0.5, 0.25]
      if "push_vis" in h:  # arrow + contact point of the push
        draw_push(ren.scene, h["push_vis"])
      rimg = ren.render()[..., ::-1].copy()
      if "push_vis" in h:
        cv2.putText(rimg, push_label(h["push_vis"]), (16, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (60, 60, 255), 3)
      elif h.get("mode") == "getup":
        cv2.putText(rimg, "GETTING UP", (16, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 160, 255), 3)
    else:
      rimg = np.zeros((H, H, 3), np.uint8)
      cv2.putText(rimg, "waiting for server...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    frame = np.concatenate([f, rimg], 1)
    bar = np.zeros((70, frame.shape[1], 3), np.uint8)
    line1 = f"{h.get('dance_en', '-')} ({h.get('dance_p', 0):.0%})   robot plays: {h.get('phase', '-')}"
    line2 = (f"camera {cfps:4.1f} fps | sim real-time x{h.get('rt_factor', 0):.2f} | falls {h.get('fell_count', 0)}"
             f" | {'person detected' if kp is not None else 'NO PERSON - step back so your whole body is visible'}")
    cv2.putText(bar, line1, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(bar, line2, (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 220, 255), 1)
    frame = np.concatenate([bar, frame], 0)
    if a.record:  # frames are buffered and written at the measured display rate (so the video plays in real time)
      rec.append(frame)
      rec_t.append(time.time())
    if not a.no_window:
      cv2.imshow("G1 follows you  (ESC quit, M mirror)", frame)
      k = cv2.waitKey(1) & 0xFF
      if k == 27:
        break
      if k in (ord("m"), ord("M")):
        mirror = not mirror
    else:
      time.sleep(0.03)
    if a.duration and time.time() - t0 > a.duration:
      break
    if st.video_done:
      if not hasattr(st, "t_done"):
        st.t_done = time.time()
      elif time.time() - st.t_done > 1.0:  # keep 1 s after the video ends
        break
  st.alive = False
  if a.record and len(rec) > 1:
    fps = (len(rec) - 1) / (rec_t[-1] - rec_t[0])
    writer = cv2.VideoWriter(a.record, cv2.VideoWriter_fourcc(*"mp4v"), fps, (rec[0].shape[1], rec[0].shape[0]))
    for fr in rec:
      writer.write(fr)
    writer.release()
    print(f"recorded {len(rec)} frames at {fps:.1f} fps -> {a.record}")
  print("final status:", json.dumps({k: v for k, v in st.hdr.items() if k not in ("qpos", "ref_qpos")}))
  sock.close()
  cv2.destroyAllWindows()


if __name__ == "__main__":
  main()
