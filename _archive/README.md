# _archive — Superseded Experiments

This folder holds files that were generated during research but are **not** part of the final
system. Nothing here is loaded by any deployed component. The contents are preserved purely
so the research lineage is traceable and so older notebooks can still re-open their inputs.

## Layout

```
_archive/
├── datasets/    superseded / redundant CSVs and JSONs (48 files)
├── models/      experimental .pkl checkpoints (38 files), bp_dataset_resampledV2.csv,
│                Dataset/, ppg_signal.txt
└── notebooks/   exploratory Jupyter notebooks (10 files)
```

## What's in `_archive/datasets/`

- Multiple intermediate cleaning passes: `cleaned_data (1).csv`, `cleaned2_data.csv`, `cleaned_data_with_bmi.csv`, `df_with_nulls.csv`.
- Channel-ablation experiments: `ir_features_*`, `red_features_*`, `ir_red_demographics_*`, `ir_red_vitals_*`, `ppg_only_dataset.csv`.
- Feature-engineering iterations: `extracted_features.csv`, `combined_features_labels.csv`, `total_features_dataset.csv`, `ppg_features_dataset.csv`.
- External-data experiments: `kaggel_features_df.csv`, `ir_local_features_df.csv`, `red_local_features_df.csv`, `ppg-bp_data_online.csv`, `ppg_data_only.csv`, `ppg_bp_data_cleaned.csv`, `Generated_PPG_Blood_Pressure_Dataset.csv`.
- Older labels: `labels.csv`, `labelsV2.csv`.
- Older Mongo exports: `BP_Measuring.finalDataV2.csv`, `BP_Measuring_finalDatav2.csv`.
- Resampling iterations: `bp_dataset_resampledV2.csv`, `bp_dataset_resampled_200_V2.csv`.
- Old archive folder: `archive (3)/`, `archive (3).zip`.
- Earlier processing notebooks and helper scripts: `PPG_Data.ipynb`, `New_PPG_Data_processing.ipynb`, `ppg_data.py`.

## What's in `_archive/models/`

- **Single-target Random Forest baselines:** `model_systolic_BP_rf.pkl`, `model_diastolic_BP_rf.pkl`, `random_forest_best_mae_model2.pkl` — the original "two separate models per output" approach, before the multi-output ensemble.
- **Multi-output combined experiments** (one model predicts both systolic and diastolic): `multi_model_combined_{rf,catboost,lgbm,adaboost,ridge}.pkl` plus their `_tight_` variants — checkpoints that explored stricter feature filters.
- **Tightened single-target experiments:** `tight_model_combined_tight_{systolic,diastolic}_BP_{rf,catboost,lgbm,adaboost,ridge}.pkl` — finer-grained ablations across regressors.
- **Kaggle-track experiments:** `multi_model_kaggle_*.pkl` and `tight_model_kaggle_tight_*.pkl` — same family of architectures trained on the external Kaggle PPG-BP dataset rather than the in-house collection. They were not deployed because the Kaggle data did not match the project's sensor characteristics.
- A misplaced training CSV (`bp_dataset_resampledV2.csv`) and a `Dataset/` subfolder that lived inside `models/`.

None of these files are loaded by the production API. The deployed Random Forest lives at
[`../BP-Monitoring-model-api/random_forest_tuned_model.pkl`](../BP-Monitoring-model-api/random_forest_tuned_model.pkl).

## What's in `_archive/notebooks/`

Exploratory Jupyter work — feature extraction, feature selection, model testing, data
resampling. The methodology in the final defense report is the canonical write-up; these
notebooks contain the raw experimental traces that fed it.
