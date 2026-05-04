# Cuffless Blood-Pressure Estimation System

> *Limitations of Low-Cost PPG Sensors for Cuffless Blood Pressure Estimation Using IoT and Machine Learning*
>
> Ridwan Sharif and Arif Mahmud — Daffodil International University, Dhaka, Bangladesh

A complete IoT + machine-learning research pipeline for estimating blood pressure from a
fingertip photoplethysmography (PPG) signal — designed, deployed, and tested end-to-end as
an undergraduate capstone. A user presses a button on an ESP32 device, rests their finger on
a MAX30102 optical sensor for 30 seconds, and the system captures their PPG waveforms (IR
and RED), heart rate, and SpO₂. That data flows through a Node.js + MongoDB backend to a
web dashboard, where the user enters basic demographics. A trained ensemble model hosted
on a Flask API returns a predicted systolic and diastolic blood pressure.

**This is a research project with a deliberately rigorous negative result.** The work
demonstrates, with full pipeline tracing, that despite extensive preprocessing, hybrid
feature engineering (morphological + spectral + entropy + nonlinear-dynamics + demographic),
three feature-selection strategies (Mutual Information, RFE, SHAP), and nine regression
candidates, the headline accuracy plateaued at **MAE ≈ 9 mmHg, R² ≈ 0.24**. Clinical-grade
performance requires MAE ≤ 5 mmHg and R² > 0.5. The bottleneck was not the methodology — it
was the **MAX30102 sensor itself**: configured for 100 Hz but delivering only ≈5.6 Hz of
stable signal in practice, with poor waveform morphology that prevented reliable extraction
of fiducial points (systolic peak, dicrotic notch, diastolic decay). The contribution of
this project is therefore credible evidence that **commodity, low-cost PPG sensors are
inappropriate for clinically reliable cuffless BP estimation**, framed by a working
end-to-end IoT system that other researchers can replicate.

---

## System Architecture

```
 ┌──────────────────────────────┐
 │  ESP32 + MAX30102 + LCD      │   firmware: IoT_code/PPG_reading/
 │  Push-button → 30 s capture  │   target: 100 Hz / 3000 samples
 │  observed: ~5.6 Hz stable    │   ← documented sensor limitation
 └──────────────┬───────────────┘
                │ HTTPS POST /api/ppgData
                │ { ir:[..], red:[..], spo2, heartRate }
                ▼
 ┌──────────────────────────────┐
 │  Node.js + Express backend   │   BP-Monitoring-website-server/index.js
 │  MongoDB Atlas               │   collections: rawDataCollection, finalData
 │  Hosted on Vercel            │
 └──────────────┬───────────────┘
                │ GET /api/ppgData/latest
                │ POST /api/mergeData/latest  (adds demographics + ground-truth BP)
                ▼
 ┌──────────────────────────────┐
 │  Web dashboard (HTML/JS)     │   BP-Monitoring-website/public/
 │  Chart.js for IR/RED graphs  │   pages: index, collect, measure, data, about
 │  Hosted on Vercel            │
 └──────────────┬───────────────┘
                │ POST /predict
                │ { ir, red, userAge, userGender, userHeight, userWeight,
                │   userBmi, heartRate, spo2 }
                ▼
 ┌──────────────────────────────┐
 │  Flask ML inference API      │   BP-Monitoring-model-api/app.py
 │  Random Forest (tuned)       │   default deployed regressor
 │  CatBoost (tuned)            │   tied co-best, kept as alternate
 │  Hosted on Hugging Face Space│   returns [[systolic, diastolic]]
 └──────────────────────────────┘
```

---

## Key Technical Details

### Hardware & Firmware (`IoT_code/`)
- **MCU:** ESP32 (Wi-Fi).
- **Sensor:** MAX30102 (combined IR + RED LED PPG + on-chip HR/SpO₂).
- **Display:** 16×2 I²C LCD, default address `0x27`.
- **Trigger:** push-button on GPIO 32 with internal pull-up.
- **Reference BP device:** Omron Automatic Blood Pressure Monitor HEM-7120 (used to capture ground-truth systolic / diastolic readings).
- **Sensor configuration:** `60 mA` LED brightness, multi-LED mode, target 100 Hz sample rate, 411 µs pulse width, 8× sample averaging, 16384 ADC range.
- **Capture window:** 30 000 ms targeting 3000 IR + 3000 RED samples — but the MAX30102's stable operational rate was measured at **≈5.6 Hz**, well below the 50 Hz minimum that the literature cites as required for cuffless BP fiducial-point detection. This shortfall is documented in the paper as the central performance bottleneck.
- **Wi-Fi credentials and backend URL** are loaded from `IoT_code/PPG_reading/secrets.h` (gitignored). Template at [`secrets.h.example`](IoT_code/PPG_reading/secrets.h.example).
- **Transport:** JSON payload over HTTPS POST to the backend.

