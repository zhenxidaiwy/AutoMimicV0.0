#!/usr/bin/env bash
# Backflip sim2sim driver. Usage: bash native_flip.sh <step> [POLICY]   (POLICY default backflip_r14_fid2)
#   export          : models/flip.mjb/.xml with knee limit 120 (export_flip_model.sh)
#   mjlab P         : equivalence + closed loop mjlab vs native 3.5 + video   (unitree_rl_mjlab env, GPU, num_envs 1)
#   delay P         : mjlab DelayedActuator (fixed lag 4 and 8 physics steps) vs native latency buffer
#   native P        : native cross checks: MuJoCo 3.5 xml (unitree_rl_mjlab env) and MuJoCo 3.16 xml (gmr env)
#   scen P [RUNS]   : native perturbation scenarios with flip.mjb (3.5) and the xml in MuJoCo 3.16
#   report          : results_flip.json / results_flip.md
#   all P           : mjlab, delay, native, scen, report
source ~/miniforge3/etc/profile.d/conda.sh
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
mkdir -p logs ~/dance_win/videos/sim2sim
P=${2:-backflip_r14_fid2}
filt() { grep -vE "Warning|warn\(|^\s*$" ; }
show() { grep -E "^\[|Error|Traceback|line [0-9]+," ; }
run_mjlab() { conda activate unitree_rl_mjlab; python native_flip.py --mode mjlab --policy "$P" 2>&1 | filt | tee logs/flip_mjlab_$P.log | show ; }
run_delay() { conda activate unitree_rl_mjlab; for L in 4 8; do python native_flip.py --mode mjlab_delay --lag $L --policy "$P" 2>&1 | filt | tee logs/flip_delay${L}_$P.log | show; done ; }
run_native() {
  conda activate unitree_rl_mjlab; python native_flip.py --mode native --policy "$P" --xml models/flip.xml --tag mj350xml 2>&1 | filt | tee logs/flip_native350_$P.log | show
  conda activate gmr; python native_flip.py --mode native --policy "$P" --xml models/flip.xml --tag mj316 2>&1 | filt | tee logs/flip_native316_$P.log | show
}
run_scen() {
  R=${3:-100}
  conda activate unitree_rl_mjlab; python native_flip.py --mode scenarios --policy "$P" --runs $R --tag mj350 2>&1 | filt | tee logs/flip_scen350_$P.log | show
  conda activate gmr; python native_flip.py --mode scenarios --policy "$P" --runs $R --xml models/flip.xml --tag mj316 2>&1 | filt | tee logs/flip_scen316_$P.log | show
}
run_scen_wc() {  # same suite with the mujoco_warp clamped-actuator damping emulated (MuJoCo 3.5 .mjb)
  R=${3:-100}
  conda activate unitree_rl_mjlab; python native_flip.py --mode scenarios --policy "$P" --runs $R --warp_clamp --tag mj350wc 2>&1 | filt | tee logs/flip_scen350wc_$P.log | show
}
run_report() { conda activate unitree_rl_mjlab; python native_flip.py --mode report > logs/flip_report.log 2>&1; tail -n 3 logs/flip_report.log; }
case "$1" in
  export) bash export_flip_model.sh ;;
  mjlab) run_mjlab ;;
  delay) run_delay ;;
  native) run_native ;;
  scen) run_scen "$@" ;;
  scenwc) run_scen_wc "$@" ;;
  report) run_report ;;
  all) run_mjlab; run_delay; run_native; run_scen "$@"; run_scen_wc "$@"; run_report ;;
  smoke) conda activate unitree_rl_mjlab; python native_flip.py --mode scenarios --policy "$P" --runs 2 --scenarios nominal,lat20,push_pre,kp085 --tag smoke 2>&1 | filt | show ;;
  *) echo "usage: bash native_flip.sh [export | mjlab P | delay P | native P | scen P [RUNS] | report | all P]" ;;
esac
