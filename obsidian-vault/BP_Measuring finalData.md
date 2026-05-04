---
tags: [dataset/used, dataset/source]
---

# BP_Measuring finalData

Path: `datasets/BP_Measuring.finalData.json` (~1.1 MB).

## What

Direct export of the [[MongoDB]] `finalData` collection. The **source of truth** for every
labelled session captured during the project. Each document contains the full IR + RED array,
on-device HR / SpO₂, demographics, and ground-truth systolic / diastolic BP.

## Provenance

- Captured by [[Firmware (ESP32)]].
- Persisted via [[Backend API]].
- Merged with demographics + Omron-measured BP through the [[Frontend Dashboard]]'s `commitCollectedData()` call.

## Used By

- Flattened into [[cleaned_data]] for offline preprocessing.

## Caveats

- 536 sessions collected total; 318 retained after cleaning for the [[all_features_dataset|feature matrix]].
- Demographic skew (per the paper): ≈48 % age 20–25, ≈70 % male.
- Real-subject medical data — gitignored at the repo root; kept locally only.

## Linked

- [[Data Pipeline]]
- [[Methodology]]
