# session_dashboard.py
# Full 4-panel visual dashboard for hockey and running sessions.
# Usage: python session_dashboard.py session1.csv hockey
#        python session_dashboard.py session1.csv running

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from data_loader import load_session
from hockey_metrics import (
    compute_playerload, compute_gps_velocity_metrics,
    detect_direction_changes, detect_accelerations_decelerations,
    compute_work_rest_ratio
)
from running_metrics import compute_velocity_metrics, compute_cadence, PACE_ZONES

def fmt_pace(pace_min_km):
    """Convert decimal min/km to mm:ss string."""
    if pace_min_km is None: return 'N/A'
    m = int(pace_min_km)
    s = int((pace_min_km - m) * 60)
    return f'{m}:{s:02d} /km'

# ================================================================
def plot_hockey_dashboard(df):
    pl_cum, pl_total = compute_playerload(df)
    vel  = compute_gps_velocity_metrics(df)
    dir_changes = detect_direction_changes(df)
    accels, decels = detect_accelerations_decelerations(df)
    work_rest = compute_work_rest_ratio(df)
    time = df['time_s'].values / 60

    fig, axes = plt.subplots(2, 2, figsize=(15, 9))
    fig.suptitle('Hockey Session Report', fontsize=17, fontweight='bold', color='#0F6E56', y=0.98)
    fig.patch.set_facecolor('#FAFAFA')

    # ---- Panel 1: Speed over time with zone bands ----
    ax = axes[0, 0]
    if vel and 'speed_kmh' in df.columns:
        gps = df[df['lat'] != 0].copy()
        gps_time = gps['time_s'].values / 60
        ax.fill_between(gps_time, 0, gps['speed_kmh'].values, alpha=0.4, color='#378ADD')
        ax.plot(gps_time, gps['speed_kmh'].values, color='#1A5FA5', linewidth=1)
        # Draw threshold lines
        for thresh, label, col in [(18,'HSR','#BA7517'),(24,'Sprint','#D85A30')]:
            ax.axhline(thresh, color=col, linewidth=1, linestyle='--', alpha=0.7, label=label)
        ax.legend(fontsize=9)
    else:
        ax.plot(time, df['acc_mag'].values, color='#378ADD', linewidth=0.5, alpha=0.7)
    ax.set_xlabel('Time (min)'); ax.set_ylabel('Speed (km/h)')
    ax.set_title('Speed over time')

    # ---- Panel 2: Cumulative PlayerLoad ----
    ax = axes[0, 1]
    t_pl = time[:len(pl_cum)]
    ax.plot(t_pl, pl_cum, color='#1D9E75', linewidth=2.5)
    ax.fill_between(t_pl, 0, pl_cum, alpha=0.15, color='#1D9E75')
    ax.set_xlabel('Time (min)'); ax.set_ylabel('PlayerLoad')
    ax.set_title(f'Cumulative PlayerLoad (total: {pl_total:.1f})')

    # ---- Panel 3: Speed zone distance bar chart ----
    ax = axes[1, 0]
    if vel:
        zones  = list(vel['zone_dists_km'].keys())
        dists  = [vel['zone_dists_km'][z] for z in zones]
        colors = ['#AAAAAA','#378ADD','#1D9E75','#BA7517','#D85A30']
        short_labels = ['Walk','Jog','Run','HSR','Sprint']
        bars = ax.bar(short_labels, dists, color=colors, edgecolor='white')
        ax.bar_label(bars, fmt='%.2f km', fontsize=9, padding=2)
    ax.set_ylabel('Distance (km)')
    ax.set_title('Distance by speed zone')

    # ---- Panel 4: Key metrics summary ----
    ax = axes[1, 1]
    ax.axis('off')
    ax.set_facecolor('#F0FAF6')
    stats = [
        ('Duration',        f"{time[-1]:.1f} min"),
        ('PlayerLoad',      f"{pl_total:.1f}"),
        ('Total distance',  f"{vel['total_distance_km']} km" if vel else 'N/A'),
        ('Max velocity',    f"{vel['max_velocity_kmh']} km/h" if vel else 'N/A'),
        ('Avg velocity',    f"{vel['avg_velocity_kmh']} km/h" if vel else 'N/A'),
        ('Sprints',         str(vel['sprint_count']) if vel else 'N/A'),
        ('Dir. changes',    str(len(dir_changes))),
        ('Accelerations',   str(accels)),
        ('Decelerations',   str(decels)),
    ]
    ax.text(0.5, 0.97, 'Session summary', ha='center', va='top', fontsize=12,
            fontweight='bold', color='#0F6E56', transform=ax.transAxes)
    for i, (label, value) in enumerate(stats):
        y = 0.83 - i * 0.095
        ax.text(0.05, y, label, fontsize=10, color='#444444', transform=ax.transAxes)
        ax.text(0.65, y, value, fontsize=11, fontweight='bold', color='#0F6E56', transform=ax.transAxes)

    plt.tight_layout()
    plt.savefig('hockey_session.png', dpi=150, bbox_inches='tight')
    plt.show()
    print('Dashboard saved to hockey_session.png')

