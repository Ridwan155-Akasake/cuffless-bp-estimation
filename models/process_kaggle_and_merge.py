import os
from typing import Dict, List

import numpy as np
import pandas as pd

from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
import joblib

from ppg_features import extract_features_df, from_csv_to_features

try:
    from lightgbm import LGBMRegressor
    HAS_LGBM = True
except Exception:
    HAS_LGBM = False

try:
    from catboost import CatBoostRegressor
    HAS_CAT = True
except Exception:
    HAS_CAT = False


def kaggle_column_map() -> Dict[str, str]:
    return {
        'Systolic Blood Pressure(mmHg)': 'systolic_BP',
        'Diastolic Blood Pressure(mmHg)': 'diastolic_BP',
        'Heart Rate(b/m)': 'heartRate',
        'BMI(kg/m^2)': 'userBmi',
        'Weight(kg)': 'userWeight',
        'Height(cm)': 'userHeight',
        # Optional comorbids kept as-is
    }


def select_top_k(X: pd.DataFrame, y: np.ndarray, k: int = 30) -> List[str]:
    Xn = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    mi = mutual_info_regression(Xn.values, y, random_state=42)
    order = np.argsort(mi)[::-1]
    return Xn.columns[order[: min(k, Xn.shape[1])]].tolist()


def get_models():
    models = [
        ("ridge", make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=3.0, random_state=42))),
        ("rf", RandomForestRegressor(n_estimators=700, random_state=42, n_jobs=-1)),
    ]
    if HAS_LGBM:
        models.append(("lgbm", LGBMRegressor(n_estimators=1200, learning_rate=0.04, num_leaves=63,
                                              subsample=0.8, colsample_bytree=0.8, random_state=42)))
    if HAS_CAT:
        models.append(("catboost", CatBoostRegressor(depth=6, learning_rate=0.05, loss_function="MAE",
                                                     n_estimators=1200, random_seed=42, verbose=False)))
    return models


def run_cv(X: pd.DataFrame, y: np.ndarray, feat_cols: List[str], target: str) -> List[tuple]:
    Xn = X[feat_cols].to_numpy(dtype=float)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = []
    for name, model in get_models():
        mae_list, r2_list = [], []
        for tr, va in kf.split(Xn):
            Xtr, Xva, ytr, yva = Xn[tr], Xn[va], y[tr], y[va]
            model.fit(Xtr, ytr)
            p = model.predict(Xva)
            mae_list.append(mean_absolute_error(yva, p))
            r2_list.append(r2_score(yva, p))
        results.append((name, float(np.mean(mae_list)), float(np.std(mae_list)), float(np.mean(r2_list))))
    results.sort(key=lambda t: t[1])
    return results


def save_results_csv(rows: List[dict], path: str) -> None:
    if rows:
        pd.DataFrame(rows).sort_values(["target", "mae_mean"]).to_csv(path, index=False)


def main():
    kaggle_csv = 'ppg-bp_data_trimmed.csv'
    if not os.path.exists(kaggle_csv):
        raise FileNotFoundError(kaggle_csv)

    # 1) Load Kaggle and rename columns
    raw = pd.read_csv(kaggle_csv)
    cmap = kaggle_column_map()
    raw = raw.rename(columns=cmap)

    # Identify PPG columns (prefix 'PPG_') and extra demographic columns we want to carry
    ir_prefix = 'PPG_'
    extra_cols = [c for c in ['heartRate', 'userBmi', 'userWeight', 'userHeight'] if c in raw.columns]
    # Keep comorbids (optional)
    extra_cols += [c for c in ['Hypertension', 'Diabetes', 'cerebral infarction', 'cerebrovascular disease'] if c in raw.columns]

    # 2) Feature extraction for Kaggle (fs=1000 -> upsample step will just interpolate to 50Hz target)
    feats_kaggle = extract_features_df(raw, ir_prefix=ir_prefix, fs_raw=1000.0, fs_target=50.0, extra_cols=extra_cols)
    # Attach targets if present
    for t in ('systolic_BP', 'diastolic_BP'):
        if t in raw.columns:
            feats_kaggle[t] = raw[t].values

    # Quality gating
    g = feats_kaggle.copy()
    if 'morph_n_beats' in g.columns:
        g = g[g['morph_n_beats'] >= 4]
    if 'sqi_power_ratio' in g.columns:
        g = g[g['sqi_power_ratio'] >= 0.6]
    g = g.reset_index(drop=True)

    # Save Kaggle feature CSVs
    feats_kaggle.to_csv('kaggle_features_extracted.csv', index=False)
    g.to_csv('kaggle_features_gated.csv', index=False)

    # 3) Get your existing dataset features (rebuild to ensure same extractor), then gate
    base_csv = 'bp_dataset_upsampled_50Hz_filtered.csv'
    base = from_csv_to_features(base_csv, fs_raw=50.0, fs_target=50.0)
    b = base.copy()
    if 'morph_n_beats' in b.columns:
        b = b[b['morph_n_beats'] >= 4]
    if 'sqi_power_ratio' in b.columns:
        b = b[b['sqi_power_ratio'] >= 0.6]
    b = b.reset_index(drop=True)
    # Save to ensure visibility
    base.to_csv('my_features_extracted.csv', index=False)
    b.to_csv('my_features_gated.csv', index=False)

    # 4) Merge Kaggle + Your gated features by aligning columns
    # Union of columns; fill missing with 0 for numeric modeling
    merged = pd.concat([g, b], axis=0, ignore_index=True, sort=False)
    merged = merged.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    merged.to_csv('combined_features_gated.csv', index=False)

    # 5) Modeling on Kaggle-only and Combined
    # Helper to run per dataset
    def evaluate_and_save(Xfull: pd.DataFrame, tag: str):
        rows = []
        for target in ('systolic_BP', 'diastolic_BP'):
            if target not in Xfull.columns:
                continue
            # Drop targets for X; numeric only
            Xnum = Xfull.drop(columns=[c for c in ('systolic_BP','diastolic_BP') if c in Xfull.columns])
            Xnum = Xnum.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            y = Xfull[target].to_numpy(dtype=float)
            topk = select_top_k(Xnum, y, k=30)
            res = run_cv(Xnum, y, topk, target)
            # Save per-target topk CSV
            out_topk = Xnum[topk].copy(); out_topk[target] = y
            out_topk.to_csv(f'{tag}_features_{target}_topk.csv', index=False)
            # Append leaderboard rows
            for name, mae_m, mae_s, r2_m in res:
                rows.append({'dataset': tag, 'target': target, 'model': name,
                            'mae_mean': mae_m, 'mae_std': mae_s, 'r2_mean': r2_m})
        # Save results
        save_results_csv(rows, f'{tag}_model_results.csv')

    evaluate_and_save(g, 'kaggle')
    evaluate_and_save(merged, 'combined')

    print('Saved:')
    print(' - kaggle_features_extracted.csv, kaggle_features_gated.csv')
    print(' - my_features_extracted.csv, my_features_gated.csv')
    print(' - combined_features_gated.csv')
    print(' - kaggle_features_*_topk.csv, combined_features_*_topk.csv')
    print(' - kaggle_model_results.csv, combined_model_results.csv')


if __name__ == '__main__':
    main()

