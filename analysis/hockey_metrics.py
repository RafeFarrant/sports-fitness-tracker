# hockey_metrics.py
# Full outdoor hockey metrics using GPS + IMU.
# Requires GPS columns in CSV (Stage 3 onwards).

import numpy as np
import pandas as pd
from data_loader import load_session

# ---- Speed thresholds (km/h) — adjust to your level ----
WALK_THRESHOLD      =  7.0   # Below this = standing/walking
JOG_THRESHOLD       = 13.0   # 7–13 km/h = jogging
RUN_THRESHOLD       = 18.0   # 13–18 km/h = running
HIGH_SPEED_THRESHOLD= 21.0   # 18–21 km/h = high speed running
SPRINT_THRESHOLD    = 24.0   # Above 24 km/h = sprinting (adjust to you)

def compute_playerload(df, sample_rate=100):
    """
    PlayerLoad = cumulative sum of triaxial acceleration differences.
    Standard metric used by Catapult and STATSports.
    """
    dax = np.diff(df['ax'].values)
    day = np.diff(df['ay'].values)
    daz = np.diff(df['az'].values)
    pl_per_sample = np.sqrt(dax**2 + day**2 + daz**2) / sample_rate
    return np.cumsum(pl_per_sample), np.sum(pl_per_sample)

def compute_gps_velocity_metrics(df):
    """
    GPS-based velocity metrics.
    Returns dict of max velocity, average velocity, and speed zone breakdowns.
    All speeds in km/h. All distances in km. All times in seconds.
    """
    gps = df[(df['lat'] != 0) & (df['speed_kmh'] > 0)].copy()
    if len(gps) == 0:
        return None

    # GPS updates at 1Hz so each row represents ~1 second
    # Use speed column directly for velocity metrics
    speeds = gps['speed_kmh'].values

    max_velocity   = speeds.max()
    avg_velocity   = speeds[speeds > WALK_THRESHOLD].mean()  # Exclude standing

    # Time in each speed zone (seconds)
    t_walk      = (speeds < JOG_THRESHOLD).sum()
    t_jog       = ((speeds >= JOG_THRESHOLD) & (speeds < RUN_THRESHOLD)).sum()
    t_run       = ((speeds >= RUN_THRESHOLD) & (speeds < HIGH_SPEED_THRESHOLD)).sum()
    t_hsr       = ((speeds >= HIGH_SPEED_THRESHOLD) & (speeds < SPRINT_THRESHOLD)).sum()
    t_sprint    = (speeds >= SPRINT_THRESHOLD).sum()

    # Distance in each zone (km): time(s) * speed(km/h) / 3600
    d_walk   = (gps.loc[gps['speed_kmh'] < JOG_THRESHOLD, 'speed_kmh'].sum()) / 3600
    d_jog    = (gps.loc[(gps['speed_kmh'] >= JOG_THRESHOLD) & (gps['speed_kmh'] < RUN_THRESHOLD), 'speed_kmh'].sum()) / 3600
    d_run    = (gps.loc[(gps['speed_kmh'] >= RUN_THRESHOLD) & (gps['speed_kmh'] < HIGH_SPEED_THRESHOLD), 'speed_kmh'].sum()) / 3600
    d_hsr    = (gps.loc[(gps['speed_kmh'] >= HIGH_SPEED_THRESHOLD) & (gps['speed_kmh'] < SPRINT_THRESHOLD), 'speed_kmh'].sum()) / 3600
    d_sprint = (gps.loc[gps['speed_kmh'] >= SPRINT_THRESHOLD, 'speed_kmh'].sum()) / 3600
    d_total  = d_walk + d_jog + d_run + d_hsr + d_sprint

    # Sprint count: each continuous block above sprint threshold = one sprint
    in_sprint = False
    sprint_count = 0
    for s in speeds:
        if s >= SPRINT_THRESHOLD and not in_sprint:
            sprint_count += 1
            in_sprint = True
        elif s < SPRINT_THRESHOLD:
            in_sprint = False

    return {
        'max_velocity_kmh':    round(max_velocity, 1),
        'avg_velocity_kmh':    round(avg_velocity, 1),
        'total_distance_km':   round(d_total, 2),
        'sprint_count':        sprint_count,
        'time_walking_s':      int(t_walk),
        'time_jogging_s':      int(t_jog),
        'time_running_s':      int(t_run),
        'time_hsr_s':          int(t_hsr),
        'time_sprinting_s':    int(t_sprint),
        'dist_walking_km':     round(d_walk, 2),
        'dist_jogging_km':     round(d_jog, 2),
        'dist_running_km':     round(d_run, 2),
        'dist_hsr_km':         round(d_hsr, 3),
        'dist_sprinting_km':   round(d_sprint, 3),
    }

def detect_accelerations_decelerations(df, threshold_g=0.5, sample_rate=100):
    """
    Count high-intensity acceleration and deceleration events from IMU.
    IMU gives better resolution than GPS for this metric.
    Returns: (accel_count, decel_count)
    """
    # Forward acceleration = positive change in acc_dynamic
    # Deceleration = negative change (braking)
    acc_diff = np.diff(df['acc_dynamic'].values)
    min_gap  = int(0.5 * sample_rate)  # 0.5s minimum between events

    accel_events, decel_events = [], []
    last_a, last_d = -min_gap, -min_gap

    for i, d in enumerate(acc_diff):
        if d > threshold_g and i - last_a > min_gap:
            accel_events.append(i)
            last_a = i
        elif d < -threshold_g and i - last_d > min_gap:
            decel_events.append(i)
            last_d = i

    return len(accel_events), len(decel_events)

def detect_direction_changes(df, threshold_gyro=200, sample_rate=100):
    """
    Direction change = rapid spike in gyroscope yaw (gz) above threshold.
    threshold_gyro: degrees/second
    """
    gz = np.abs(df['gz'].values)
    changes = np.where(gz > threshold_gyro)[0]
    min_gap = int(0.5 * sample_rate)
    events, last = [], -min_gap
    for idx in changes:
        if idx - last > min_gap:
            events.append(df['time_s'].iloc[idx])
            last = idx
    return events

def compute_work_rest_ratio(df, active_threshold_g=0.3, window_s=60):
    """Work/rest ratio per minute window. Returns list of (minute, ratio) tuples."""
    sample_rate = 100
    window = window_s * sample_rate
    ratios = []
    for start in range(0, len(df) - window, window):
        chunk  = df['acc_dynamic'].iloc[start:start+window]
        active = (chunk > active_threshold_g).sum()
        rest   = window - active
        ratio  = active / rest if rest > 0 else float('inf')
        ratios.append((start // window + 1, ratio))
    return ratios

def hockey_report(filepath):
