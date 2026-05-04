---
tags: [model/final, model/deployed]
---

# random_forest_tuned_model

Path: `BP-Monitoring-model-api/random_forest_tuned_model.pkl` (~750 KB).

## What

Multi-output Random Forest regressor predicting `[systolic_BP, diastolic_BP]` simultaneously
from an 18-feature vector. The **deployed production model**.

## Trained On

- [[all_features_dataset]] (with the 18-feature reduction described in [[Methodology]]).

## Performance (paper Table 2)

| MAE | MSE | RMSE | R² | MAPE |
|---|---|---|---|---|
| 9.08 | 165.7 | 12.87 | 0.241 | 8.83 % |

Top of the nine-regressor evaluation, **tied** with [[best_catboost_model]] (MAE 9.20, same R² 0.241).
Full table in [[Results]].

## Loaded By

- [[Flask ML API]] — `joblib.load('random_forest_tuned_model.pkl')` in `app.py`.

## Supersedes

- [[Single-target RF baselines]] — earlier "two separate models per output" approach.
- [[Multi-output combined experiments]] — multi-output tries with other algorithms.
- [[Tightened-threshold experiments]] — stricter feature filters; no improvement.

## Linked

- [[Results]]
- [[Methodology]]
- [[Data Pipeline]]
- [[PROJECT OVERVIEW]]
