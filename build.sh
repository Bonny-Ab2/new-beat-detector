#!/usr/bin/env bash
set -o errexit

python -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel

# Install numpy first
pip install numpy==1.20.3

# Install BeatThis (this will also install PyTorch)
pip install git+https://github.com/CPJKU/beat_this.git

# Install BeatThis dependencies
pip install einops rotary-embedding-torch

# Install Flask and server dependencies
pip install flask==2.3.3 flask-cors==4.0.0 gunicorn==21.2.0 librosa==0.10.1

# Force reinstall setuptools
pip install --force-reinstall --no-deps setuptools==70.0.0
