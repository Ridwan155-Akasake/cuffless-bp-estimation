---
tags: [research, methodology]
---

# Methodology

Per the conference paper (`Report and Documentation/10330_Camera_Ready.pdf`).

## 1. Data Acquisition

- Hardware: ESP32 + MAX30102 + 16×2 LCD + push-button — see [[Firmware (ESP32)]].
- Capture target: 30 s × 100 Hz = 3000 IR + 3000 RED samples.
- **Observed sampling rate: ≈5.6 Hz** — the MAX30102's stable operational rate, far below the literature-recommended 50 Hz minimum. Multiple physical units were swapped with similar behaviour. This is the central performance bottleneck (see [[Results]]).
- HR and SpO₂ computed on-device.
- Ground-truth BP captured with **Omron HEM-7120** sphygmomanometer immediately after each session.
- Demographics (age, gender, height, weight, BMI) entered by the subject in the [[Frontend Dashboard]].
- **Dataset: 536 records** total, captured from volunteers in indoor environments (university libraries, dormitories, residential spaces).

## 2. Storage

- Raw payload posted to [[Backend API]] → [[MongoDB]] (`rawDataCollection`).
- Demographics + ground-truth BP merged into `finalData`.
- Exported to CSV / JSON for offline training — see [[BP_Measuring finalData]].

## 3. Preprocessing

- Exception handling (drop `-999` placeholders, NaN rows).
- Nominal encoding (gender).
- Hardware mitigations: swap MAX30102 units, vary firmware libraries — could not lift the sampling rate.
- Digital upscaling explored at interpolation factors of 10 (→50 Hz) and 20 (→100 Hz). **Rejected** because synthetic interpolated samples do not recover real morphology — the resulting features look denser but are noisier.
- Aggressive feature engineering as the final countermeasure.

## 4. Feature Engineering

Hybrid extraction over five categories:

1. **Morphological:** amplitude, rise time, fall time, pulse widths at 25 / 75 % amplitude, augmentation index, dicrotic-notch timing.
2. **Heart-rate variability:** mean inter-beat interval (IBI), SDNN, RMSSD, Poincaré indices SD1 / SD2.
3. **Spectral:** spectral centroid, spectral entropy, LF energy (0.04–0.15 Hz), HF energy (0.15–0.4 Hz).
4. **Entropy:** Shannon entropy, sample entropy.
5. **Nonlinear dynamics:** Hjorth parameters (activity, mobility, complexity), detrended fluctuation analysis (DFA), Petrosian fractal dimension.

Plus demographic features: `userAge, userGender, userHeight, userWeight, userBmi`.

> **Channel ablation finding:** adding RED-derived features alongside IR was **redundant** and slightly **degraded** results. The deployed pipeline is **IR-only + demographics**. Ablation experiments live in [[Feature ablation experiments]].

The full feature matrix used for training is [[all_features_dataset]].

## 5. Feature Selection (three-stage filter)

1. **Mutual Information** — rank features by dependency with BP target.
2. **Recursive Feature Elimination (RFE)** — wrapper-based pruning.
3. **SHAP values** — pruning by per-feature contribution to model predictions.

Retained set: **~15–20 features**.

## 6. Model Search

Nine regressors compared: Linear Regression, Random Forest (tuned), CatBoost (tuned),
AdaBoost, ANN, BiLSTM, KNN, SVR, XGBoost. CatBoost / LightGBM / Ridge / AdaBoost ensembles
were also explored with multi-output and tightened-threshold variants — those checkpoints
are in [[Multi-output combined experiments]] and [[Tightened-threshold experiments]].

External Kaggle PPG-BP data was tried as augmentation — see [[Kaggle PPG-BP]] and
[[Kaggle-track experiments]] — but did not transfer cleanly to this project's sensor
characteristics and was dropped.

## 7. Selected Models

Tied at the top of the evaluation:

- [[random_forest_tuned_model]] — default deployed.
- [[best_catboost_model]] — kept as alternate.

See [[Results]] for the full table.

## 8. Deployment

Model served behind a Flask API ([[Flask ML API]]) hosted on Hugging Face Spaces; called from
[[Frontend Dashboard]]'s `measureBP()`. Full sequence captured in [[Data Pipeline]].
