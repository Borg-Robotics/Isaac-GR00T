FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/var/cache/apt <<EOT
apt-get update
apt-get install -qqy --no-install-recommends \
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
EOT

RUN --mount=type=cache,target=/var/cache/apt <<EOT
apt-get update
apt-get install -qqy --no-install-recommends \
    unzip
EOT

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .

ENV UV_PROJECT_ENVIRONMENT=/opt/conda/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system setuptools wheel wheel-stub && \
    uv sync --extra base --extra dev --no-build-isolation --no-install-project

COPY . .

RUN uv pip install -e . --system --no-deps

ENV PATH="/opt/conda/bin:${PATH}"
WORKDIR /workspace