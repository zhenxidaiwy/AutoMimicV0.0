"""Local web demo of the follow-dance pipeline: http://localhost:8000
Pick a test video or the laptop camera; the person is pose-tracked (YOLOv8-pose, here on Windows), the WSL
simulation server recognises the dance (no prior: nothing tells it which dance or who is dancing), the dancer policy
follows, and a "push" button knocks the robot over so the learned get-up policy takes over and it dances on.

Runs with the dancecam env:  <conda>\\envs\\dancecam\\python.exe web_app.py [--port 8000]
(start_web.ps1 does this and opens the browser). It (re)starts the WSL simulation server itself.
"""
import argparse
import json
import os
import socket
import struct
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import mujoco
import numpy as np
from ultralytics import YOLO

from vis import draw_push, push_label

HERE = Path(__file__).resolve().parent
WSL = ["wsl.exe", "-d", "Ubuntu-22.04", "--"]
TESTS = r"\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance\live_tests"
LOG = r"\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance_logs\live_server.log"
EDGES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def placeholder(text, w=640, h=540):
  img = np.zeros((h, w, 3), np.uint8)
  cv2.putText(img, text, (20, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
  return cv2.imencode(".jpg", img)[1].tobytes()


def recv_exact(sock, n):
  b = b""
  while len(b) < n:
    chunk = sock.recv(n - len(b))
    if not chunk:
      raise ConnectionError("server closed")
    b += chunk
  return b


class App:
  def __init__(self, a):
    self.a = a
    self.lock = threading.Lock()
    self.model = YOLO(str(HERE / "yolov8n-pose.pt"))
    self.human_jpg = placeholder("choose a video or the camera, then Start")
    self.robot_jpg = placeholder("simulation server starting ...", 540, 540)
    self.hdr, self.sock, self.session = {}, None, 0
    self.status = {"server": "starting", "source": None, "cam_fps": 0.0, "video_done": False, "error": ""}
    self.mirror = True
    threading.Thread(target=self.start_server, daemon=True).start()

  # ---------------------------------------------------------------- WSL simulation server
  def start_server(self):
    subprocess.call(WSL + ["bash", "/home/user/dance_win/live/stop_server.sh"], creationflags=NO_WINDOW,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
      os.remove(LOG)
    except OSError:
      pass
    subprocess.Popen(WSL + ["bash", "/home/user/dance_win/live/server_logged.sh"], creationflags=NO_WINDOW,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 240:
      time.sleep(1)
      try:
        if "waiting for the camera client" in Path(LOG).read_text(errors="ignore"):
          self.status["server"] = "ready"
          self.robot_jpg = placeholder("server ready - press Start", 540, 540)
          return
      except OSError:
        pass
    self.status["server"] = "failed (see dance_logs/live_server.log)"

  def stop_server(self):
    subprocess.call(WSL + ["bash", "/home/user/dance_win/live/stop_server.sh"], creationflags=NO_WINDOW,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  # ---------------------------------------------------------------- sessions
  def sources(self):
    try:
      vids = sorted(p.name for p in Path(TESTS).glob("*.mp4"))
    except OSError:
      vids = []
    unseen = [v for v in vids if v.startswith("unseen")]
    return {"unseen": unseen, "other": [v for v in vids if v not in unseen]}

  def start(self, source, loop):
    if self.status["server"] != "ready":
      return False, "simulation server not ready yet"
    self.stop()
    try:
      sock = socket.create_connection(("localhost", self.a.sim_port), timeout=10)
    except OSError as e:
      return False, f"cannot connect to the simulation server: {e}"
    sock.settimeout(None)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    with self.lock:
      self.session += 1
      sid, self.sock = self.session, sock
      self.status.update(source=source, video_done=False, error="", cam_fps=0.0)
    self.command("reset")
    threading.Thread(target=self.source_loop, args=(sid, sock, source, loop), daemon=True).start()
    threading.Thread(target=self.recv_loop, args=(sid, sock), daemon=True).start()
    return True, "started"

  def stop(self):
    with self.lock:
      self.session += 1
      s, self.sock = self.sock, None
      self.status["source"] = None
    if s is not None:
      try:
        s.close()
      except OSError:
        pass

  def control_session(self):
    """Connect without an input source (robot control only, e.g. the dance buttons before Start)."""
    if self.status["server"] != "ready":
      return False
    try:
      sock = socket.create_connection(("localhost", self.a.sim_port), timeout=10)
    except OSError:
      return False
    sock.settimeout(None)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    with self.lock:
      self.session += 1
      sid, self.sock = self.session, sock
      self.status.update(source="control only", video_done=False, error="")
    threading.Thread(target=self.recv_loop, args=(sid, sock), daemon=True).start()
    return True

  def command(self, cmd):
    with self.lock:
      s = self.sock
    if s is None and cmd.startswith("dance") and self.control_session():
      with self.lock:
        s = self.sock
    if s is None:
      return False
    try:
      s.sendall((json.dumps({"cmd": cmd}) + "\n").encode())
      return True
    except OSError:
      return False

  def alive(self, sid):
    return self.session == sid

  def source_loop(self, sid, sock, source, loop):
    is_cam = source == "camera"
    if is_cam:
      cap = cv2.VideoCapture(self.a.cam, cv2.CAP_DSHOW)
      cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
      cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    else:
      cap = cv2.VideoCapture(str(Path(TESTS) / source))
    if not cap.isOpened():
      self.status["error"] = f"cannot open {source}"
      return
    vfps = cap.get(cv2.CAP_PROP_FPS) or 30
    ok, f0 = cap.read()
    if ok:
      self.model.predict(f0, imgsz=480, conf=0.4, verbose=False)  # warm-up before the clock starts
    if not is_cam:
      cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    t_start, n, times = time.time(), 0, []
    while self.alive(sid):
      if is_cam:
        ok, f = cap.read()
        t = time.time()
      else:  # behave like a camera: show the frame due now, drop late frames, never play faster
        target = int((time.time() - t_start) * vfps)
        while n < target and cap.grab():
          n += 1
        while time.time() - t_start < n / vfps:
          time.sleep(0.002)
        ok, f = cap.read()
        n += 1
        t = t_start + (n - 1) / vfps
        if not ok and loop:  # re-open instead of seeking back (seeking was unreliable: the 2nd pass sent nothing)
          cap.release()
          cap = cv2.VideoCapture(str(Path(TESTS) / source))
          t_start, n = time.time(), 0
          continue
      if not ok:
        if is_cam:
          continue
        self.status["video_done"] = True
        break
      r = self.model.predict(f, imgsz=480, conf=0.4, verbose=False)[0]
      kp = None
      if r.keypoints is not None and len(r.keypoints) > 0 and r.boxes is not None and len(r.boxes) > 0:
        b = r.boxes.xyxy.cpu().numpy()
        i = int(np.argmax((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])))  # largest person
        xy = r.keypoints.xy[i].cpu().numpy()
        cf = r.keypoints.conf[i].cpu().numpy() if r.keypoints.conf is not None else np.ones(17)
        kp = np.concatenate([xy, cf[:, None]], 1)
      try:
        sock.sendall((json.dumps({"t": t, "wh": [f.shape[1], f.shape[0]],
                                  "kp": None if kp is None else kp.round(2).tolist()}) + "\n").encode())
      except OSError:
        break
      if kp is not None:
        for i, j in EDGES:
          if kp[i, 2] > 0.3 and kp[j, 2] > 0.3:
            cv2.line(f, tuple(kp[i, :2].astype(int)), tuple(kp[j, :2].astype(int)), (120, 255, 0), 3)
      if is_cam and self.mirror:
        f = cv2.flip(f, 1)
      f = cv2.resize(f, (int(f.shape[1] * 540 / f.shape[0]), 540))
      self.human_jpg = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()
      times = (times + [t])[-30:]
      self.status["cam_fps"] = round((len(times) - 1) / max(times[-1] - times[0], 1e-3), 1) if len(times) > 1 else 0
      self.status["person"] = kp is not None
    cap.release()

  def recv_loop(self, sid, sock):
    try:
      while self.alive(sid):
        h = json.loads(recv_exact(sock, struct.unpack(">I", recv_exact(sock, 4))[0]))
        nb = struct.unpack(">I", recv_exact(sock, 4))[0]
        if nb:
          recv_exact(sock, nb)
        self.hdr = h
    except (ConnectionError, OSError, ValueError):
      pass

  # ---------------------------------------------------------------- robot rendering (main thread: owns the GL context)
  def render_forever(self):
    os.chdir(HERE / "g1")  # MuJoCo cannot open non-ASCII absolute paths on Windows
    m = mujoco.MjModel.from_xml_path("scene_live.xml")
    d, dref = mujoco.MjData(m), mujoco.MjData(m)
    H = 540
    ren = mujoco.Renderer(m, H, H)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 3.2, -8.0, 180.0
    ghost, az = mujoco.MjvOption(), None
    while True:
      h = self.hdr
      if "qpos" not in h or self.status["source"] is None and not h:
        time.sleep(0.05)
        continue
      d.qpos[:] = h["qpos"]
      mujoco.mj_kinematics(m, d)
      cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.75]
      w, x, y, z = d.qpos[3:7]
      target = np.degrees(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))) + 180.0
      az = target if az is None else az + ((target - az + 180) % 360 - 180) * 0.1
      if h.get("mode") == "getup":  # side view while getting up, the front view hides a lying robot
        cam.azimuth, cam.elevation = az + 70.0, -15.0
      else:
        cam.azimuth, cam.elevation = az, -8.0
      ren.update_scene(d, camera=cam)
      if "ref_qpos" in h:  # translucent reference ("what the robot is trying to play")
        dref.qpos[:] = h["ref_qpos"]
        dref.qpos[:2] = d.qpos[:2]
        mujoco.mj_kinematics(m, dref)
        n0 = ren.scene.ngeom
        mujoco.mjv_addGeoms(m, dref, ghost, mujoco.MjvPerturb(), mujoco.mjtCatBit.mjCAT_DYNAMIC, ren.scene)
        for k in range(n0, ren.scene.ngeom):
          ren.scene.geoms[k].rgba[:] = [0.3, 1.0, 0.5, 0.25]
      if "push_vis" in h:  # arrow + contact point of the push
        draw_push(ren.scene, h["push_vis"])
      img = ren.render()[..., ::-1].copy()
      if "push_vis" in h:
        cv2.putText(img, push_label(h["push_vis"]), (16, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 60, 255), 3)
      elif h.get("mode") == "getup":
        cv2.putText(img, "GETTING UP", (16, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 160, 255), 3)
      self.robot_jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()
      time.sleep(1 / 30)

  def state(self):
    h = {k: v for k, v in self.hdr.items() if k not in ("qpos", "ref_qpos")}
    return {**self.status, "mirror": self.mirror, "sim": h}


def make_handler(app):
  page = (HERE / "web" / "index.html").read_bytes()

  class H(BaseHTTPRequestHandler):
    def log_message(self, *args):
      pass

    def _json(self, obj, code=200):
      b = json.dumps(obj).encode()
      self.send_response(code)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(b)))
      self.send_header("Cache-Control", "no-store")
      self.end_headers()
      self.wfile.write(b)

    def _mjpeg(self, attr):
      self.send_response(200)
      self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
      self.send_header("Cache-Control", "no-store")
      self.end_headers()
      last = None
      try:
        while True:
          jpg = getattr(app, attr)
          if jpg is not last:
            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode()
                             + b"\r\n\r\n" + jpg + b"\r\n")
            last = jpg
          time.sleep(1 / 30)
      except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
        return

    def do_GET(self):
      if self.path in ("/", "/index.html"):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)
      elif self.path == "/api/sources":
        self._json(app.sources())
      elif self.path == "/api/status":
        self._json(app.state())
      elif self.path.startswith("/snap/"):  # single JPEG (tests / screenshots)
        jpg = app.human_jpg if "human" in self.path else app.robot_jpg
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpg)))
        self.end_headers()
        self.wfile.write(jpg)
      elif self.path.startswith("/stream/human"):
        self._mjpeg("human_jpg")
      elif self.path.startswith("/stream/robot"):
        self._mjpeg("robot_jpg")
      else:
        self._json({"error": "not found"}, 404)

    def do_POST(self):
      n = int(self.headers.get("Content-Length") or 0)
      body = json.loads(self.rfile.read(n) or b"{}")
      if self.path == "/api/start":
        ok, msg = app.start(body.get("source", "camera"), bool(body.get("loop", False)))
        self._json({"ok": ok, "msg": msg})
      elif self.path == "/api/stop":
        app.stop()
        self._json({"ok": True})
      elif self.path in ("/api/push", "/api/reset"):
        self._json({"ok": app.command(self.path.rsplit("/", 1)[1])})
      elif self.path == "/api/dance":  # {"dance": 0 | 1}: dance this now, regardless of the person
        self._json({"ok": app.command(f"dance{int(body.get('dance', 0))}")})
      elif self.path == "/api/mirror":
        app.mirror = not app.mirror
        self._json({"ok": True, "mirror": app.mirror})
      else:
        self._json({"error": "not found"}, 404)

  return H


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--port", type=int, default=8000)
  ap.add_argument("--sim_port", type=int, default=5577)
  ap.add_argument("--cam", type=int, default=0)
  a = ap.parse_args()
  app = App(a)
  srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(app))
  srv.daemon_threads = True
  threading.Thread(target=srv.serve_forever, daemon=True).start()
  print(f"open http://localhost:{a.port}   (Ctrl+C to quit)", flush=True)
  try:
    app.render_forever()
  except KeyboardInterrupt:
    pass
  finally:
    app.stop()
    app.stop_server()


if __name__ == "__main__":
  main()
