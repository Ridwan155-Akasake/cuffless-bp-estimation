---
tags: [pipeline, architecture]
---

# Data Pipeline

Full end-to-end sequence from finger on sensor to predicted BP on screen.

```
┌──────────────────────┐
│ [[Firmware (ESP32)]] │
│  MAX30102 capture    │
│  3000 IR + 3000 RED  │
│  HR, SpO2            │
└──────────┬───────────┘
           │ HTTPS POST /api/ppgData
           │ JSON: { ir, red, spo2, heartRate }
           ▼
┌──────────────────────┐
│ [[Backend API]]      │
│  Express + Vercel    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ [[MongoDB]]          │
│  rawDataCollection   │
└──────────┬───────────┘
           │ user opens collect.html
           │ GET /api/ppgData/latest
           ▼
┌──────────────────────┐
│ [[Frontend Dashboard]] │
│  Chart.js IR / RED   │
│  Form: age, gender,  │
│  height, weight, BP  │
└──────────┬───────────┘
           │ POST /api/mergeData/latest
           ▼
┌──────────────────────┐
│ [[MongoDB]]          │
│  finalData           │  ◀── exported as [[BP_Measuring finalData]]
└──────────┬───────────┘
           │ offline export + flatten
           ▼
       [[cleaned_data]]
           │ resample IR/RED → 200 samples + features
           ▼
   [[all_features_dataset]]
           │ train_bp_models.py
           ▼
 [[random_forest_tuned_model]]
           │ joblib.load in app.py
           ▼
┌──────────────────────┐
│ [[Flask ML API]]     │
│  POST /predict       │
│  return [[sys, dia]] │
└──────────┬───────────┘
           │
           ▼
   Frontend shows BP
```

## Linked

- [[Firmware (ESP32)]]
- [[Backend API]]
- [[MongoDB]]
- [[Frontend Dashboard]]
- [[Flask ML API]]
- [[Methodology]]
- [[PROJECT OVERVIEW]]
