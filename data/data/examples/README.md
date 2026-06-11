# Example IMU Data

This folder contains small validation datasets collected using the ESP32 + MPU6050 + MicroSD logger.

| File | Description |
|---|---|
| `desk_still_2.csv` | Sensor stationary on a desk |
| `upper_back_still_2.csv` | Sensor worn between the shoulder blades while standing still |
| `walking_2.csv` | Sensor worn between the shoulder blades while walking |

These files are used by `analysis/imu_compare.py` to compare stationary and movement trials.
