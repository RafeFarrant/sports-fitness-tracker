## 2026-05-23
**Phase:** Setup
**Did:** Ordered Stage 1 components — ELEGOO ESP32 CP2102, 
DollaTek MicroSD module 5-pack, KEXIN 16GB MicroSD, found the MPU-6050
**Result:** Order placed, delivery expected mid-week
**Issue:** in order to receive ESP32 in time to use had to order the 13.99 two pack rather than predicted cost £9
**Fix:** 
**Next:** Solder MPU-6050 header pins in lab Monday

## 2026-05-24
**Phase:** Setup
**Did:** Installed Arduino IDE, added ESP32 board support, 
installed MPU6050 and TinyGPS++ libraries, set up GitHub repo, 
added firmware and Python analysis pipeline
**Result:** Arduino IDE compiling, repo live at 
github.com/RafeFarrant/sports-fitness-tracker
**Issue:** GitHub folder structure created as files not folders
**Fix:** Deleted and recreated with correct paths
**Next:** solder MPU-6050 Monday

## 2026-05-27
**Phase:** Hardware
**Did:** Wired MPU-6050 via I2C, uploaded firmware
**Result:** IMU OK on first attempt
**Issue:** SD card failed
**Fix:** Card reader ordered — format issue, arriving tomorrow
**Next:** Format SD card as FAT32, confirm SD card OK

## 2026-05-28
**Phase:** Software
**Did:** Ran imu_metrics.py and plot_session.py on lift test data
**Result:** Clean data — PlayerLoad 79.57, peak 1.3g, cadence 94.8 spm
**Issue:** No gyro data yet
**Fix:** Updating Arduino sketch to include gyro output
**Next:** Retest with gyro, then SD card workflow tomorrow
