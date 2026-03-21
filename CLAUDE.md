# CLAUDE.md

## Project Overview

NVIDIA Isaac GR00T N1.5 — open foundation model for humanoid robot reasoning and skills. Frozen Eagle 2.5 VLM backbone + learnable DiT action head, multi-embodiment. Python >=3.10,<3.12, Apache 2.0.

## Commands

```bash
# Format
make format              # isort + black

# Lint & test
make run-checks          # isort --check + black --check + ruff check + pytest
ruff check . --fix       # auto-fix lint issues

# Test
pytest -v --color=yes tests/
pytest -v tests/test_dataset.py  # single file

# Install
pip install -e .[base]
pip install --no-build-isolation flash-attn==2.7.1.post4
pip install -e .[dev]            # dev tools (black, isort, ruff, pytest)
```

## Code Style

- **Black**: line-length = 100
- **isort**: profile = black
- **ruff**: line-length = 115, target py310, `__init__.py` ignores F401
- `PYTHONPATH=./` in CI

## Key Entry Points

```bash
# Fine-tuning
python scripts/gr00t_finetune.py --dataset-path ./demo_data/robot_sim.PickNPlace --num-gpus 1

# Inference server/client
python scripts/inference_service.py --model-path nvidia/GR00T-N1.5-3B --server
python scripts/inference_service.py --client

# Evaluation
python scripts/eval_policy.py --plot --model_path nvidia/GR00T-N1.5-3B
python scripts/evaluate_replay.py

# Dataset inspection
python scripts/load_dataset.py --dataset-path ./demo_data/robot_sim.PickNPlace
```

## Architecture

- **`gr00t/model/`** — `Gr00tPolicy` (policy.py), `GR00T_N1_5` (gr00t_n1.py), Eagle backbone (backbone/), DiT action head (action_head/)
- **`gr00t/data/`** — `LeRobotSingleDataset`/`LeRobotMixtureDataset` (dataset.py), `EmbodimentTag` enum (embodiment_tags.py), transforms (transform/)
- **`gr00t/experiment/`** — `DualBrainTrainer` (trainer.py), `TrainRunner` (runner.py), `DATA_CONFIG_MAP` (data_config.py)
- **`gr00t/eval/`** — ZeroMQ service (service.py), FastAPI server (http_server.py), robot client (robot.py)

## Embodiment Tags

Defined in `gr00t/data/embodiment_tags.py` — each maps to a projector index in the action expert:

| Tag | Index |
|-----|-------|
| `GR1` | 24 |
| `OXE_DROID` | 17 |
| `AGIBOT_GENIE1` | 26 |
| `BORG` | 31 |
| `NEW_EMBODIMENT` | 31 |

## Data Configs

Built-in configs in `gr00t/experiment/data_config.py` (`DATA_CONFIG_MAP`):
`fourier_gr1_arms_waist`, `fourier_gr1_arms_only`, `fourier_gr1_full_upper_body`, `bimanual_panda_gripper`, `bimanual_panda_hand`, `single_panda_gripper`, `so100`, `so100_dualcam`, `unitree_g1`, `unitree_g1_full_body`, `oxe_droid`, `agibot_genie1`, `borg`

External configs via `module:ClassName` format.

## Docker

```bash
docker compose -f docker/compose.yaml up --build
docker exec -it borg-isaac-gr00t bash
```
