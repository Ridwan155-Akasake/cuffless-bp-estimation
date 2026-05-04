---
tags: [dataset/used, dataset/training]
---

# all_features_dataset

Path: `datasets/all_features_dataset.csv` (~2.3 MB, 400 columns × 318 rows).

## What

Final training matrix. Each session contributes one row of:

```
ir_0 … ir_199         (200 resampled IR samples)
red_0 … red_199       (200 resampled RED samples)
userAge, userGender, userHeight, userWeight, userBmi
spo2, heartRate
systolic_BP, diastolic_BP   (targets)
```

## Provenance

- Derived from [[cleaned_data]] by resampling each session's IR / RED arrays to 200 samples and adding BMI / encoded gender.

## Used By

- [[random_forest_tuned_model]] — trained on this matrix.
- [[best_catboost_model]] — same training set.
- All checkpoints in [[Multi-output combined experiments]] and [[Tightened-threshold experiments]].

## Linked

- [[Methodology]]
- [[Results]]
- [[Data Pipeline]]
