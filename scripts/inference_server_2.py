import time
import json
import base64
import cv2
import numpy as np
import zmq
from dataclasses import dataclass
from typing import Literal
import tyro

from gr00t.data.embodiment_tags import EMBODIMENT_TAG_MAPPING
from gr00t.eval.robot import RobotInferenceClient
from gr00t.experiment.data_config import load_data_config
from gr00t.model.policy import Gr00tPolicy


# ==============================================================
# 🔧 Helper: Decode the incoming observation from base64 + JSON
# ==============================================================
def decode_observation(obs):
    """Decode base64-encoded video and expand joint states for GR00T inference."""
    decoded = {}

    # --- VIDEO ---
    if "video.cam_head" in obs:
        frame_b64 = obs["video.cam_head"]
        try:
            frame_bytes = base64.b64decode(frame_b64)
            frame_array = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            # ✅ Keep original resolution (GR00T will handle resizing internally)
            decoded["video.cam_head"] = np.expand_dims(frame, axis=0)
        except Exception as e:
            print(f"⚠️ Failed to decode video.cam_head: {e}")
            decoded["video.cam_head"] = np.zeros((1, 720, 1280, 3), dtype=np.uint8)
    else:
        decoded["video.cam_head"] = np.zeros((1, 720, 1280, 3), dtype=np.uint8)

    # --- STATE ---
    if "observation.state" in obs:
        state = np.array(obs["observation.state"], dtype=np.float32)
        if len(state) != 12:
            print(f"⚠️ Warning: Expected 12 joint state values, got {len(state)}")

        for i in range(6):
            decoded[f"state.l_arm_pivot_{i+1}_joint"] = state[i:i+1].reshape(1, 1)
        for i in range(6):
            decoded[f"state.r_arm_pivot_{i+1}_joint"] = state[6+i:6+i+1].reshape(1, 1)
    else:
        print("⚠️ Missing observation.state, filling zeros.")
        for i in range(6):
            decoded[f"state.l_arm_pivot_{i+1}_joint"] = np.zeros((1, 1), dtype=np.float32)
        for i in range(6):
            decoded[f"state.r_arm_pivot_{i+1}_joint"] = np.zeros((1, 1), dtype=np.float32)

    # --- LANGUAGE ---
    decoded["annotation.human.action.task_description"] = obs.get(
        "annotation.human.action.task_description", ["pick up the box"]
    )

    return decoded


# ==============================================================
# ⚙️ CLI Arguments
# ==============================================================
@dataclass
class ArgsConfig:
    model_path: str = "nvidia/GR00T-N1.5-3B"
    embodiment_tag: Literal[tuple(EMBODIMENT_TAG_MAPPING.keys())] = "gr1"
    data_config: str = "fourier_gr1_arms_waist"
    port: int = 5555
    host: str = "localhost"
    server: bool = False
    client: bool = False
    denoising_steps: int = 4
    api_token: str = None
    http_server: bool = False


# ==============================================================
# 🧩 Example client (ZMQ)
# ==============================================================
def _example_zmq_client_call(obs: dict, host: str, port: int, api_token: str):
    policy_client = RobotInferenceClient(host=host, port=port, api_token=api_token)
    print("Available modality config available:")
    modality_configs = policy_client.get_modality_config()
    print(modality_configs.keys())

    time_start = time.time()
    action = policy_client.get_action(obs)
    print(f"Total time taken to get action from server: {time.time() - time_start:.3f} seconds")
    return action


# ==============================================================
# 🚀 Main entrypoint
# ==============================================================
def main(args: ArgsConfig):
    # ==========================================================
    # 🧠 SERVER MODE
    # ==========================================================
    if args.server:
        data_config = load_data_config(args.data_config)
        modality_config = data_config.modality_config()
        modality_transform = data_config.transform()

        policy = Gr00tPolicy(
            model_path=args.model_path,
            modality_config=modality_config,
            modality_transform=modality_transform,
            embodiment_tag=args.embodiment_tag,
            denoising_steps=args.denoising_steps,
        )

        # Manual ZMQ server (for base64 + JSON decoding)
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(f"tcp://*:{args.port}")

        print(f"🧠 GR00T Inference Server listening on port {args.port}...")
        print(f"Model: {args.model_path}")
        print(f"Embodiment: {args.embodiment_tag}")
        print(f"Data Config: {args.data_config}")

        while True:
            try:
                message = socket.recv_string()
                request = json.loads(message)
                if "data" not in request:
                    socket.send_json({"error": "No 'data' field in request"})
                    continue

                # ✅ Decode observation (video + state)
                obs = decode_observation(request["data"])

                # ✅ Run policy inference
                actions = policy.get_action(obs)

                # ✅ Convert all outputs to JSON-safe format
                try:
                    formatted_actions = {
                        "action": {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in actions.items()}
                    }
                except Exception as e:
                    print(f"⚠️ Failed to format actions: {e}")
                    formatted_actions = {"action": {}}

                socket.send_json(formatted_actions)

            except Exception as e:
                print(f"⚠️ Error: {e}")
                socket.send_json({"error": str(e)})

    # ==========================================================
    # 🧪 CLIENT MODE
    # ==========================================================
    elif args.client:
        obs = {
            "video.cam_head": np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8).tolist(),
            "observation.state": np.random.rand(12).tolist(),
            "annotation.human.action.task_description": ["pick up the box from the roller table"],
        }

        action = _example_zmq_client_call(obs, args.host, args.port, args.api_token)
        if "action" in action:
            for key, value in action["action"].items():
                print(f"Action: {key}: {np.array(value).shape}")
        else:
            print("⚠️ No 'action' key returned from server.")

    else:
        raise ValueError("Please specify either --server or --client")


# ==============================================================
# Entry
# ==============================================================
if __name__ == "__main__":
    config = tyro.cli(ArgsConfig)
    main(config)
