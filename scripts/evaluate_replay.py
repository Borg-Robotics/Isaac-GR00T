import cv2
import zmq
import json
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from tqdm import tqdm
from sklearn.metrics import mean_absolute_error


def send_request_to_server(obs, port=5556, host="localhost"):
    """Send observation to inference server and return predicted action."""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{port}")

    msg = json.dumps({"endpoint": "get_action", "data": obs})
    socket.send_string(msg)

    reply = socket.recv_json()
    socket.close()
    if "error" in reply:
        raise RuntimeError(f"Server error: {reply['error']}")
    return reply["action"]


def flatten_action_dict(pred_action):
    """
    Convert a dict of {joint_name: [[values]]} into a flat (12,) array.
    If output is 192 dims, try to reshape or slice intelligently.
    """
    # Collect all numeric values
    all_values = []
    for k, v in pred_action.items():
        if isinstance(v, list):
            all_values.extend(np.array(v).flatten().tolist())
        elif isinstance(v, np.ndarray):
            all_values.extend(v.flatten().tolist())

    arr = np.array(all_values, dtype=np.float32)

    # 🔧 Handle wrong shapes from diffusion head
    if arr.size == 192:
        print("⚠️ Warning: Model returned 192D output, reshaping to (12, 16) and averaging over last dim.")
        arr = arr.reshape(12, 16).mean(axis=1)
    elif arr.size > 12 and arr.size % 12 == 0:
        print(f"⚠️ Output has {arr.size} dims, downsampling evenly to 12 joints.")
        step = arr.size // 12
        arr = np.array([arr[i*step:(i+1)*step].mean() for i in range(12)])
    elif arr.size < 12:
        print(f"⚠️ Output too small ({arr.size}), padding zeros to 12.")
        arr = np.pad(arr, (0, 12 - arr.size))

    return arr[:12]  # ensure final shape (12,)


def main(args):
    # ---- Load data ----
    parquet_path = f"/workspace/Isaac-GR00T/data/box_pickup_dataset/data/chunk-000/episode_{args.episode_id}.parquet"
    video_path = f"/workspace/Isaac-GR00T/data/box_pickup_dataset/videos/chunk-000/observation.images.cam_head/episode_{args.episode_id}.mp4"

    df = pd.read_parquet(parquet_path)
    print(f"Loaded {len(df)} frames from parquet.")

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Loaded video: {total_frames} frames.")

    gt_actions = []
    pred_actions = []

    # ---- Main loop ----
    for i in tqdm(range(min(len(df), total_frames))):
        ret, frame = cap.read()
        if not ret:
            break

        # ✅ Encode frame
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            print(f"⚠️ Failed to encode frame {i}")
            continue
        frame_b64 = base64.b64encode(buffer).decode("utf-8")

        # ✅ State
        state = df["observation.state"].iloc[i]
        if isinstance(state, np.ndarray):
            state_array = state.tolist()
        elif isinstance(state, list):
            state_array = state
        elif isinstance(state, str):
            try:
                state_array = json.loads(state)
            except Exception:
                state_array = [float(x) for x in state.strip("[]").split(",")]
        else:
            raise TypeError(f"Unexpected state type at frame {i}: {type(state)}")

        obs = {"video.cam_head": frame_b64, "observation.state": state_array}

        try:
            pred_action = send_request_to_server(obs, port=args.port, host=args.host)
            pred_vector = flatten_action_dict(pred_action)
            pred_actions.append(pred_vector)
            gt_actions.append(df["action"].iloc[i])
        except Exception as e:
            print(f"⚠️ Error on frame {i}: {e}")
            break

    cap.release()

    gt_actions = np.array(gt_actions)
    pred_actions = np.array(pred_actions)

    print(f"✅ Collected {len(pred_actions)} predictions")
    print(f"Predicted shape: {pred_actions.shape}, Ground-truth shape: {gt_actions.shape}")

    if len(pred_actions) == 0:
        print("❌ No predictions collected. Check JSON serialization or server handling of image input.")
        return

    # ---- Evaluation ----
    num_joints = gt_actions.shape[1]
    mae_per_joint = [mean_absolute_error(gt_actions[:, j], pred_actions[:, j]) for j in range(num_joints)]

    print("\n📊 Mean Absolute Error per Joint:")
    for j, mae in enumerate(mae_per_joint, start=1):
        print(f"  Joint {j:02d}: {mae:.6f}")

    print(f"\nAverage MAE across all joints: {np.mean(mae_per_joint):.6f}")

    # ---- Plot ----
    fig, axes = plt.subplots(6, 2, figsize=(14, 12))
    axes = axes.flatten()
    for j in range(num_joints):
        axes[j].plot(gt_actions[:, j], label="Ground Truth", color="blue")
        axes[j].plot(pred_actions[:, j], label="Predicted", color="red", linestyle="--")
        axes[j].set_title(f"Joint {j+1}")
        axes[j].legend()
        axes[j].grid(True)

    plt.tight_layout()
    save_path = f"/workspace/Isaac-GR00T/data/replay_eval_{args.episode_id}.png"
    plt.savefig(save_path)
    print(f"\n✅ Saved plot to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-id", type=str, default="000000")
    parser.add_argument("--port", type=int, default=5556)
    parser.add_argument("--host", type=str, default="localhost")
    args = parser.parse_args()
    main(args)
