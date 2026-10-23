#!/usr/bin/env bash
# quick check that the exported scene XML loads (3.5 unitree env and 3.16 gmr env)
source ~/miniforge3/etc/profile.d/conda.sh
cd ~/dance_win/sim2sim
for e in unitree_rl_mjlab gmr; do
  conda activate $e
  python -c "import mujoco, native_dance as nd; m = nd.load_xml_model('models/dance.xml', str(nd.G1_ASSETS)); print(mujoco.__version__, m.nq, m.nv, m.nu, m.ngeom, m.nsensor, m.opt.timestep)" 2>&1 | tail -n 3
done
