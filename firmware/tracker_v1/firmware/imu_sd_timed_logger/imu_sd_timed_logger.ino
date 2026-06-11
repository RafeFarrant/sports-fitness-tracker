// ESP32 IMU + SD timed logger
// Logs MPU6050 acceleration and gyroscope data to MicroSD as CSV
// Current version: timed logging, no button required
// Tested sample rate: approximately 83 Hz
// Hardware: ESP32 Dev Module, MPU6050, MicroSD module

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <math.h>

// -------------------------
// Test settings
// CHANGE THESE FOR EACH TEST
// -------------------------
#define TEST_NAME "walking"
#define LOG_DURATION_MS 30000

// -------------------------
// Hardware pins
// -------------------------
#define SD_CS_PIN 5
#define MPU_ADDR 0x68
#define LED_PIN 2

// -------------------------
// Timing settings
// -------------------------
#define START_DELAY_MS 3000
#define SAMPLE_DELAY_MS 10
#define FLUSH_EVERY_ROWS 10

File f;

bool logging = false;
bool finished = false;

int rowCount = 0;
unsigned long logStartTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("Booting");

  // -------------------------
  // MPU6050 setup
  // -------------------------
  Wire.begin(21, 22); // SDA, SCL

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);   // Power management register
  Wire.write(0);      // Wake MPU6050

  if (Wire.endTransmission(true) != 0) {
    Serial.println("MPU6050 not found");
    while (true) delay(1000);
  }

  Serial.println("MPU6050 found");

  // -------------------------
  // SD setup
  // -------------------------
  SPI.begin(18, 19, 23, SD_CS_PIN); // SCK, MISO, MOSI, CS

  if (!SD.begin(SD_CS_PIN, SPI, 1000000)) {
    Serial.println("SD mount failed");
    while (true) delay(1000);
  }

  Serial.println("SD mounted");

  Serial.println("Starting in 3 seconds...");
  delay(START_DELAY_MS);

  startLogging();
}

void loop() {
  if (finished) {
    delay(1000);
    return;
  }

  if (logging) {
    if (millis() - logStartTime >= LOG_DURATION_MS) {
      stopLogging();
      return;
    }

    logIMURow();
    delay(SAMPLE_DELAY_MS);
  }
}

void startLogging() {
  String filename = nextFilename();

  f = SD.open(filename, FILE_WRITE);

  if (!f) {
    Serial.println("File open failed");
    while (true) delay(1000);
  }

  f.println("test_name,millis,elapsed_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,accel_mag_g,accel_dynamic_g");
  f.flush();

  rowCount = 0;
  logStartTime = millis();
  logging = true;

  digitalWrite(LED_PIN, HIGH);

  Serial.print("Logging started: ");
  Serial.println(filename);
}

void stopLogging() {
  logging = false;

  f.flush();
  f.close();

  digitalWrite(LED_PIN, LOW);

  Serial.println("Logging finished safely");
  Serial.println("Safe to remove SD card");

  finished = true;
}

String nextFilename() {
  int sessionNumber = 1;
  String filename = "/" + String(TEST_NAME) + "_" + String(sessionNumber) + ".csv";

  while (SD.exists(filename)) {
    sessionNumber++;
    filename = "/" + String(TEST_NAME) + "_" + String(sessionNumber) + ".csv";
  }

  return filename;
}

void logIMURow() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() < 14) {
    Serial.println("MPU read failed");
    return;
  }

  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();

  Wire.read();
  Wire.read(); // skip temperature

  int16_t gx = Wire.read() << 8 | Wire.read();
  int16_t gy = Wire.read() << 8 | Wire.read();
  int16_t gz = Wire.read() << 8 | Wire.read();

  float ax_g = ax / 16384.0;
  float ay_g = ay / 16384.0;
  float az_g = az / 16384.0;

  float gx_dps = gx / 131.0;
  float gy_dps = gy / 131.0;
  float gz_dps = gz / 131.0;

  float accel_mag_g = sqrt(ax_g * ax_g + ay_g * ay_g + az_g * az_g);
  float accel_dynamic_g = fabs(accel_mag_g - 1.0);

  unsigned long now = millis();

  f.print(TEST_NAME);
  f.print(",");
  f.print(now);
  f.print(",");
  f.print(now - logStartTime);
  f.print(",");
  f.print(ax_g, 4);
  f.print(",");
  f.print(ay_g, 4);
  f.print(",");
  f.print(az_g, 4);
  f.print(",");
  f.print(gx_dps, 2);
  f.print(",");
  f.print(gy_dps, 2);
  f.print(",");
  f.print(gz_dps, 2);
  f.print(",");
  f.print(accel_mag_g, 4);
  f.print(",");
  f.println(accel_dynamic_g, 4);

  rowCount++;

  if (rowCount % FLUSH_EVERY_ROWS == 0) {
    f.flush();
  }
}
