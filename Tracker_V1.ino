// ================================================================
// Sports Fitness Tracker — Phase 1 Firmware
// IMU logging to SD card
// Target: ESP32 Dev Module
// ================================================================

#include <Wire.h>          // I2C communication (for IMU)
#include <MPU6050.h>       // IMU library by Electronic Cats
#include <SD.h>            // SD card library (built into Arduino IDE)
#include <SPI.h>           // SPI bus (for SD card)

// ---- Pin definitions ----
const int SD_CS_PIN  = 5;   // SD card chip select
const int BTN_PIN    = 0;   // Session start/stop button (GPIO0)
const int LED_PIN    = 2;   // Onboard LED (GPIO2 on most ESP32 boards)

// ---- IMU object ----
MPU6050 imu;

// ---- Session state ----
bool logging       = false;  // True when a session is active
File sessionFile;            // The open file on the SD card
int  sessionCount  = 0;      // Increments each session for unique filenames
unsigned long lastSample = 0;
const int SAMPLE_INTERVAL_MS = 10; // 100Hz (10ms between samples)

// ---- Button debounce ----
bool     lastBtnState = HIGH;
unsigned long lastDebounce = 0;
const int DEBOUNCE_MS = 50;

// ================================================================
void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP); // Internal pull-up: HIGH = not pressed
  pinMode(LED_PIN, OUTPUT);

  // ---- Initialise I2C and IMU ----
  Wire.begin();          // Start I2C on default SDA/SCL (GPIO21/22)
  imu.initialize();      // Power on and configure MPU-6050

  if (!imu.testConnection()) {
    Serial.println("IMU connection failed. Check wiring.");
    while (true) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); delay(200); }
    // Fast blink = IMU error. Check SDA/SCL connections.
  }
  Serial.println("IMU OK");

  // Set accelerometer range to +/-8g (good for sport, not too sensitive)
  imu.setFullScaleAccelRange(MPU6050_ACCEL_FS_8);
  // Set gyroscope range to +/-1000 degrees/sec
  imu.setFullScaleGyroRange(MPU6050_GYRO_FS_1000);

  // ---- Initialise SD card ----
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("SD card failed. Check wiring or card format (must be FAT32).");
    while (true) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); delay(500); }
    // Slow blink = SD error.
  }
  Serial.println("SD card OK");
  digitalWrite(LED_PIN, HIGH); // Solid LED = ready
}

// ================================================================
void loop() {
  handleButton();   // Check for session start/stop
  if (logging) {
    logSample();    // Write one row of IMU data
  }
}

// ================================================================
// handleButton: debounced button to start/stop session
void handleButton() {
  bool state = digitalRead(BTN_PIN);
  if (state != lastBtnState) {
    lastDebounce = millis();
  }
  if ((millis() - lastDebounce) > DEBOUNCE_MS && state == LOW && lastBtnState == HIGH) {
    // Button just pressed (LOW because of pull-up)
    if (!logging) startSession();
    else          stopSession();
  }
  lastBtnState = state;
}

// ================================================================
// startSession: open a new CSV file and write the header row
void startSession() {
  sessionCount++;
  String filename = "/session" + String(sessionCount) + ".csv";
  sessionFile = SD.open(filename, FILE_WRITE);
  if (!sessionFile) {
    Serial.println("Could not open file for writing.");
    return;
  }
  // Write CSV header
  sessionFile.println("timestamp_ms,ax,ay,az,gx,gy,gz");
  logging = true;
  Serial.println("Session started: " + filename);
  // Blink LED twice to confirm
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_PIN, LOW); delay(100);
    digitalWrite(LED_PIN, HIGH); delay(100);
  }
}

// ================================================================
// stopSession: flush and close the file safely
void stopSession() {
  sessionFile.flush(); // Ensure all buffered data is written
  sessionFile.close();
  logging = false;
  Serial.println("Session stopped and saved.");
  // Three blinks to confirm save
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW); delay(80);
    digitalWrite(LED_PIN, HIGH); delay(80);
  }
}

// ================================================================
// logSample: read IMU and write one CSV row at 100Hz
void logSample() {
  if (millis() - lastSample < SAMPLE_INTERVAL_MS) return;
  lastSample = millis();

  int16_t ax, ay, az, gx, gy, gz;
  imu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Convert raw values to physical units
  // Accel scale: +/-8g range, 16-bit ADC -> divide by 4096 for g
  // Gyro scale:  +/-1000 dps range -> divide by 32.8 for degrees/sec
  float ax_g  = ax  / 4096.0;
  float ay_g  = ay  / 4096.0;
  float az_g  = az  / 4096.0;
  float gx_ds = gx  / 32.8;
  float gy_ds = gy  / 32.8;
  float gz_ds = gz  / 32.8;

  // Write comma-separated row
  sessionFile.print(millis()); sessionFile.print(',');
  sessionFile.print(ax_g, 4);  sessionFile.print(',');
  sessionFile.print(ay_g, 4);  sessionFile.print(',');
  sessionFile.print(az_g, 4);  sessionFile.print(',');
  sessionFile.print(gx_ds, 2); sessionFile.print(',');
  sessionFile.print(gy_ds, 2); sessionFile.print(',');
  sessionFile.println(gz_ds, 2);
}
