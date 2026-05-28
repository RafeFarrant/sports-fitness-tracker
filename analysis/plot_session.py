import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Load data
df = pd.read_csv("session1.csv")

# Handle column naming
if 'timestamp_ms' in df.columns:
    df["time_s"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / 1000
elif 'time_ms' in df.columns:
    df["time_s"] = (df["time_ms"] - df["time_ms"].iloc[0]) / 1000

if 'ax_g' not in df.columns and 'ax' in df.columns:
    df = df.rename(columns={'ax':'ax_g','ay':'ay_g','az':'az_g'})

df["acc_mag"] = np.sqrt(df["ax_g"]**2 + df["ay_g"]**2 + df["az_g"]**2)
df["dynamic_acc"] = np.abs(df["acc_mag"] - 1)

# PlayerLoad cumulative
dax = np.diff(df["ax_g"])
day = np.diff(df["ay_g"])
daz = np.diff(df["az_g"])
pl_steps = np.insert(np.sqrt(dax**2 + day**2 + daz**2), 0, 0)
df["playerload_cumulative"] = np.cumsum(pl_steps)

# Find acceleration peaks
peaks, _ = find_peaks(df["acc_mag"], prominence=0.05, distance=20)

# ---- Plot ----
fig, axes = plt.subplots(3, 1, figsize=(12, 10))
fig.suptitle('IMU Session Analysis — Lift Test', fontsize=15, fontweight='bold', color='#0F6E56')
fig.patch.set_facecolor('#FAFAFA')

# Panel 1: Individual axes + magnitude
ax = axes[0]
ax.plot(df["time_s"], df["ax_g"], color='#378ADD', linewidth=1, alpha=0.8, label='ax')
ax.plot(df["time_s"], df["ay_g"], color='#BA7517', linewidth=1, alpha=0.8, label='ay')
ax.plot(df["time_s"], df["az_g"], color='#1D9E75', linewidth=1.5, label='az (vertical)')
ax.plot(df["time_s"], df["acc_mag"], color='#D85A30', linewidth=2, label='magnitude')
ax.axhline(1.0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5, label='1g (gravity)')
ax.set_ylabel('Acceleration (g)')
ax.set_title('Acceleration axes over time')
ax.legend(fontsize=9, loc='upper right')
ax.set_facecolor('#F8F8F8')

# Panel 2: Dynamic acceleration with lift events highlighted
ax = axes[1]
ax.plot(df["time_s"], df["acc_mag"], color='#1D9E75', linewidth=1.5, label='Total magnitude')
ax.fill_between(df["time_s"], 1.0, df["acc_mag"],
                where=df["acc_mag"] > 1.02,
                alpha=0.3, color='#D85A30', label='Above 1g (accelerating up)')
ax.fill_between(df["time_s"], df["acc_mag"], 1.0,
                where=df["acc_mag"] < 0.98,
                alpha=0.3, color='#378ADD', label='Below 1g (decelerating)')
ax.axhline(1.0, color='gray', linewidth=1, linestyle='--', alpha=0.6)
ax.set_ylabel('Acceleration magnitude (g)')
ax.set_title('Lift phases — red = accelerating upward, blue = decelerating')
ax.legend(fontsize=9)
ax.set_facecolor('#F8F8F8')

# Panel 3: Cumulative PlayerLoad
ax = axes[2]
ax.plot(df["time_s"], df["playerload_cumulative"], color='#7F77DD', linewidth=2.5)
ax.fill_between(df["time_s"], 0, df["playerload_cumulative"], alpha=0.15, color='#7F77DD')
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('PlayerLoad')
ax.set_title(f'Cumulative PlayerLoad (total: {df["playerload_cumulative"].iloc[-1]:.2f})')
ax.set_facecolor('#F8F8F8')

plt.tight_layout()
plt.savefig('lift_test_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved to lift_test_analysis.png")
