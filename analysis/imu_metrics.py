import pandas as pd
import numpy as np
from scipy.signal import find_peaks

df = pd.read_csv("session1.csv")

# Handle both column naming formats
if 'timestamp_ms' in df.columns:
    df["time_s"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / 1000
elif 'time_ms' in df.columns:
    df["time_s"] = (df["time_ms"] - df["time_ms"].iloc[0]) / 1000

# Rename columns if needed
if 'ax_g' not in df.columns and 'ax' in df.columns:
    df = df.rename(columns={'ax':'ax_g','ay':'ay_g','az':'az_g'})

df["acc_mag"] = np.sqrt(df["ax_g"]**2 + df["ay_g"]**2 + df["az_g"]**2)
df["dynamic_acc"] = np.abs(df["acc_mag"] - 1)

# PlayerLoad
dax = np.diff(df["ax_g"])
day = np.diff(df["ay_g"])
daz = np.diff(df["az_g"])
df["playerload_step"] = np.insert(np.sqrt(dax**2 + day**2 + daz**2), 0, 0)
df["playerload_cumulative"] = df["playerload_step"].cumsum()

# Per-minute bins
df["minute"] = (df["time_s"] // 60).astype(int)
per_min = df.groupby("minute").agg(
    playerload_per_min=("playerload_step", "sum"),
    mean_intensity=("dynamic_acc", "mean"),
    peak_acceleration=("acc_mag", "max")
)

# Work/rest ratio
ACTIVE_THRESHOLD = 0.08
df["active"] = df["dynamic_acc"] > ACTIVE_THRESHOLD
work_rest = df.groupby("minute")["active"].mean()
per_min["work_rest_ratio"] = work_rest

# Peak acceleration
peak_acc = df["acc_mag"].max()

# Cadence from vertical acceleration
peaks, _ = find_peaks(df["az_g"], distance=30, prominence=0.05)
duration_min = df["time_s"].iloc[-1] / 60
cadence_spm = len(peaks) / duration_min if duration_min > 0 else 0

# Acceleration event count
accel_events, _ = find_peaks(df["dynamic_acc"], prominence=0.15, distance=20)

# Direction changes from gyro if available
if 'gz' in df.columns or 'gz_dps' in df.columns:
    gz_col = 'gz' if 'gz' in df.columns else 'gz_dps'
    gz_abs = np.abs(df[gz_col].values)
    dir_changes = np.where(gz_abs > 200)[0]
    min_gap = 50
    events, last = [], -min_gap
    for idx in dir_changes:
        if idx - last > min_gap:
            events.append(idx)
            last = idx
    dir_change_count = len(events)
else:
    dir_change_count = "N/A (no gyro data)"

print("=== IMU Session Report ===")
print(f"Session duration:    {round(df['time_s'].iloc[-1], 1)} s")
print(f"Total PlayerLoad:    {round(df['playerload_cumulative'].iloc[-1], 2)}")
print(f"Peak acceleration:   {round(peak_acc, 2)} g")
print(f"Cadence estimate:    {round(cadence_spm, 1)} steps/min")
print(f"Acceleration events: {len(accel_events)}")
print(f"Direction changes:   {dir_change_count}")
print()
print("--- Per minute breakdown ---")
print(per_min.round(3))
