# IoT_code — ESP32 Firmware

The hardware-side of the NIBP monitor. An ESP32 reads 30 seconds of dual-channel PPG
(IR + RED) from a MAX30102 sensor, computes heart rate and SpO₂ on-device, and POSTs the
result over Wi-Fi to the cloud backend.

## Files

| File | Purpose |
|---|---|
| [`PPG_reading/PPG_reading.ino`](PPG_reading/PPG_reading.ino) | Main Arduino sketch — Wi-Fi setup, button-triggered capture loop, MAX30102 driver calls, JSON serialization, HTTPS POST to backend. |

## Hardware

| Component | Notes |
|---|---|
| ESP32 dev board | Wi-Fi MCU; flashes via Arduino IDE |
| MAX30102 | I²C optical sensor (IR + RED + on-chip HR/SpO₂) |
| 16×2 I²C LCD | Status display, default address `0x27` (try `0x3F` if it fails) |
| Push-button | GPIO 32, active-low with internal pull-up |

## Wi-Fi Credentials

Wi-Fi SSID, password, and the backend ingest URL live in `PPG_reading/secrets.h`. That file
is **gitignored** so secrets never reach the repo.

To set it up after cloning:

```bash
cp IoT_code/PPG_reading/secrets.h.example IoT_code/PPG_reading/secrets.h
# edit secrets.h with your real Wi-Fi SSID + password
```

`PPG_reading.ino` reads `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_URL` from this header.

## Required Arduino Libraries

- `Wire.h` (built-in)
- `LiquidCrystal_I2C`
- `DFRobot_MAX30102`
- `WiFi.h` (ESP32 core)
- `HTTPClient.h` (ESP32 core)

## Capture Configuration

| Constant | Value | Meaning |
|---|---|---|
| `SESSION_DURATION` | 30 000 ms | Capture window |
| `SAMPLE_RATE` | 100 Hz | PPG sampling rate |
| `SAMPLE_INTERVAL` | 10 ms | `1000 / SAMPLE_RATE` |
| `MAX_SAMPLES` | 3000 | Per-channel array length |
| `SPO2_BUFFER_SIZE` | 100 | Used by `heartrateAndOxygenSaturation` |
| LED brightness | 60 mA | Sensor configuration |
| Pulse width | 411 µs | Sensor configuration |
| ADC range | 16384 | Sensor configuration |
| Sample averaging | 8× | Sensor configuration |

## Session Flow

1. On boot, the ESP32 connects to Wi-Fi using the hard-coded SSID/password (line 38–39 of `PPG_reading.ino`) and shows `Press to Start` on the LCD.
2. The user presses the button (GPIO 32). The LCD prompts to place a finger on the sensor.
3. For 30 s, IR and RED samples are read every 10 ms into `irBuffer[3000]` and `redBuffer[3000]`. The current sample count is shown on the LCD.
4. After the window ends, `particleSensor.heartrateAndOxygenSaturation()` computes HR and SpO₂.
5. The buffers are serialized into a single JSON payload:
   ```json
   {
     "ir":   [int, int, ...],   // 3000 values
     "red":  [int, int, ...],   // 3000 values
     "spo2": <int>,
     "heartRate": <int>
   }
   ```
6. The payload is sent via HTTPS POST to `https://io-t-ppg-bp-monitor-backend.vercel.app/api/ppgData`. The LCD shows the resulting HR / SpO₂.

## Connection to the Rest of the System

```
ESP32 ──POST /api/ppgData──▶ BP-Monitoring-website-server (Express + MongoDB)
                                      │
                                      ▼
                               rawDataCollection (Mongo)
                                      │
                                ─ then merged with demographics ─
                                      ▼
                                finalData (Mongo) → used for ML training & inference
```

## Notes & Caveats

- Wi-Fi credentials and the backend URL live in the gitignored `secrets.h` (template at `secrets.h.example`); they are not embedded in source.
- Switching backends requires editing `secrets.h` and re-flashing.
- HR and SpO₂ are computed by the on-device MAX30102 driver and are passed through; the ML model treats them as features rather than re-deriving them.
