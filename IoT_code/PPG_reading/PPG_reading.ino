#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DFRobot_MAX30102.h>
#include <WiFi.h>        // Include WiFi library to connect to the internet
#include <HTTPClient.h>  // Include HTTPClient library for HTTP requests
#include "secrets.h"     // WIFI_SSID, WIFI_PASSWORD, BACKEND_URL — gitignored

#define BUTTON_PIN 32
#define SESSION_DURATION 30000                            // 30 seconds (ms)
// #define SESSION_DURATION 15000                            // 15 seconds (ms)
#define SAMPLE_RATE 100                                   // Hz
#define SAMPLE_INTERVAL (1000 / SAMPLE_RATE)              // 10 ms
#define MAX_SAMPLES (SESSION_DURATION / SAMPLE_INTERVAL)  // 3000 samples
#define SPO2_BUFFER_SIZE 100                              // For SpO2/HR calculation

// LCD (16x2, adjust address from I2C scanner)
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Try 0x3F if 0x27 fails
DFRobot_MAX30102 particleSensor;

int32_t irBuffer[MAX_SAMPLES];
int32_t redBuffer[MAX_SAMPLES];
int sampleCount = 0;
bool sessionRunning = false;
unsigned long sessionStartTime = 0;
unsigned long lastSampleTime = 0;
int lastButtonState = HIGH;

// SpO2 and HR
int32_t SPO2 = 0;
int8_t SPO2Valid = 0;
int32_t heartRate = 0;
int8_t heartRateValid = 0;

// Wi-Fi credentials are loaded from secrets.h (gitignored). See secrets.h.example.
const char* ssid     = WIFI_SSID;
const char* password = WIFI_PASSWORD;



void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Wire.begin();
  Wire.setClock(400000);  // 400 kHz I2C

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Init LCD
  lcd.begin(16, 2);
  lcd.backlight();
  lcd.print("PPG BP Monitor");
  delay(2000);
  lcd.clear();
  lcd.print("Press to Start");

  // Init MAX30102
  while (!particleSensor.begin()) {
    Serial.println("MAX30102 not found");
    lcd.clear();
    lcd.print("Sensor Error");
    delay(1000);
    lcd.clear();
    lcd.print("Press to Start");
  }
  particleSensor.sensorConfiguration(
    60,              // ledBrightness (60 mA)
    SAMPLEAVG_8,     // sampleAverage
    MODE_MULTILED,   // ledMode
    SAMPLERATE_100,  // sampleRate (~100 Hz with averaging)
    PULSEWIDTH_411,  // pulseWidth
    ADCRANGE_16384   // adcRange
  );
}

void loop() {
  // Button to start session
  int buttonState = digitalRead(BUTTON_PIN);
  if (buttonState != lastButtonState && buttonState == LOW && !sessionRunning) {
    sessionRunning = true;
    sessionStartTime = millis();
    lastSampleTime = millis();
    sampleCount = 0;

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Put Finger on");
    lcd.setCursor(0, 1);
    lcd.print("the sensor");
    delay(3000);

    lcd.clear();
    lcd.print("Session: Run");
    Serial.println("Session Start");
    delay(200);  // Debounce
  }
  lastButtonState = buttonState;

  // Collect PPG
  if (sessionRunning && sampleCount < MAX_SAMPLES) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastSampleTime >= SAMPLE_INTERVAL) {
      lastSampleTime = currentMillis;

      // Read and store
      irBuffer[sampleCount] = particleSensor.getIR();
      redBuffer[sampleCount] = particleSensor.getRed();

      // Log data to serial
      Serial.print("IR: ");
      Serial.println(irBuffer[sampleCount]);
      Serial.print("Red: ");
      Serial.println(redBuffer[sampleCount]);

      sampleCount++;

      lcd.setCursor(0, 1);
      lcd.print("Samples: ");
      lcd.print(sampleCount);
      lcd.print("   ");
    }
  }

  // End session
  if (sessionRunning && (millis() - sessionStartTime >= SESSION_DURATION || sampleCount >= MAX_SAMPLES)) {
    sessionRunning = false;

    // Calculate SpO2 and HR
    particleSensor.heartrateAndOxygenSaturation(&SPO2, &SPO2Valid, &heartRate, &heartRateValid);

    // LCD Results
    lcd.clear();
    lcd.print(" Done");
    lcd.setCursor(0, 1);
    if (heartRateValid) {
      lcd.print("HR:");
      lcd.print(heartRate);
      lcd.print(" bpm");
    } else {
      lcd.print("HR: Invalid");
    }
    delay(3000);
    lcd.clear();
    lcd.print("SpO2: ");
    lcd.print(SPO2Valid ? SPO2 : -1);
    lcd.print(SPO2Valid ? "%" : "Invalid");
    delay(3000);
    lcd.clear();
    lcd.print("Press to Start");

    // Log results
    Serial.println("--- Session End ---");
    Serial.print("Heart Rate: ");
    Serial.print(heartRateValid ? heartRate : -1);
    Serial.println(heartRateValid ? " bpm" : " (Invalid)");
    Serial.print("SpO2: ");
    Serial.print(SPO2Valid ? SPO2 : -1);
    Serial.println(SPO2Valid ? "%" : " (Invalid)");
    Serial.print("Samples Collected: ");
    Serial.println(sampleCount);

    // Create JSON payload to send
    String jsonPayload = "{\"ir\": [";
    for (int i = 0; i < sampleCount; i++) {
      jsonPayload += String(irBuffer[i]);
      if (i < sampleCount - 1) jsonPayload += ", ";
    }
    jsonPayload += "], \"red\": [";
    for (int i = 0; i < sampleCount; i++) {
      jsonPayload += String(redBuffer[i]);
      if (i < sampleCount - 1) jsonPayload += ", ";
    }
    jsonPayload += "], \"spo2\": " + String(SPO2) + ", \"heartRate\": " + String(heartRate) + "}";


    // String jsonPayload = "{\"heartRate\": " + String(heartRate) + ", \"spo2\": " + String(SPO2) + "}";

    // Post data to backend
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(BACKEND_URL);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(jsonPayload);  // Send POST request

      if (httpResponseCode > 0) {
      
        Serial.println("Data sent successfully.");
        Serial.println("HTTP Response Code: " + String(httpResponseCode));
      } else {
        Serial.println("Error sending data. HTTP Response Code: " + String(httpResponseCode));
      }
      http.end();  // Free resources
    } else {
      Serial.println("Error: WiFi not connected");
    }
  }
}
