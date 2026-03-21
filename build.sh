#!/usr/bin/env bash
set -o errexit

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install core build tools
pip install --upgrade pip wheel
pip install Cython numpy==1.20.3

# Install setuptools and lock it
pip install setuptools==70.0.0

# Install madmom using --no-build-isolation
pip install madmom==0.16.1 --no-build-isolation

# Install BeatNet from the correct repository
pip install git+https://github.com/mjhydri/BeatNet.git --no-deps

# Install BeatThis
pip install git+https://github.com/CPJKU/beat_this.git --no-deps

# Install missing BeatThis dependencies
pip install einops rotary-embedding-torch

# Apply Python 3.9 compatibility fix to BeatThis
python fix_beatthis.py

# Install matplotlib version compatible with numpy 1.20.3
pip install matplotlib==3.5.3

# Install remaining requirements
pip install -r requirements.txt

# Reinstall setuptools to ensure it's present
pip install --force-reinstall --no-deps setuptools==70.0.0
