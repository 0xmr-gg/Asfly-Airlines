#!/usr/bin/env bash
set -e

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install \
  opencv-contrib-python \
  pandas \
  matplotlib \
  tqdm \
  pyyaml \
  requests \
  scipy \
  psutil \
  polars \
  nvidia-ml-py

mkdir -p .cache/matplotlib

echo "Done. Activate with: source activate_asfly_env.sh"
