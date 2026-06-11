# Sports Fitness Tracker

A wearable IMU-based sports performance logger for hockey and running.

The project uses an ESP32, MPU6050 inertial sensor and MicroSD card module to collect acceleration and gyroscope data, then analyses the data in Python to estimate movement intensity, PlayerLoad, cadence and activity patterns.

## Current Status

- ESP32 successfully logging MPU6050 data to MicroSD
- Stable sample rate of approximately 83 Hz achieved
- Initial stationary and walking trials completed
- Python analysis pipeline calculates dynamic acceleration, PlayerLoad and dominant frequency
- Battery power system and GPS integration are currently in development
