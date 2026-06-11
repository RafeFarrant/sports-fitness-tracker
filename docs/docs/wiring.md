# Wiring

This document records the wiring used for the ESP32 sports fitness tracker.

## Current Working Prototype

### ESP32 to MPU6050

| MPU6050 Pin | ESP32 Pin |
|---|---|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO21 |
| SCL | GPIO22 |

### ESP32 to MicroSD Module

| MicroSD Pin | ESP32 Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| CS | GPIO5 |
| SCK / CLK | GPIO18 |
| MISO / DO | GPIO19 |
| MOSI / DI | GPIO23 |

## Battery Power Plan

The next stage is to power the logger from a rechargeable LiPo battery.

Planned power chain:

```text
3.7V LiPo battery
→ TP4056 charger/protection board
→ slide switch
→ 5V boost converter
→ ESP32 VIN/5V pin
