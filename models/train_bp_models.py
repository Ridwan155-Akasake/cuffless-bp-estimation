import argparse
import os
from typing import List, Tuple

import numpy as np
import pandas as pd

from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
import joblib

from ppg_features import from_csv_to_features

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except Exception:
    CATBOOST_AVAILABLE = False


def select_top_k_features(X: pd.DataFrame, y: np.ndarray, k: int = 25) -> List[str]:
    Xn = X.select_dtypes(include=[np.number]).fillna(0.0)
    mi = mutual_info_regression(Xn.values, y, random_state=42)
    order = np.argsort(mi)[::-1]
    top_idx = order[: min(k, Xn.shape[1])]
    return Xn.columns[top_idx].tolist()


def get_regressors() -> List[Tuple[str, object]]:
    regs: List[Tuple[str, object]] = []
    # Robust baseline
    regs.append(("rf", RandomForestRegressor(n_estimators=600, max_depth=None, random_state=42, n_jobs=-1)))
    # Linear ridge on scaled features as a complementary bias
    regs.append(("ridge", make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=3.0, random_state=42))))
    if CATBOOST_AVAILABLE:
        regs.append((
            "catboost",
            CatBoostRegressor(
                depth=6,
                learning_rate=0.05,
                loss_function="MAE",
                n_estimators=1500,
                random_seed=42,
                verbose=False,
            ),
        ))
    return regs


def run_cv(X: pd.DataFrame, y: np.ndarray, feature_names: List[str], target_name: str) -> None:
    Xn = X[feature_names].to_numpy(dtype=float)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    regs = get_regressors()

    for name, reg in regs:
        fold_mae, fold_r2 = [], []
        for tr, va in kf.split(Xn):
            Xtr, Xva = Xn[tr], Xn[va]
            ytr, yva = y[tr], y[va]
            reg.fit(Xtr, ytr)
            p = reg.predict(Xva)
            fold_mae.append(mean_absolute_error(yva, p))
            fold_r2.append(r2_score(yva, p))
        print(f"{target_name} | {name} -> MAE: {np.mean(fold_mae):.3f} ± {np.std(fold_mae):.3f} | R2: {np.mean(fold_r2):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="bp_dataset_upsampled_50Hz_filtered.csv", help="Input CSV with ir_.. columns and targets")
    ap.add_argument("--fs_raw", type=float, default=5.63)
    ap.add_argument("--fs_target", type=float, default=50.0)
    ap.add_argument("--k", type=int, default=25, help="Top-K features by mutual information")
    ap.add_argument("--save_model", action="store_true")
    ap.add_argument("--use_weights", action="store_true", help="Reweight by (age_bin, gender) to reduce demographic bias")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        raise FileNotFoundError(args.csv)

    # Build features
    feats = from_csv_to_features(args.csv, fs_raw=args.fs_raw, fs_target=args.fs_target)
    if "systolic_BP" not in feats.columns or "diastolic_BP" not in feats.columns:
        raise ValueError("Targets systolic_BP and diastolic_BP not found in input CSV")

    # Numeric feature matrix (drop targets)
    feature_cols = [c for c in feats.columns if c not in ("systolic_BP", "diastolic_BP")]
    X = feats[feature_cols].select_dtypes(include=[np.number]).copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Optional sample weights by demographic bins
    sample_weights = None
    if args.use_weights and {"userAge", "userGender"}.issubset(feats.columns):
        age = feats["userAge"].to_numpy(dtype=float)
        gender = feats["userGender"].to_numpy(dtype=float)
        # Define age bins
        bins = np.array([0, 25, 35, 50, 65, 200])
        age_bin = np.digitize(age, bins)  # 1..len(bins)
        groups = age_bin.astype(int) * 10 + gender.astype(int)
        # Compute inverse frequency weights
        vals, counts = np.unique(groups, return_counts=True)
        freq = dict(zip(vals.tolist(), counts.tolist()))
        w = np.array([1.0 / max(freq.get(g, 1), 1) for g in groups], dtype=float)
        w = w * (len(w) / (np.sum(w) + 1e-12))  # normalize to mean ~1
        sample_weights = w

    # Train two separate models (SBP and DBP)
    for target in ("systolic_BP", "diastolic_BP"):
        y = feats[target].to_numpy(dtype=float)
        topk = select_top_k_features(X, y, k=args.k)
        print(f"Selected top-{len(topk)} features for {target}")
        run_cv(X, y, topk, target)

        if args.save_model:
            # Fit strongest regressor on full data and save
            regs = get_regressors()
            # Choose CatBoost if available else RF
            name, reg = regs[-1] if CATBOOST_AVAILABLE else regs[0]
            if sample_weights is not None:
                try:
                    reg.fit(X[topk].to_numpy(dtype=float), y, sample_weight=sample_weights)
                except TypeError:
                    reg.fit(X[topk].to_numpy(dtype=float), y)
            else:
                reg.fit(X[topk].to_numpy(dtype=float), y)
            out_name = f"model_{target}_{name}.pkl"
            joblib.dump({"model": reg, "features": topk}, out_name)
            print(f"Saved {target} model -> {out_name}")


if __name__ == "__main__":
    main()
