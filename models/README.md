# models — Training, Feature Engineering, and Result Plots

This folder contains the offline research code: feature extraction over PPG waveforms,
training drivers for several regressors, evaluation utilities, and the headline performance
plots.

The two **deployed** model artifacts (`random_forest_tuned_model.pkl` and
`best_catboost_model.pkl`) live alongside the Flask app in
[`../BP-Monitoring-model-api/`](../BP-Monitoring-model-api/), not here.

## Scripts

| File | Role |
|---|---|
| [`train_bp_models.py`](train_bp_models.py) | Main 5-fold CV training driver. Reads a CSV of IR signal samples + targets, runs `from_csv_to_features` from `ppg_features.py`, selects top-K features by mutual information, trains Random Forest + Ridge + CatBoost, prints per-fold MAE / R². Optional sample reweighting by `(age_bin, gender)` to reduce demographic bias (`--use_weights`). |
| [`multi_target_train.py`](multi_target_train.py) | Multi-output variant — trains a single model that predicts systolic and diastolic simultaneously. |
| [`target_train_tightened.py`](target_train_tightened.py) | Stricter-threshold training run (the "tight_*" model checkpoints came from this script; all such checkpoints are now in `_archive/models/`). |
| [`quick_train_eval.py`](quick_train_eval.py) | Lightweight script for running a single model + dataset combination during development. |
| [`process_kaggle_and_merge.py`](process_kaggle_and_merge.py) | Utility for ingesting an external Kaggle PPG-BP dataset and merging it with the in-house collection. The Kaggle-trained checkpoints were not selected for deployment. |
| [`ppg_features.py`](ppg_features.py) | Reusable feature module — Butterworth low-pass filter, signal interpolation/resampling, peak detection, beat-morphology, Hjorth parameters, spectral features (centroid, bandwidth, log-energy, band power 0.5–8 Hz), Petrosian fractal dimension, perfusion / augmentation index. Exposes `from_csv_to_features(csv_path, fs_raw, fs_target)`. |
| [`preprocessing.py`](preprocessing.py) | Older preprocessing utilities (the deployed inference pipeline lives in `BP-Monitoring-model-api/preprocessing.py`). |
| [`requirements.txt`](requirements.txt) | Python dependencies for the training environment (matplotlib, ipykernel, etc.). |
| `features list.txt` | Notes file. |

## Result Plots

PNGs in this folder show comparison runs against several model families. They are referenced
by the defense report and kept here as part of the research artifact.

| File | Shows |
|---|---|
| `Ensumble(RF+AB).png` | Random Forest + AdaBoost ensemble. |
| `Ensumble(RF+AB+CAT).png` | Random Forest + AdaBoost + CatBoost triple ensemble. |
| `XGBoost(tuned).png` | Tuned XGBoost. |
| `cat(Tuned).png` | Tuned CatBoost. |
| `lightGMB(tuned).png` | Tuned LightGBM. |
| `Ridgid.png` | Ridge regression baseline. |

## Headline Numbers (paper Table 2)

| Model | MAE | RMSE | R² | MAPE |
|---|---|---|---|---|
| Random Forest (Tuned) | 9.08 | 12.87 | 0.241 | 8.83 % |
| CatBoost (Tuned)      | 9.20 | 12.94 | 0.241 | 9.02 % |

Random Forest is deployed by default; CatBoost ships alongside as a tied alternate. Full
nine-model comparison and the discussion of why the pipeline plateaus at MAE ≈ 9 mmHg are in
the top-level [`README.md`](../README.md#research--results) and the conference paper.

## Reproducing a Training Run

The main script expects a CSV with `ir_*` columns and `systolic_BP` / `diastolic_BP` targets:

```bash
pip install -r requirements.txt
python train_bp_models.py --csv ../datasets/all_features_dataset.csv --k 25 --save_model
```

Optional flags:
- `--fs_raw 5.63 --fs_target 50.0` — raw and target sampling rates for `ppg_features` resampling.
- `--use_weights` — apply `(age_bin, gender)` sample weights to compensate for the demographic skew (≈50 % age 20–25, ≈70 % male) noted in the report.

## Other Files in `models/`

- `__pycache__/`, `catboost_info/`, `venv/` — build / cache directories. All ignored via `.gitignore`.
- `images/` — figures used in slide decks and the report.
