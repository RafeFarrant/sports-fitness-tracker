```python
"""
IMU validation analysis script.

Compares stationary and walking trials from the ESP32 + MPU6050 sports tracker.

Calculates:
- sample rate
- dynamic acceleration
- PlayerLoad
- peak count
- dominant frequency

Outputs:
- imu_test_summary.csv
- one plot per input CSV file
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, periodogram


# ---------------------------------------------------------------------
# Files to analyse
# ---------------------------------------------------------------------

FILES = [
    "desk_still_2.csv",
    "upper_back_still_2.csv",
    "walking_2.csv",
]

OUTPUT_SUMMARY = "imu_test_summary.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def load_imu_csv(filepath: str) -> pd.DataFrame:
    """Load an IMU CSV file and create a time column in seconds."""
    df = pd.read_csv(filepath)

    # Normalise column names
    df.columns = [col.strip() for col in df.columns]

    # Create time_s from the available timestamp column
    if "elapsed_ms" in df.columns:
        df["time_s"] = df["elapsed_ms"] / 1000.0
    elif "millis" in df.columns:
        df["time_s"] = (df["millis"] - df["millis"].iloc[0]) / 1000.0
    elif "timestamp_ms" in df.columns:
        df["time_s"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / 1000.0
    else:
        raise ValueError(
            f"{filepath} needs one of: elapsed_ms, millis, timestamp_ms"
        )

    required_cols = ["ax_g", "ay_g", "az_g"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"{filepath} is missing columns: {missing_cols}")

    # Acceleration magnitude
    df["accel_mag_g"] = np.sqrt(
        df["ax_g"] ** 2 +
        df["ay_g"] ** 2 +
        df["az_g"] ** 2
    )

    # Dynamic acceleration: deviation from gravity
    df["accel_dynamic_g"] = np.abs(df["accel_mag_g"] - 1.0)

    return df


def calculate_sample_rate(df: pd.DataFrame) -> float:
    """Estimate sample rate from median timestep."""
    dt = df["time_s"].diff().dropna()
    dt = dt[dt > 0]

    if len(dt) == 0:
        return np.nan

    return 1.0 / dt.median()


def calculate_playerload(df: pd.DataFrame) -> float:
    """
    Calculate PlayerLoad-like movement intensity.

    Uses cumulative vector difference between consecutive acceleration samples.
    """
    dax = df["ax_g"].diff()
    day = df["ay_g"].diff()
    daz = df["az_g"].diff()

    playerload = np.sqrt(dax ** 2 + day ** 2 + daz ** 2).sum()

    return float(playerload)


def calculate_peak_count(df: pd.DataFrame, sample_rate_hz: float) -> int:
    """Count acceleration peaks using a basic threshold."""
    signal = df["accel_dynamic_g"].to_numpy()

    if np.isnan(sample_rate_hz) or sample_rate_hz <= 0:
        return 0

    min_distance = int(0.25 * sample_rate_hz)

    peaks, _ = find_peaks(
        signal,
        height=0.05,
        distance=max(min_distance, 1)
    )

    return int(len(peaks))


def calculate_dominant_frequency(df: pd.DataFrame, sample_rate_hz: float) -> float:
    """Find dominant frequency in the 0.5-10 Hz movement band."""
    if np.isnan(sample_rate_hz) or sample_rate_hz <= 0:
        return np.nan

    signal = df["accel_dynamic_g"].to_numpy()
    signal = signal - np.mean(signal)

    frequencies, power = periodogram(signal, fs=sample_rate_hz)

    movement_band = (frequencies >= 0.5) & (frequencies <= 10.0)

    if not np.any(movement_band):
        return np.nan

    band_frequencies = frequencies[movement_band]
    band_power = power[movement_band]

    dominant_frequency = band_frequencies[np.argmax(band_power)]

    return float(dominant_frequency)


def plot_trial(df: pd.DataFrame, filepath: str) -> None:
    """Save acceleration magnitude and dynamic acceleration plot."""
    input_path = Path(filepath)
    output_path = input_path.with_name(f"{input_path.stem}_plot.png")

    plt.figure(figsize=(10, 5))

    plt.plot(df["time_s"], df["accel_mag_g"], label="Acceleration magnitude")
    plt.plot(df["time_s"], df["accel_dynamic_g"], label="Dynamic acceleration")

    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (g)")
    plt.title(input_path.stem.replace("_", " ").title())
    plt.legend()
    plt.tight_layout()

    plt.savefig(output_path, dpi=200)
    plt.close()


# ---------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------

def analyse_file(filepath: str) -> dict:
    """Analyse one IMU CSV file and return summary metrics."""
    df = load_imu_csv(filepath)

    duration_s = df["time_s"].iloc[-1] - df["time_s"].iloc[0]
    sample_rate_hz = calculate_sample_rate(df)
    playerload = calculate_playerload(df)
    peak_count = calculate_peak_count(df, sample_rate_hz)
    dominant_freq_hz = calculate_dominant_frequency(df, sample_rate_hz)

    plot_trial(df, filepath)

    return {
        "file": Path(filepath).name,
        "samples": len(df),
        "duration_s": round(duration_s, 2),
        "sample_rate_hz": round(sample_rate_hz, 2),
        "mean_dynamic_g": round(df["accel_dynamic_g"].mean(), 4),
        "max_dynamic_g": round(df["accel_dynamic_g"].max(), 4),
        "playerload": round(playerload, 4),
        "peak_count": peak_count,
        "dominant_freq_hz": round(dominant_freq_hz, 3),
    }


def main() -> None:
    """Run analysis for all files."""
    summaries = []

    for filepath in FILES:
        if not Path(filepath).exists():
            print(f"Skipping missing file: {filepath}")
            continue

        print(f"Analysing {filepath}...")
        summaries.append(analyse_file(filepath))

    if not summaries:
        print("No files analysed. Check the FILES list and file locations.")
        return

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)

    print("\nAnalysis complete.")
    print(summary_df.to_string(index=False))
    print(f"\nSaved summary to: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
```
