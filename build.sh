#!/usr/bin/env bash
set -o errexit

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel
pip install numpy==1.24.3
pip install git+https://github.com/CPJKU/beat_this.git
pip install einops rotary-embedding-torch
pip install flask==2.3.3 flask-cors==4.0.0 gunicorn==21.2.0 librosa==0.10.1
