---
tags: [research, results, metrics]
---

# Results

From the conference paper (`Report and Documentation/10330_Camera_Ready.pdf`, Table 2).

| Model                       | MAE   | MSE    | RMSE  | R²    | MAPE (%) |
|-----------------------------|-------|--------|-------|-------|----------|
| **Random Forest (Tuned)** ⭐ | **9.08** | **165.7** | **12.87** | **0.241** | **8.83** |
| **CatBoost (Tuned)**        | 9.20  | 167.6  | 12.94 | 0.241 | 9.02 |
| AdaBoost                    | 9.84  | 170.2  | 13.04 | 0.230 | 9.87 |
| ANN                         | 9.45  | 168.8  | 12.99 | 0.213 | 9.19 |
| Linear Regression           | 9.40  | 175.7  | 13.25 | 0.190 | 9.17 |
| KNN                         | 9.73  | 181.1  | 13.45 | 0.175 | 9.52 |
| XGBoost                     | 9.78  | 185.2  | 13.61 | 0.146 | 9.61 |
| SVR                         | 9.82  | 194.1  | 13.93 | 0.137 | 9.49 |
| BiLSTM                      | 10.21 | 198.6  | 14.09 | 0.107 | 10.03 |

Evaluation set: 536-record in-house dataset (post-cleaning feature matrix in
[[all_features_dataset]]).

## Headline Findings

- **Random Forest (Tuned)** and **CatBoost (Tuned)** are statistically tied at the top — that is why **both** checkpoints ship with the repo (see [[random_forest_tuned_model]], [[best_catboost_model]]).
- Deep models (ANN, BiLSTM) underperform classical ensembles on this dataset — likely a sample-size effect.
- **No model crosses the clinical bar.** Clinical practice needs **MAE ≤ 5 mmHg and R² > 0.5**; the best achievable is MAE ≈ 9.08 mmHg and R² ≈ 0.24.

## Why The Plateau (Four Diagnosable Factors)

The paper attributes the gap to hardware and dataset constraints, not pipeline shortcomings:

1. **Sampling-rate ceiling.** MAX30102 stabilised at **≈5.6 Hz** versus the 50 Hz literature minimum. Systolic peaks, dicrotic notches, and diastolic decay cannot be resolved cleanly at this rate, so morphological and entropy features inherit the noise.
2. **Sensor unit-to-unit consistency.** Swapping multiple physical MAX30102 modules produced similar behaviour — the limit is the sensor class, not a defective unit.
3. **Dataset bias.** ~70 % male, ~48 % aged 20–25 — generalisation to underrepresented groups is unreliable.
4. **Sample size.** n=536 is too small for deep architectures (BiLSTM, ANN) to recover temporal structure that classical RF / CatBoost don't already capture, leading to over- / under-fitting on those candidates.

## Engineering Significance

The contribution of this work is **not** a deployable medical device — it is a **fully
traced end-to-end pipeline** producing credible evidence that commodity, low-cost PPG sensors
are inappropriate for clinically reliable cuffless BP estimation. The paper recommends future
research focus on:

- Medical-grade PPG sensors with adequate sampling rate and peak detection.
- Larger, more demographically balanced datasets.
- Sensor-fusion strategies (PPG + ECG / IMU) for noise / motion-artifact resilience.
- Calibration-free formulations to reduce dependence on cuff-reference measurements.

## Deployed Artifact

- Default: [[random_forest_tuned_model]] — loaded by [[Flask ML API]].
- Alternate: [[best_catboost_model]] — swap by editing one line of `app.py`.

## Linked

- [[Research Problem]]
- [[Methodology]]
- [[PROJECT OVERVIEW]]
