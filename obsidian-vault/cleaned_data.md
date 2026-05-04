---
tags: [dataset/used, dataset/intermediate]
---

# cleaned_data

Path: `datasets/cleaned_data.csv`.

## What

Tabular flattening of [[BP_Measuring finalData]]. Each row is one session; the `ir` and `red`
arrays are stored as JSON-array strings inside their columns. Columns:

```
serialNumber, ir, red, spo2, heartRate,
userAge, userGender, userHeight, userWeight,
systolic_BP, diastolic_BP
```

(BMI is added downstream during feature engineering.)

## Used By

- Resampling + feature extraction → [[all_features_dataset]].

## Linked

- [[Methodology]]
- [[BP_Measuring finalData]]
- [[Data Pipeline]]
