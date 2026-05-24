# running_metrics.py
# Full GPS running analysis: velocity, pace zones, cadence, route map.
# Requires GPS columns in CSV (Stage 3 onwards).

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import folium
from data_loader import load_session

# ---- Pace zones (min/km) — adjust to your fitness level ----
# Zone 1: easy/recovery, Zone 2: aerobic base, Zone 3: tempo,
# Zone 4: threshold, Zone 5: race pace / VO2max
PACE_ZONES = [
    ('Zone 1 (easy)',     7.0, 99.0),   # slower than 7:00/km
    ('Zone 2 (aerobic)',  5.5,  7.0),   # 5:30–7:00/km
    ('Zone 3 (tempo)',    4.5,  5.5),   # 4:30–5:30/km
    ('Zone 4 (threshold)',3.8,  4.5),   # 3:48–4:30/km
    ('Zone 5 (race)',     0.0,  3.8),   # faster than 3:48/km
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance in metres between two GPS coordinates."""
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def compute_gps_distance(df):
    """Total GPS distance in kilometres using haversine between consecutive points."""
    gps = df[df['lat'] != 0].copy()
    if len(gps) < 2:
        return 0.0
    dists = [haversine_distance(
        gps['lat'].iloc[i], gps['lon'].iloc[i],
        gps['lat'].iloc[i+1], gps['lon'].iloc[i+1]
    ) for i in range(len(gps)-1)]
    return sum(dists) / 1000.0

def compute_velocity_metrics(df):
    """
    Full velocity breakdown from GPS speed column.
    Returns dict with max/avg velocity and per-km split paces.
    """
    gps = df[(df['lat'] != 0) & (df['speed_kmh'] > 0)].copy()
    if len(gps) == 0:
        return None

    speeds   = gps['speed_kmh'].values
    max_vel  = speeds.max()
    avg_vel  = speeds[speeds > 3].mean()   # Exclude stopped/near-stopped

    # Convert speed to pace (min/km) for zone bucketing
    # Avoid divide-by-zero for stationary rows
    gps = gps.copy()
    gps['pace_min_km'] = np.where(gps['speed_kmh'] > 0.5, 60.0 / gps['speed_kmh'], np.nan)

    # Time in each pace zone (seconds = rows at 1Hz GPS)
    zone_times = {}
    zone_dists = {}
    for name, fast, slow in PACE_ZONES:
        mask = (gps['pace_min_km'] >= fast) & (gps['pace_min_km'] < slow)
        zone_times[name] = int(mask.sum())
        zone_dists[name] = round(gps.loc[mask, 'speed_kmh'].sum() / 3600, 3)

    # Per-km split paces
    distance_km = compute_gps_distance(df)
    avg_pace    = 60.0 / avg_vel if avg_vel > 0 else None

    return {
        'max_velocity_kmh': round(max_vel, 1),
        'avg_velocity_kmh': round(avg_vel, 1),
        'avg_pace_min_km':  round(avg_pace, 2) if avg_pace else None,
        'total_distance_km':round(distance_km, 2),
        'zone_times_s':     zone_times,
        'zone_dists_km':    zone_dists,
    }

def compute_cadence(df, sample_rate=100):
    """Steps per minute from vertical acceleration peak detection."""
    peaks, _ = find_peaks(
        df['az'].values,
        height=0.3,
        distance=sample_rate * 0.25
    )
    duration_min = df['time_s'].iloc[-1] / 60.0
    return (len(peaks) / duration_min) if duration_min > 0 else 0

def create_route_map(df, output_file='route.html'):
    """
    Interactive route map with pace colour coding.
    Green = fast pace, red = slow pace.
    """
    gps = df[(df['lat'] != 0) & (df['lat'].notna())].copy()
    if len(gps) < 2:
        print('Not enough GPS data for a map.')
        return

    centre = [gps['lat'].mean(), gps['lon'].mean()]
    m = folium.Map(location=centre, zoom_start=15, tiles='OpenStreetMap')

    # Colour-code route segments by speed
    coords = list(zip(gps['lat'], gps['lon']))
    speeds = gps['speed_kmh'].values
    max_s  = speeds.max() if speeds.max() > 0 else 1

    for i in range(len(coords)-1):
        ratio = min(speeds[i] / max_s, 1.0)
        # Green (fast) to red (slow) colour interpolation
        r = int(255 * (1 - ratio))
        g = int(200 * ratio)
        color = f'#{r:02X}{g:02X}30'
        folium.PolyLine([coords[i], coords[i+1]], color=color, weight=4, opacity=0.85).add_to(m)

    folium.Marker(coords[0],  popup='Start',  icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(coords[-1], popup='Finish', icon=folium.Icon(color='red')).add_to(m)

    m.save(output_file)
    print(f'Route map saved to {output_file}')

def running_report(filepath):
    df  = load_session(filepath)
    vel = compute_velocity_metrics(df)
    cad = compute_cadence(df)

    print(f"\n=== Running Session Report ===")
    print(f"Duration:      {df['time_s'].iloc[-1]/60:.1f} min")
    if vel:
        mins = int(vel['avg_pace_min_km'])
        secs = int((vel['avg_pace_min_km'] - mins) * 60)
        print(f"Total distance:{vel['total_distance_km']} km")
        print(f"Max velocity:  {vel['max_velocity_kmh']} km/h")
        print(f"Avg velocity:  {vel['avg_velocity_kmh']} km/h")
        print(f"Avg pace:      {mins}:{secs:02d} /km")
        print(f"Cadence:       {cad:.0f} spm")
        print(f"\n--- Time and distance by pace zone ---")
        for name, _, _ in PACE_ZONES:
            t = vel['zone_times_s'][name]
            d = vel['zone_dists_km'][name]
            print(f"  {name:<28} {t:>4}s   {d:.3f} km")
    create_route_map(df)

if __name__ == '__main__':
    running_report('session1.csv')