### Backend (`BP-Monitoring-website-server/`)
- **Stack:** Node.js, Express 4, `mongodb` driver, dotenv, cors.
- **Database:** MongoDB Atlas, database `BP_Measuring`.
  - `rawDataCollection` — raw device payloads (auto-incremented `serialNumber`).
  - `finalData` — raw payload merged with demographics + ground-truth BP, used for training data export.
- **Endpoints:** `POST /api/ppgData`, `GET /api/ppgData/latest`, `GET /api/ppgData`, `PUT /api/ppgData/latest`, `POST /api/mergeData/latest`, `GET /api/finalData`, `GET /api/finalData/latest`, `DELETE /api/ppgData/:id`.
- **Mongo URI** is built entirely from environment variables (`USER`, `PASS`, `MONGO_CLUSTER`); template at `.env.example`.
- **Deployed on:** Vercel — `https://io-t-ppg-bp-monitor-backend.vercel.app`.

### Frontend (`BP-Monitoring-website/`)
- **Stack:** Plain HTML / CSS / vanilla JS, Chart.js for waveform plots, Express server for hosting.
- **Pages:** `index.html` (home), `collect.html` (capture + demographics), `measure.html` (run prediction), `data.html` (view all records), `about.html`.
- **Flow in `public/main.js`:** `fetchSensorData()` → `commitCollectedData()` → `measureBP()` (calls Flask API) → render predicted systolic / diastolic.

### ML Model & Inference API (`BP-Monitoring-model-api/`)
- **Stack:** Python, Flask, flask-cors, joblib, scikit-learn, scipy, pandas, numpy. Containerized via `Dockerfile` (Python 3.9-slim, port 7860).
- **Default deployed model:** [`random_forest_tuned_model.pkl`](BP-Monitoring-model-api/random_forest_tuned_model.pkl) — tuned Random Forest regressor, multi-output (systolic + diastolic). ~750 KB.
- **Co-best alternate:** [`best_catboost_model.pkl`](BP-Monitoring-model-api/best_catboost_model.pkl) — tuned CatBoost variant, statistically tied with Random Forest in the evaluation; kept so the API can be swapped over with a one-line change in `app.py`. ~365 KB.
- **Inference pipeline** (`preprocessing.py`):
  1. JSON → DataFrame; label-encode `userGender`.
  2. Expand `ir` / `red` arrays to per-sample columns.
  3. Resample each signal to a fixed length of **200 samples** (`scipy.signal.resample`).
  4. Extract **12 IR features**: `mean, median, std, min, max, range, skewness, kurtosis, num_peaks, mean_peak_amplitude, dominant_freq (FFT), total_energy (FFT)`.
  5. Concatenate **6 demographic / vital features**: `userAge, userGender, userHeight, userWeight, userBmi, heartRate`.
  6. Final input: an **18-feature vector** → `model.predict(X)` → `[[systolic, diastolic]]`.
- **Deployed on:** Hugging Face Spaces — `https://akasake-bp-monitor-api.hf.space/predict`.
- **Standalone reference repo:** <https://github.com/Ridwan155-Akasake/IoT-PPG-BP-Monitor-FlaskAPI>.

### Training & Feature Engineering (`models/`)

The **training-time** pipeline is more elaborate than the production inference path. Per the paper (Section 3.5):

- **Hybrid feature extraction** spanning four categories:
  - *Morphological:* amplitude, rise time, fall time, pulse width 25 / 75, augmentation index, dicrotic-notch timing.
  - *Heart-rate variability:* mean inter-beat interval (IBI), SDNN, RMSSD, Poincaré indices SD1 / SD2.
  - *Spectral:* spectral centroid, spectral entropy, LF-band energy (0.04–0.15 Hz), HF-band energy (0.15–0.4 Hz).
  - *Entropy:* Shannon entropy, sample entropy.
  - *Nonlinear dynamics:* Hjorth parameters (activity, mobility, complexity), detrended fluctuation analysis (DFA), Petrosian fractal dimension.
