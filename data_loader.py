# data_loader.py
# Loads a session CSV from the SD card and returns a clean DataFrame.

import pandas as pd
import numpy as np

def load_session(filepath):
    """
    Load a session CSV file.
    Returns a pandas DataFrame with physical units and a time column in seconds.
    """
    df = pd.read_csv(filepath)

    # Convert timestamp from milliseconds to seconds from session start
    df['time_s'] = (df['timestamp_ms'] - df['timestamp_ms'].iloc[0]) / 1000.0

    # Compute vector magnitude of acceleration (total acceleration)
    df['acc_mag'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)

    # Remove gravity component (device at rest reads ~1g)
    # Subtract 1g from the magnitude to get dynamic acceleration
    df['acc_dynamic'] = np.abs(df['acc_mag'] - 1.0)

    print(f"Loaded {len(df)} samples, duration {df['time_s'].iloc[-1]:.1f}s")
    return df

if __name__ == '__main__':
    df = load_session('session1.csv')
    print(df.head())
    print(df.describe())
