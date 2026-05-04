---
tags: [model/final, model/alternate]
---

# best_catboost_model

Path: `BP-Monitoring-model-api/best_catboost_model.pkl` (~365 KB).

## What

Tuned CatBoost regressor that is **statistically tied** with the Random Forest at the top of
the model evaluation: MAE 9.20 vs 9.08, identical R² of 0.241 (paper Table 2). Kept alongside
the deployed Random Forest precisely because the paper concludes both are co-best.

## Trained On

- [[all_features_dataset]].

## Why Random Forest Is The Default

- Slightly lower MAE (9.08 vs 9.20) and lower MAPE (8.83 % vs 9.02 %).
- Within standard error these differences are not significant — choice between the two is essentially a tiebreaker.
- The Flask app loads [[random_forest_tuned_model]] by default; switching to this CatBoost
  artifact requires a one-line change in `app.py`.

## Linked

- [[random_forest_tuned_model]]
- [[Results]]
- [[Methodology]]