- **Three-stage feature selection:** Mutual Information ranking → Recursive Feature Elimination → SHAP-value pruning. The retained set was **~15–20 features**.
- **Model search:** Linear Regression, Random Forest, Random Forest (tuned), CatBoost, CatBoost (tuned), AdaBoost, ANN, BiLSTM, KNN, SVR, XGBoost.
- Driver scripts: `train_bp_models.py`, `multi_target_train.py`, `target_train_tightened.py`, `quick_train_eval.py`. Reusable feature module: `ppg_features.py`.

---

## Folder Structure

```
nibp-monitor/
├── IoT_code/                       ESP32 firmware (Arduino C++)
├── BP-Monitoring-website-server/   Node.js + Express + MongoDB backend (Vercel)
├── BP-Monitoring-website/          HTML/JS dashboard served via Express (Vercel)
├── BP-Monitoring-model-api/        Flask ML inference API (Hugging Face Space)
├── models/                         Training scripts + feature module + result plots
├── datasets/                       Final cleaned + feature-engineered datasets
├── Report and Documentation/       Defense report, conference paper, slides
├── obsidian-vault/                 Linked research-graph notes (open in Obsidian)
└── _archive/                       Superseded experiments retained for reference only
```

---

## Tech Stack

| Layer        | Tools |
|--------------|-------|
| Firmware     | C++ (Arduino), ESP32, MAX30102, LiquidCrystal_I2C, HTTPClient, WiFi |
| Backend      | Node.js, Express, MongoDB (Atlas), `mongodb` driver, dotenv, cors |
| Frontend     | HTML, CSS, vanilla JavaScript, Chart.js, Express (host) |
| ML API       | Python, Flask, flask-cors, joblib, scikit-learn, scipy, pandas, numpy, gunicorn |
| Training     | scikit-learn, CatBoost, LightGBM, AdaBoost, XGBoost, Ridge, mutual-info / RFE / SHAP feature selection |
| Hosting      | Vercel (web), Hugging Face Spaces (ML API), MongoDB Atlas (database), Google Colab (training) |
| Reference    | Omron Automatic Blood Pressure Monitor HEM-7120 (ground-truth BP) |

---

## How to Run

### 1. Firmware (ESP32)
1. Open [`IoT_code/PPG_reading/PPG_reading.ino`](IoT_code/PPG_reading/PPG_reading.ino) in the Arduino IDE.
2. Install libraries: `LiquidCrystal_I2C`, `DFRobot_MAX30102`, `WiFi`, `HTTPClient`.
3. `cp IoT_code/PPG_reading/secrets.h.example IoT_code/PPG_reading/secrets.h` and fill in your Wi-Fi SSID/password.
4. Flash to an ESP32 board, wire the MAX30102 over I²C, and connect a 16×2 LCD and a push-button on GPIO 32.

### 2. Backend (`BP-Monitoring-website-server/`)
```bash
cd BP-Monitoring-website-server
npm install
cp .env.example .env       # then edit with real Mongo creds
node index.js
```

### 3. Frontend (`BP-Monitoring-website/`)
```bash
cd BP-Monitoring-website
npm install
cp .env.example .env       # then edit with real Mongo creds
node index.js              # serves the static dashboard
```
Open `http://localhost:5000`.

### 4. Flask ML API (`BP-Monitoring-model-api/`)
```bash
cd BP-Monitoring-model-api
pip install -r requirements.txt
python app.py     # Flask serves on 0.0.0.0:7860
# or via Docker:
docker build -t nibp-api . && docker run -p 7860:7860 nibp-api
```

---

## Research & Results

### Problem
Cuff-based blood-pressure monitors are intermittent, bulky, and unsuitable for continuous
or at-home use. Cuffless BP estimation from PPG is well-explored on **research-grade**
datasets (e.g. MIMIC) and clinical sensors, but the published literature rarely studies
what happens when one attempts the same pipeline with a **commodity sensor** (the
MAX30102) of the kind embedded in cheap consumer wearables. This project asks that
question explicitly: can a low-cost optical sensor combined with demographic features and
classical / ensemble ML produce clinically meaningful BP estimates?

