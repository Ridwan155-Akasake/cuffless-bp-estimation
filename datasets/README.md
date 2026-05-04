# datasets — Curated Training Data

Three files were kept; everything else was either superseded, redundant, or experimental,
and has been moved to [`../_archive/datasets/`](../_archive/datasets/).

| File | What it is |
|---|---|
| [`BP_Measuring.finalData.json`](BP_Measuring.finalData.json) | Raw export of the MongoDB `finalData` collection — the source of truth. Each document is one captured session: full IR + RED arrays, on-device HR / SpO₂, user-supplied demographics (age, gender, height, weight, BMI), and ground-truth systolic / diastolic BP measured with an Omron sphygmomanometer. ~1.1 MB. |
| [`cleaned_data.csv`](cleaned_data.csv) | Same content as the JSON above, flattened into a CSV with `ir` / `red` stored as JSON-array strings — the canonical input for downstream preprocessing notebooks. |
| [`all_features_dataset.csv`](all_features_dataset.csv) | Final feature matrix used for model training. 400 columns × 318 rows: `ir_0 … ir_199, red_0 … red_199, userAge, userGender, userHeight, userWeight, userBmi, spo2, heartRate, systolic_BP, diastolic_BP`. Produced by resampling each session's IR / RED arrays to a fixed length of 200 samples. (The full collected set was 536 records; 318 remain after dropping rows with invalid placeholders / missing demographics.) |

## Pipeline

```
ESP32 device  ──HTTPS POST──▶  rawDataCollection (Mongo)
                                       │
                                       ▼
                          merged with demographics + BP
                                       │
                                       ▼
                            finalData (Mongo)
                                       │
                          export ───┐  │
                                    ▼  ▼
                       BP_Measuring.finalData.json
                                       │
                          flatten + clean
                                       ▼
                              cleaned_data.csv
                                       │
                          resample IR/RED to 200 samples
                                       ▼
                          all_features_dataset.csv  ◀── used by models/train_bp_models.py
```

## Caveats

- **Sample size:** 536 collected sessions, 318 retained for the feature matrix. Small for a regression task as noisy as cuffless BP.
- **Demographic skew (per the paper):** ≈48 % aged 20–25, ≈70 % male. Models should not be assumed to generalize to elderly or female populations.
- **Sensor quality:** consumer-grade MAX30102, not research-grade PPG hardware.
- **Privacy:** these are real-subject measurements. `BP_Measuring.finalData.json` and `cleaned_data.csv` are listed in the root `.gitignore` — they remain in your local working tree but are **not committed** to the public repo. The aggregated, signal-only feature matrix [`all_features_dataset.csv`](all_features_dataset.csv) does not contain personally identifying fields and is safe to commit.
