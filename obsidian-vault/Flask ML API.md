---
tags: [component, ml, api]
---

# Flask ML API

Path: `BP-Monitoring-model-api/`

## Role

Serve the trained regression model. Single endpoint: `POST /predict`.

## Stack

- Python 3.9, Flask, flask-cors, joblib, scikit-learn, scipy, pandas, numpy.
- Containerized via `Dockerfile` (port 7860). Procfile uses `gunicorn`.
- Hosted on Hugging Face Spaces — `https://akasake-bp-monitor-api.hf.space/predict`.
- Standalone reference repo: <https://github.com/Ridwan155-Akasake/IoT-PPG-BP-Monitor-FlaskAPI>.

## Loaded Model

- [[random_forest_tuned_model]] (production).
- [[best_catboost_model]] (backup).

## Inference Pipeline (`preprocessing.py`)

1. Parse JSON → DataFrame.
2. Encode `userGender`.
3. Expand `ir` / `red` arrays to columns.
4. `scipy.signal.resample` each signal → 200 samples.
5. Extract 12 IR features (mean, median, std, min, max, range, skewness, kurtosis, num_peaks, mean_peak_amplitude, dominant_freq, total_energy).
6. Concatenate with 6 demographics → **18-feature vector**.
7. `model.predict(X)` → `[[systolic, diastolic]]`.

## Talks To

- Called by [[Frontend Dashboard]]'s `measureBP()`.

## Linked

- [[Methodology]]
- [[Data Pipeline]]
- [[PROJECT OVERVIEW]]
