"""Overlay helpers for the robot render (Windows clients): the push arrow and its contact point.
push_vis (from the server header): {"stage": "approach"|"contact"|"release", "u": 0..1 progress of the stage,
"p": contact point [x, y, z] (display frame), "d": unit push direction [dx, dy, 0]}.
"""
import mujoco
import numpy as np

ARROW_LEN = 0.45


def _add(scene):
  if scene.ngeom >= scene.maxgeom:
    return None
  g = scene.geoms[scene.ngeom]
  scene.ngeom += 1
  return g


def draw_push(scene, pv):
  p, d = np.asarray(pv["p"], float), np.asarray(pv["d"], float)
  stage, u = pv["stage"], float(pv["u"])
  if stage == "approach":  # the "hand" comes in from the side
    gap, rgba, width = 0.5 * (1.0 - u) + 0.02, [1.0, 0.65, 0.15, 0.95], 0.025
  elif stage == "contact":  # pushing: arrow touches the body, red, pulsing contact point
    gap, rgba, width = 0.0, [1.0, 0.15, 0.15, 1.0], 0.035
  else:  # release: retreats and fades
    gap, rgba, width = 0.5 * u + 0.02, [1.0, 0.4, 0.2, max(0.0, 1.0 - u)], 0.025
  tip = p - d * gap
  tail = tip - d * ARROW_LEN
  g = _add(scene)
  if g is not None:
    mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_ARROW, np.zeros(3), np.zeros(3), np.eye(3).flatten(),
                        np.array(rgba, np.float32))
    mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_ARROW, width, tail, tip)
  g = _add(scene)  # contact point marker
  if g is not None:
    r = 0.035 + (0.025 * (0.5 + 0.5 * np.sin(u * np.pi * 4)) if stage == "contact" else 0.0)
    col = [1.0, 0.1, 0.1, 0.95] if stage == "contact" else [1.0, 0.8, 0.2, 0.6 if stage == "approach" else 0.3]
    mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_SPHERE, np.array([r, r, r]), p, np.eye(3).flatten(),
                        np.array(col, np.float32))


def push_label(pv):
  return {"approach": "PUSH incoming", "contact": "PUSHING", "release": "PUSHED!"}.get(pv.get("stage"), "")
