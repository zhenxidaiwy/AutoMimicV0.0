#!/usr/bin/env bash
# Dance sim2sim driver. Usage: bash native_dance.sh [mjlab CLIP | native CLIP | report | all]
#   mjlab CLIP  : mjlab vs native MuJoCo 3.5 for CLIP (sss | gxdsm)   (unitree_rl_mjlab env, GPU)
#   native CLIP : cross-version native closed loop with MuJoCo 3.16 (gmr env) + same-version xml check (3.5)
#   report      : merge results -> results_dance.json / results_dance.md
#   all         : everything above for both clips
source ~/miniforge3/etc/profile.d/conda.sh
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
mkdir -p logs ~/dance_win/videos/sim2sim
filt() { grep -vE "Warning|warn\(|^\s*$" ; }
run_mjlab() { conda activate unitree_rl_mjlab; python native_dance.py --mode mjlab --clip "$1" 2>&1 | filt | tee logs/dance_mjlab_$1.log | grep -E "^\[|Error|Traceback|line [0-9]+," ; }
run_native() {
  conda activate unitree_rl_mjlab; python native_dance.py --mode native --clip "$1" --tag mj350xml 2>&1 | filt | tee logs/dance_native350_$1.log | grep -E "^\[|Error|Traceback|line [0-9]+,"
  conda activate gmr; python native_dance.py --mode native --clip "$1" --tag mj316 2>&1 | filt | tee logs/dance_native316_$1.log | grep -E "^\[|Error|Traceback|line [0-9]+,"
}
run_report() { conda activate unitree_rl_mjlab; python native_dance.py --mode report > logs/dance_report.log 2>&1; tail -n 5 logs/dance_report.log; }
case "$1" in
  mjlab) run_mjlab "$2" ;;
  native) run_native "$2" ;;
  report) run_report ;;
  all) for c in sss gxdsm; do run_mjlab $c; run_native $c; done; run_report ;;
  *) echo "usage: bash native_dance.sh [mjlab CLIP | native CLIP | report | all]" ;;
esac
