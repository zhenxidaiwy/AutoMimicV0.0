#!/usr/bin/env bash
# Video -> world-frame SMPL-X env: GVHMR.
# Upstream pins torch 2.3+cu121, which has no sm_120 (RTX 50) kernels, so we use torch 2.7.1+cu128
# and build pytorch3d from source for sm_120 with a conda-installed CUDA 12.8 toolkit.
set -e
source ~/miniforge3/etc/profile.d/conda.sh
conda env list | grep -q "^gvhmr " || conda create -y -q -n gvhmr python=3.10
conda activate gvhmr
cd ~/projects/GVHMR

pip install -q torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
grep -vE "^(--extra-index-url|torch==|torchvision==|pytorch3d)" requirements.txt > /tmp/gvhmr_req.txt
pip install -q cython "numpy==1.23.5" setuptools wheel
pip install -q --no-build-isolation -r /tmp/gvhmr_req.txt
pip install -q -e .

# CUDA 12.8 toolkit inside the env (nvcc + dev headers), only for compiling pytorch3d.
conda install -y -q -c nvidia/label/cuda-12.8.1 cuda-nvcc cuda-cudart-dev cuda-cccl \
  libcublas-dev libcusparse-dev libcusolver-dev libcurand-dev cuda-profiler-api
export CUDA_HOME=$CONDA_PREFIX FORCE_CUDA=1 TORCH_CUDA_ARCH_LIST="12.0" MAX_JOBS=6
python -c "import pytorch3d" 2>/dev/null || \
  pip install --no-build-isolation "git+https://github.com/facebookresearch/pytorch3d.git@stable"

mkdir -p inputs/checkpoints/{body_models/smplx,body_models/smpl,gvhmr,hmr2,vitpose,yolo} outputs
python - <<'EOF'
import torch, pytorch3d, pytorch3d.ops, pytorch3d.renderer
x = torch.randn(1, 64, 3, device="cuda")
d = pytorch3d.ops.knn_points(x, x, K=2).dists
print("torch", torch.__version__, "| pytorch3d", pytorch3d.__version__, "| knn on cuda ok", d.shape)
EOF
echo DONE_GVHMR