### Methodology
1. **Data acquisition.** Custom IoT device (ESP32 + MAX30102 + 16×2 LCD + push-button); web interface for real-time PPG monitoring and demographics entry; Omron HEM-7120 sphygmomanometer for ground-truth BP. **536 sessions** were captured from volunteers across university campus and residential settings.
2. **Preprocessing.** Exception handling (e.g. `-999` placeholder removal), nominal encoding (gender), and digital upscaling experiments. Hardware-side mitigations included swapping multiple physical MAX30102 units and varying the firmware (different libraries, different clock rates) — none recovered the missing temporal resolution.
3. **Feature engineering.** Hybrid morphological + HRV + spectral + entropy + nonlinear-dynamics features extracted with `ppg_features.py`, concatenated with `userAge, userGender, userHeight, userWeight, userBmi`.
4. **Feature selection.** Three-stage filter: Mutual Information → Recursive Feature Elimination → SHAP values. Retained ~15–20 features.
5. **Model search.** Nine regressors evaluated: Linear Regression, Random Forest (tuned), CatBoost (tuned), AdaBoost, XGBoost, ANN, BiLSTM, KNN, SVR.

### Headline Results (paper Table 2)

| Model                  | MAE   | MSE    | RMSE  | R²    | MAPE (%) |
|------------------------|-------|--------|-------|-------|----------|
| **Random Forest (Tuned)** ⭐ | **9.08** | **165.7** | **12.87** | **0.241** | **8.83** |
| **CatBoost (Tuned)**   | 9.20  | 167.6  | 12.94 | 0.241 | 9.02 |
| AdaBoost               | 9.84  | 170.2  | 13.04 | 0.230 | 9.87 |
| ANN                    | 9.45  | 168.8  | 12.99 | 0.213 | 9.19 |
| Linear Regression      | 9.40  | 175.7  | 13.25 | 0.190 | 9.17 |
| KNN                    | 9.73  | 181.1  | 13.45 | 0.175 | 9.52 |
| XGBoost                | 9.78  | 185.2  | 13.61 | 0.146 | 9.61 |
| SVR                    | 9.82  | 194.1  | 13.93 | 0.137 | 9.49 |
| BiLSTM                 | 10.21 | 198.6  | 14.09 | 0.107 | 10.03 |

Random Forest and CatBoost are statistically tied at the top, which is why both checkpoints
ship with this repo.

### Negative Result and Its Engineering Significance

> Clinical practice requires **MAE ≤ 5 mmHg and R² > 0.5**. The pipeline plateaus at
> **MAE ≈ 9 mmHg and R² ≈ 0.24** regardless of which model, feature set, or selection
> strategy is used.

The paper traces this gap to four diagnosable factors:

1. **Sampling-rate ceiling.** The MAX30102 was configured for 100 Hz but stabilised at **≈5.6 Hz** under continuous use, far below the literature-recommended 50 Hz minimum. Without that temporal resolution, the systolic peak / dicrotic notch / diastolic decay cannot be resolved cleanly; downstream morphological and entropy features inherit the noise.
2. **Sensor unit-to-unit variation.** Multiple MAX30102 modules were swapped during data collection, with similar behaviour — the limit is not a defective unit, it is the sensor class.
3. **Dataset bias.** Of 536 records, **~70 % male** and **~48 % aged 20–25**, limiting generalisation across age and sex.
4. **Sample size.** n=536 is too small for deep models (BiLSTM, ANN) to recover temporal structure beyond what classical RF / CatBoost capture, contributing to under- / over-fitting on those candidates.

The contribution is therefore not a deployable medical device — it is a **fully traced
end-to-end pipeline** showing that the limit lies in commodity hardware. Future work
flagged in the paper: medical-grade PPG sensors with adequate sampling rate, larger and
more demographically balanced datasets, sensor-fusion strategies (PPG + ECG / IMU), and
calibration-free formulations.

For the full literature review, methodology write-up, gap analysis, and conference paper,
see [`Report and Documentation/`](Report%20and%20Documentation/) — particularly
[`10330_Camera_Ready.pdf`](Report%20and%20Documentation/10330_Camera_Ready.pdf).

---

## Repository Status

- **Phase:** completed academic capstone; conference paper produced. Preserved as a portfolio repository.
- **Curation:** experimental datasets and superseded model checkpoints have been moved to [`_archive/`](_archive/) and are not part of the active codebase. Real-subject medical data is gitignored. See [`obsidian-vault/`](obsidian-vault/) for the interactive research graph.

## Authors

- **Ridwan Sharif** — primary author and implementer.
- **Arif Mahmud** — supervisor / co-author.

Daffodil International University, Dhaka-1216, Bangladesh.
Final Year Design Project / undergraduate capstone, 2025.
