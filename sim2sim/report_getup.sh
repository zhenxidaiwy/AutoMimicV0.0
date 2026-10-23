#!/usr/bin/env bash
# Re-run only the report phase of the get-up sim2sim (metrics, results_getup.json/.md, video) and dump 2 video frames
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
python native_getup.py report $1 > out/getup_report.log 2>&1 || tail -n 30 out/getup_report.log
python - <<'EOF'
import imageio.v2 as imageio
r = imageio.get_reader("/home/user/dance_win/videos/sim2sim/getup_side_by_side.mp4")
n = r.count_frames()
for i in (60, 150 + 120):
  imageio.imwrite(f"out/getup_video_frame{i}.png", r.get_data(min(i, n - 1)))
print("frames", n)
EOF
