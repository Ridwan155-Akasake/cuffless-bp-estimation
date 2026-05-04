# BP-Monitoring-model-api — Flask ML Inference API

The brains of the system. A Flask service that loads the trained Random Forest model,
preprocesses an incoming PPG + demographics JSON payload into an 18-feature vector, and
returns predicted systolic / diastolic blood pressure.

## Files

| File | Purpose |
|---|---|
| [`app.py`](app.py) | Flask app — single `POST /predict` route, loads `random_forest_tuned_model.pkl`, calls `preprocess_json_data`, returns `{ "prediction": [[systolic, diastolic]] }`. |
| [`preprocessing.py`](preprocessing.py) | All inference-time preprocessing: gender encoding, IR/RED array expansion, scipy resampling to 200 samples, statistical + FFT feature extraction, demographic concatenation. Also exports the `EnsembleModel` helper class kept for compatibility with older serialized ensembles. |
| [`random_forest_tuned_model.pkl`](random_forest_tuned_model.pkl) | **Production model** — tuned Random Forest regressor, multi-output (systolic + diastolic). ~750 KB. |
| [`best_catboost_model.pkl`](best_catboost_model.pkl) | Backup model — best CatBoost variant, kept for comparison. ~365 KB. |
| [`requirements.txt`](requirements.txt) | Flask, flask-cors, joblib, scikit-learn, scipy, pandas, numpy, gunicorn. |
| [`Dockerfile`](Dockerfile) | Python 3.9-slim, exposes port 7860, runs `python app.py`. |
| [`Procfile`](Procfile) | `web: gunicorn app:app` (for Heroku-style hosts). |

## Endpoint

### `POST /predict`

**Request body**
```json
{
  "ir":         [float, float, ...],
  "red":        [float, float, ...],
  "userAge":    24,
  "userGender": "male",
  "userHeight": 175.26,
  "userWeight": 70,
  "heartRate":  72,
  "spo2":       97,
  "userBmi":    22.81
}
```

**Response body**
```json
{ "prediction": [[118.4, 77.6]] }
```
(Where `prediction[0]` is `[systolic_BP, diastolic_BP]` in mmHg.)

## Inference Pipeline (`preprocessing.py`)

1. **Parse** the JSON body to a single-row DataFrame.
2. **Encode** `userGender` with `LabelEncoder` (lossy at inference because no fixed vocabulary — see "Limitations" below).
3. **Expand** the `ir` and `red` arrays to per-sample columns (`ir_0…ir_N`, `red_0…red_N`).
4. **Resample** each signal to a fixed length of **200 samples** using `scipy.signal.resample`. This decouples the API from the ESP32's specific 3000-sample / 100-Hz capture format.
5. **Extract 12 features** from the IR signal: `mean, median, std, min, max, range, skewness, kurtosis, num_peaks, mean_peak_amplitude, dominant_freq (FFT), total_energy (FFT)`.
6. **Concatenate 6 demographic / vital features**: `userAge, userGender, userHeight, userWeight, userBmi, heartRate`.
7. **Predict** — pass the 18-feature array to `model.predict(X)`.

> RED-channel features are computed but not used by the deployed model. Earlier experiments
> showed that adding RED features alongside IR was redundant and slightly degraded results,
> so the production model is IR-only + demographics.

## Run Locally

```bash
pip install -r requirements.txt
python app.py
# Flask listens on 0.0.0.0:7860
```

Or via Docker:
```bash
docker build -t nibp-api .
docker run -p 7860:7860 nibp-api
```

Smoke test:
```bash
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"ir":[1,2,3,...],"red":[1,2,3,...],"userAge":25,"userGender":"male","userHeight":175,"userWeight":70,"heartRate":72,"spo2":97,"userBmi":22.8}'
```

## Deployment

Hosted on Hugging Face Spaces at **`https://akasake-bp-monitor-api.hf.space/predict`**. The
web dashboard's `measureBP()` function calls this URL directly.

A standalone repo of just this service is also published at:
<https://github.com/Ridwan155-Akasake/IoT-PPG-BP-Monitor-FlaskAPI>.

## Limitations

- `LabelEncoder` is fitted *per request* on a single value, so the encoded gender is just `0`. This is a known artifact of the inference code path; the model was trained with a consistent encoding so single-row inference still produces the expected category in practice for the two-class case.
- `random_forest_tuned_model.pkl` is the deployed artifact; the alternate `best_catboost_model.pkl` is loaded only if `app.py` is modified to point at it.
- The `EnsembleModel` class in `preprocessing.py` exists to allow joblib to deserialize older ensemble checkpoints — it is not used by the current deployed model.
