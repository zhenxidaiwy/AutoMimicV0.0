"""Print the G1 (GMR mocap model) joint order of the csv columns (col = 7 + index) with ranges; optional name filter.
Usage (gmr env): python g1_joints.py [substring]"""
import sys

import mujoco

m = mujoco.MjModel.from_xml_path("/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml")
f = sys.argv[1] if len(sys.argv) > 1 else ""
for i in range(1, m.njnt):
  if f in m.joint(i).name:
    print(i - 1, m.joint(i).name, [round(float(x), 2) for x in m.jnt_range[i]])
