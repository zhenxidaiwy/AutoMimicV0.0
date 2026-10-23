#!/usr/bin/env bash
# Deps GVHMR imports at demo time but does not list in requirements.txt.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gvhmr
pip install -q yacs
cd ~/projects/GVHMR
python -c "
import tools.demo.demo  # noqa: imports the whole demo dependency tree
print('demo imports ok')"
