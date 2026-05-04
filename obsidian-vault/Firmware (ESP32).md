---
tags: [component, firmware, hardware]
---

# Firmware (ESP32)

Path: `IoT_code/PPG_reading/PPG_reading.ino`

## Role

Capture 30 seconds of dual-channel PPG and ship it to the cloud.

## Hardware

- ESP32 dev board (Wi-Fi).
- MAX30102 (IR + RED PPG, on-chip HR/SpO₂).
- 16×2 I²C LCD at `0x27`.
- Push-button on GPIO 32 (active-low, pull-up).

## Configuration

- `SAMPLE_RATE` = 100 Hz, `SESSION_DURATION` = 30 000 ms → `MAX_SAMPLES` = 3000 per channel.
- LED brightness 60 mA, pulse width 411 µs, ADC range 16384, sample averaging 8×.

## Flow

1. Connect to Wi-Fi.
2. Wait for GPIO 32 button press.
3. Capture IR + RED at 10 ms intervals into 3000-element arrays.
4. Compute HR + SpO₂ on-device via the MAX30102 driver.
5. Build JSON payload `{ ir, red, spo2, heartRate }`.
6. HTTPS POST → [[Backend API]] (`/api/ppgData`).

## Feeds Into

- [[Backend API]] → [[MongoDB]] (`rawDataCollection`)
- Eventually feeds [[BP_Measuring finalData]] after the user adds demographics in [[Frontend Dashboard]].

## Notes

- Wi-Fi credentials and the backend URL are hard-coded in the sketch (lines 38–39 and 194). For real-world distribution they should move to Wi-Fi provisioning + a configurable endpoint.
- See [[Data Pipeline]] for the full end-to-end view.
