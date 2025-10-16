import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- CONFIG ---
# Path to your recorded dataset
file_path = "/workspace/Isaac-GR00T/data/box_pickup_dataset/data/chunk-000/episode_000000.parquet"
save_path = "/workspace/Isaac-GR00T/data/joint_action_comparison.png"

# --- LOAD DATA ---
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

df = pd.read_parquet(file_path)
print(f"✅ Loaded dataset: {file_path}")
print("Columns:", df.columns.tolist())

# --- EXPAND STATE + ACTION ARRAYS ---
state_array = np.stack(df["observation.state"].to_numpy())
action_array = np.stack(df["action"].to_numpy())

state_df = pd.DataFrame(state_array, columns=[f"state.joint_{i+1}" for i in range(state_array.shape[1])])
action_df = pd.DataFrame(action_array, columns=[f"action.joint_{i+1}" for i in range(action_array.shape[1])])

# --- COMBINE ---
full_df = pd.concat([state_df, action_df], axis=1)

# --- PLOT ---
fig, axes = plt.subplots(6, 2, figsize=(14, 12))
axes = axes.flatten()

for i in range(12):
    axes[i].plot(full_df[f"state.joint_{i+1}"], label="state", color="blue")
    axes[i].plot(full_df[f"action.joint_{i+1}"], label="action", color="red", linestyle="--")
    axes[i].set_title(f"Joint {i+1}")
    axes[i].set_xlabel("Frame index")
    axes[i].set_ylabel("Position (radians)")
    axes[i].grid(True)
    axes[i].legend()

plt.tight_layout()
plt.savefig(save_path)
print(f"✅ Saved joint comparison plot to: {save_path}")

# Optional: display interactively (comment this out if running headless)
# plt.show()

# --- MSE CHECK ---
print("\n🔍 Mean Squared Error between state and action per joint:")
for i in range(12):
    mse = np.mean((full_df[f"state.joint_{i+1}"] - full_df[f"action.joint_{i+1}"])**2)
    print(f"  Joint {i+1}: MSE = {mse:.6f}")