# Sports Fitness Tracker

A wearable IMU-based sports performance logger for hockey and running.

The project uses an ESP32, MPU6050 inertial sensor and MicroSD card module to collect acceleration and gyroscope data, then analyses the data in Python to estimate movement intensity, PlayerLoad, cadence and activity patterns.

## Current Status

## Development Status

| Stage | Status | Notes |
|---|---|---|
| IMU wiring | Complete | MPU6050 connected over I2C |
| SD logging | Complete | CSV logging working |
| Python analysis | Complete v1 | PlayerLoad, dynamic acceleration and dominant frequency calculated |
| Battery power | In progress | LiPo, TP4056 and boost converter stage |
| Wearable enclosure | Planned | Compression vest/back-mounted unit |
| GPS | Planned | NEO-6M module for distance/speed tracking |

## Firmware

The current firmware is a timed ESP32 logger located at:

`firmware/imu_sd_timed_logger/imu_sd_timed_logger.ino`

It logs MPU6050 accelerometer and gyroscope readings to a CSV file on the MicroSD card. The current version starts automatically, records for a fixed duration and safely closes the file at the end of the session.
