#!/usr/bin/env bash
# Fix stage of the get-up sim2sim: re-run every simulation phase (equivalence test + mjlab reference, native closed
# loops incl. XML / MuJoCo 3.16 variants, contact diagnostic, saturation / push diagnostic). The report is run
# separately (fix_getup_report.sh). Log: out/fix_getup_runs.log
source ~/miniforge3/etc/profile.d/conda.sh
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
mkdir -p out
LOG=out/fix_getup_runs.log
FILTER="^Module |Warp [0-9]|CUDA Toolkit|Devices:|\"cuda:0\"|\"cpu\"|Kernel cache|^\s*$"
{
  conda activate unitree_rl_mjlab
  echo "=== mjlab phase $(date)"
  python native_getup.py mjlab --n 64 --steps 500 --seed 0 || exit 1
  echo "=== native (mjb) $(date)"
  python native_getup.py native || exit 1
  echo "=== native (xml, 3.5) $(date)"
  python native_getup.py native --model models/getup.xml --tag native_xml35 || exit 1
  conda activate gmr
  echo "=== native (xml, gmr env) $(date)"
  python -c "import mujoco, torch; print('gmr env: mujoco', mujoco.__version__, 'torch', torch.__version__)"
  python native_getup.py native --model models/getup.xml --tag native_v316 || exit 1
  conda activate unitree_rl_mjlab
  echo "=== diag_getup (contacts) $(date)"
  python diag_getup.py > out/getup_diag.log 2>&1 || { tail -n 20 out/getup_diag.log; exit 1; }
  echo "=== diag_getup_sat (saturation / push) $(date)"
  python diag_getup_sat.py || exit 1
  echo "=== done $(date)"
} 2>&1 | grep -v -E "$FILTER" > $LOG
grep -E "^===|^\[mjlab\] (step|wrote)|^\[native|^\[sat\]|gmr env|Error|Traceback|line [0-9]+" $LOG | cut -c 1-400
