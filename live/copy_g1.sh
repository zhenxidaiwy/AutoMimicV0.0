#!/usr/bin/env bash
# Copy mjlab's G1 MJCF + meshes next to the live demo so the Windows client can render the robot natively.
SRC=~/miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab/asset_zoo/robots/unitree_g1/xmls
mkdir -p ~/dance_win/live/g1
cp -r $SRC/* ~/dance_win/live/g1/
cat > ~/dance_win/live/g1/scene_live.xml <<'EOF'
<mujoco model="g1_live">
  <include file="g1.xml"/>
  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3" specular="0 0 0"/>
    <global offwidth="960" offheight="960"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="3072"/>
    <texture type="2d" name="grid" builtin="checker" mark="edge" rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" markrgb="0.8 0.8 0.8" width="300" height="300"/>
    <material name="grid" texture="grid" texrepeat="5 5" reflectance="0.2"/>
  </asset>
  <worldbody>
    <light pos="0 0 3.5" dir="0 0 -1" directional="true"/>
    <geom name="floor" size="0 0 0.05" type="plane" material="grid"/>
  </worldbody>
</mujoco>
EOF
ls ~/dance_win/live/g1 | head; du -sh ~/dance_win/live/g1
