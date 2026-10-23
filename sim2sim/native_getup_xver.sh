#!/usr/bin/env bash
# Optional cross-version check for the get-up sim2sim (run after native_getup.sh):
#   native closed loop from the exported scene XML (+ mjlab's solver options from out/getup_opt.json) in
#   MuJoCo 3.5.0 (unitree_rl_mjlab env, tag native_xml35: isolates XML-export effects) and in MuJoCo 3.16 (gmr env,
#   tag native_v316), then re-runs the report (results_getup.json / .md / video) with all simulators.
source ~/miniforge3/etc/profile.d/conda.sh
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
LOG=out/getup_xver.log
{
  conda activate unitree_rl_mjlab
  [ -f out/getup_fingerprint.npz ] || python native_getup.py native || exit 1  # writes the mjb fingerprint
  python native_getup.py native --model models/getup.xml --tag native_xml35 || exit 1
  conda activate gmr
  python -c "import mujoco, torch; print('gmr env: mujoco', mujoco.__version__, 'torch', torch.__version__)"
  python native_getup.py native --model models/getup.xml --tag native_v316 || exit 1
  conda activate unitree_rl_mjlab
  python native_getup.py report || exit 1
} > $LOG 2>&1
grep -E "^\[native|gmr env|Error|Traceback|line [0-9]+|video:" $LOG | cut -c 1-600
