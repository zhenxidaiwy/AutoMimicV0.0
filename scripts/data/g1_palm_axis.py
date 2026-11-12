"""Which side of the G1 rubber hand is the palm? Mesh vertices of left/right_rubber_hand in the wrist_yaw_link frame:
extent along each axis + where the finger tips curl (the hand collision capsule bends to -y on the left hand and +y
on the right one). Usage (gmr env): python g1_palm_axis.py"""
import mujoco
import numpy as np

m = mujoco.MjModel.from_xml_path("/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml")
d = mujoco.MjData(m)
mujoco.mj_kinematics(m, d)
for side in ("left", "right"):
  wb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{side}_wrist_yaw_link")
  hb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{side}_rubber_hand")
  g = [i for i in range(m.ngeom) if m.geom_bodyid[i] == hb and m.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH][0]
  mid = m.geom_dataid[g]
  v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
  # mesh -> world -> wrist_yaw frame
  Rg, pg = d.geom_xmat[g].reshape(3, 3), d.geom_xpos[g]
  Rw, pw = d.xmat[wb].reshape(3, 3), d.xpos[wb]
  vw = (v @ Rg.T + pg - pw) @ Rw
  far = vw[vw[:, 0] > np.percentile(vw[:, 0], 90)]  # finger tips (far end along x)
  print(f"{side}: x [{vw[:,0].min():.3f},{vw[:,0].max():.3f}] y [{vw[:,1].min():.3f},{vw[:,1].max():.3f}] "
        f"z [{vw[:,2].min():.3f},{vw[:,2].max():.3f}]; finger tips mean y {far[:,1].mean():+.3f} z {far[:,2].mean():+.3f}")
