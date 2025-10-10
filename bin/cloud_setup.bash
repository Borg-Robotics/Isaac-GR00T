sudo apt update
sudo apt install -qy --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    ffmpeg \
    git \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libvulkan-dev \
    libxext6 \
    libxrender-dev \
    sudo \
    tensorrt

curl -L https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python pin /opt/conda/bin/python

uv venv --name gr00t
uv pip install setuptools wheel wheel-stub
uv pip install psutil torch==2.5.1
uv sync --extra base --extra dev --no-build-isolation --no-install-project
uv pip install -e . --no-deps

source .venv/bin/activate
export PYTHONPATH=/root/Isaac-GR00T:$PYTHONPATH