# ================================================================
def plot_running_dashboard(df):
    vel = compute_velocity_metrics(df)
    cad = compute_cadence(df)
    time = df['time_s'].values / 60

    fig, axes = plt.subplots(2, 2, figsize=(15, 9))
    fig.suptitle('Running Session Report', fontsize=17, fontweight='bold', color='#0F6E56', y=0.98)
    fig.patch.set_facecolor('#FAFAFA')

    # ---- Panel 1: Speed over time ----
    ax = axes[0, 0]
    if 'speed_kmh' in df.columns:
        gps = df[df['lat'] != 0].copy()
        gps_time = gps['time_s'].values / 60
        ax.fill_between(gps_time, 0, gps['speed_kmh'].values, alpha=0.35, color='#378ADD')
        ax.plot(gps_time, gps['speed_kmh'].values, color='#1A5FA5', linewidth=1.2)
        if vel:
            ax.axhline(vel['avg_velocity_kmh'], color='#1D9E75', linewidth=1.5,
                      linestyle='--', label=f"Avg {vel['avg_velocity_kmh']} km/h")
            ax.legend(fontsize=9)
    ax.set_xlabel('Time (min)'); ax.set_ylabel('Speed (km/h)')
    ax.set_title('Speed over time')

    # ---- Panel 2: Pace zone time bar chart ----
    ax = axes[0, 1]
    if vel:
        zones  = [z for z, _, _ in PACE_ZONES]
        times  = [vel['zone_times_s'][z] for z in zones]
        colors = ['#AAAAAA','#378ADD','#1D9E75','#BA7517','#D85A30']
        short  = ['Z1 Easy','Z2 Aerobic','Z3 Tempo','Z4 Threshold','Z5 Race']
        bars   = ax.barh(short, times, color=colors, edgecolor='white')
        ax.bar_label(bars, fmt='%ds', fontsize=9, padding=2)
    ax.set_xlabel('Time (seconds)')
    ax.set_title('Time in pace zones')

    # ---- Panel 3: Cadence over time ----
    ax = axes[1, 0]
    # Rolling cadence: peaks per 30s window
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(df['az'].values, height=0.3, distance=25)
    window_s = 30
    sr = 100
    win_cadences, win_times = [], []
    for start in range(0, len(df) - window_s*sr, window_s*sr // 2):
        end = start + window_s*sr
        n = sum(1 for p in peaks if start <= p < end)
        win_cadences.append(n * (60/window_s))
        win_times.append(df['time_s'].iloc[start + window_s*sr//2] / 60)
    ax.plot(win_times, win_cadences, color='#7F77DD', linewidth=2)
    ax.axhline(180, color='#D85A30', linewidth=1, linestyle='--', alpha=0.6, label='180 spm target')
    ax.legend(fontsize=9)
    ax.set_xlabel('Time (min)'); ax.set_ylabel('Cadence (spm)')
    ax.set_title('Running cadence over time')

    # ---- Panel 4: Key metrics summary ----
    ax = axes[1, 1]
    ax.axis('off')
    stats = [
        ('Duration',      f"{time[-1]:.1f} min"),
        ('Total distance', f"{vel['total_distance_km']} km" if vel else 'N/A'),
        ('Max velocity',   f"{vel['max_velocity_kmh']} km/h" if vel else 'N/A'),
        ('Avg velocity',   f"{vel['avg_velocity_kmh']} km/h" if vel else 'N/A'),
        ('Avg pace',       fmt_pace(vel['avg_pace_min_km']) if vel else 'N/A'),
        ('Avg cadence',    f"{cad:.0f} spm"),
    ]
    ax.text(0.5, 0.97, 'Session summary', ha='center', va='top', fontsize=12,
            fontweight='bold', color='#0F6E56', transform=ax.transAxes)
    for i, (label, value) in enumerate(stats):
        y = 0.83 - i * 0.13
        ax.text(0.05, y, label, fontsize=10, color='#444444', transform=ax.transAxes)
        ax.text(0.65, y, value, fontsize=11, fontweight='bold', color='#0F6E56', transform=ax.transAxes)

    plt.tight_layout()
    plt.savefig('running_session.png', dpi=150, bbox_inches='tight')
    plt.show()
    print('Dashboard saved to running_session.png')

# ================================================================
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python session_dashboard.py <csv_file> <hockey|running>')
        sys.exit(1)
    df = load_session(sys.argv[1])
    if sys.argv[2] == 'hockey':
        plot_hockey_dashboard(df)
    else:
        plot_running_dashboard(df)
