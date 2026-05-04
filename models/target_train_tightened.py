import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, r2_score, make_scorer
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
import joblib


DEMO_COLS_CANON = [
    "spo2", "heartRate", "userAge", "userGender", "userHeight", "userWeight", "userBmi",
    "Hypertension", "Diabetes", "cerebral infarction", "cerebrovascular disease"
]


def load_ungated_features() -> Tuple[pd.DataFrame, pd.DataFrame]:
    kag = pd.read_csv("kaggle_features_extracted.csv") if os.path.exists("kaggle_features_extracted.csv") else None
    myf = pd.read_csv("my_features_extracted.csv") if os.path.exists("my_features_extracted.csv") else None
    if kag is None or myf is None:
        raise FileNotFoundError("Missing kaggle_features_extracted.csv or my_features_extracted.csv. Run process_kaggle_and_merge.py first.")
    return kag, myf


def tighten_gates(df: pd.DataFrame, min_beats: int = 5, min_sqi: float = 0.7) -> pd.DataFrame:
    g = df.copy()
    if "morph_n_beats" in g.columns:
        g = g[g["morph_n_beats"] >= min_beats]
    if "sqi_power_ratio" in g.columns:
        g = g[g["sqi_power_ratio"] >= min_sqi]
    return g.reset_index(drop=True)


def split_demo_ppg(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    demo = [c for c in DEMO_COLS_CANON if c in df.columns]
    # Consider all numeric, non-target, non-demo as PPG-derived
    targets = [c for c in ("systolic_BP", "diastolic_BP") if c in df.columns]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    ppg = [c for c in numeric_cols if c not in demo + targets]
    return demo, ppg


def select_ppg_topk(X: pd.DataFrame, y: np.ndarray, ppg_cols: List[str], k: int = 30) -> List[str]:
    # MI on PPG features only
    Xppg = X[ppg_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if Xppg.shape[1] == 0:
        return []
    mi = mutual_info_regression(Xppg.values, y, random_state=42)
    order = np.argsort(mi)[::-1]
    return [ppg_cols[i] for i in order[: min(k, len(ppg_cols))]]


def get_models() -> Dict[str, Tuple[object, Dict[str, List]]]:
    models: Dict[str, Tuple[object, Dict[str, List]]] = {}
    # Ridge
    ridge = make_pipeline(StandardScaler(with_mean=False), Ridge(random_state=42))
    ridge_grid = {"ridge__alpha": [0.3, 1.0, 3.0, 10.0, 30.0, 100.0]}
    models["ridge"] = (ridge, ridge_grid)

    # RandomForest
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    rf_grid = {
        "n_estimators": [500, 800, 1200],
        "max_depth": [None, 10, 16, 24],
        "min_samples_leaf": [1, 2, 3, 5],
        "max_features": ["sqrt", 0.6, 0.8, 1.0],
    }
    models["rf"] = (rf, rf_grid)

    # AdaBoost
    ada = AdaBoostRegressor(random_state=42)
    ada_grid = {
        "n_estimators": [200, 400, 600, 800],
        "learning_rate": [0.02, 0.03, 0.05, 0.1, 0.3],
        "loss": ["linear", "square", "exponential"],
    }
    models["adaboost"] = (ada, ada_grid)

    # LightGBM
    try:
        from lightgbm import LGBMRegressor
        lgb = LGBMRegressor(random_state=42)
        lgb_grid = {
            "n_estimators": [800, 1200, 1600],
            "learning_rate": [0.02, 0.03, 0.05],
            "num_leaves": [31, 63, 127],
            "subsample": [0.7, 0.8, 1.0],
            "colsample_bytree": [0.7, 0.8, 1.0],
            "min_child_samples": [10, 20, 40],
        }
        models["lgbm"] = (lgb, lgb_grid)
    except Exception:
        pass

    # CatBoost
    try:
        from catboost import CatBoostRegressor
        cat = CatBoostRegressor(loss_function="MAE", random_seed=42, verbose=False, bootstrap_type="Bernoulli")
        cat_grid = {
            "depth": [4, 6, 8],
            "learning_rate": [0.03, 0.05, 0.1],
            "l2_leaf_reg": [3, 7, 10],
            "iterations": [800, 1200, 1600],
            "subsample": [0.7, 1.0],
        }
        models["catboost"] = (cat, cat_grid)
    except Exception:
        pass

    return models


def eval_cv(model, X: np.ndarray, y: np.ndarray, splits: int = 5) -> Tuple[float, float]:
    kf = KFold(n_splits=splits, shuffle=True, random_state=42)
    maes, r2s = [], []
    for tr, va in kf.split(X):
        Xtr, Xva, ytr, yva = X[tr], X[va], y[tr], y[va]
        model.fit(Xtr, ytr)
        p = model.predict(Xva)
        maes.append(mean_absolute_error(yva, p))
        r2s.append(r2_score(yva, p))
    return float(np.mean(maes)), float(np.mean(r2s))


def train_per_target(df: pd.DataFrame, tag: str, topk: int = 30, n_iter: int = 20) -> pd.DataFrame:
    # Prepare X, y and column partitions
    if not {"systolic_BP", "diastolic_BP"}.issubset(df.columns):
        raise ValueError("Targets missing in dataframe")
    y_sbp = df["systolic_BP"].to_numpy(dtype=float)
    y_dbp = df["diastolic_BP"].to_numpy(dtype=float)
    demo_cols, ppg_cols = split_demo_ppg(df)
    # Coerce demo cols to numeric when possible (e.g., comorbids)
    df_num = df.copy()
    for c in demo_cols:
        if c in df_num.columns:
            df_num[c] = pd.to_numeric(df_num[c], errors='coerce')
    Xnum = df_num.drop(columns=["systolic_BP", "diastolic_BP"]).select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    results: List[dict] = []

    # For each target, select PPG top-k and always include demographics
    for target_name, y in ("systolic_BP", y_sbp), ("diastolic_BP", y_dbp):
        ppg_top = select_ppg_topk(Xnum, y, ppg_cols, k=topk)
        feat_cols = demo_cols + ppg_top

        # Save chosen features dataset
        # Keep only columns that exist (some demo may still be absent)
        feat_exist = [c for c in feat_cols if c in Xnum.columns]
        feat_df = Xnum[feat_exist].copy()
        feat_df[target_name] = y
        out_feat_path = f"tight_features_{tag}_{target_name}.csv"
        feat_df.to_csv(out_feat_path, index=False)

        X = Xnum[feat_exist].to_numpy(dtype=float)
        models = get_models()
        scorer = make_scorer(mean_absolute_error, greater_is_better=False)

        for name, (est, grid) in models.items():
            try:
                rs = RandomizedSearchCV(est, grid, n_iter=min(n_iter, np.prod([len(v) for v in grid.values()])),
                                        scoring=scorer, cv=5, random_state=42, n_jobs=-1, verbose=0)
                rs.fit(X, y)
                best = rs.best_estimator_
                mae, r2 = eval_cv(best, X, y, splits=5)
                results.append({
                    "dataset": tag,
                    "target": target_name,
                    "model": name,
                    "mae_mean": mae,
                    "r2_mean": r2,
                    "best_params": str(rs.best_params_),
                    "n_features": len(feat_cols)
                })
                joblib.dump({"model": best, "features": feat_cols}, f"tight_model_{tag}_{target_name}_{name}.pkl")
            except Exception as e:
                results.append({
                    "dataset": tag,
                    "target": target_name,
                    "model": name,
                    "mae_mean": np.nan,
                    "r2_mean": np.nan,
                    "best_params": f"error: {e}",
                    "n_features": len(feat_cols)
                })

    res_df = pd.DataFrame(results).sort_values(["target", "mae_mean"]).reset_index(drop=True)
    res_df.to_csv(f"tight_model_results_{tag}.csv", index=False)
    return res_df


def main():
    # 1) Load ungated features
    kag, myf = load_ungated_features()

    # 2) Tighten gates
    kag_t = tighten_gates(kag, min_beats=5, min_sqi=0.7)
    myf_t = tighten_gates(myf, min_beats=5, min_sqi=0.7)

    kag_t.to_csv("kaggle_features_gated_tight.csv", index=False)
    myf_t.to_csv("my_features_gated_tight.csv", index=False)

    # 3) Merge
    combined_t = pd.concat([kag_t, myf_t], axis=0, ignore_index=True, sort=False)
    combined_t = combined_t.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    combined_t.to_csv("combined_features_gated_tight.csv", index=False)

    # 4) Train per target on each dataset
    print("Training on Kaggle (tight gates)...")
    res_k = train_per_target(kag_t, tag="kaggle_tight", topk=30, n_iter=20)
    print("Training on Combined (tight gates)...")
    res_c = train_per_target(combined_t, tag="combined_tight", topk=30, n_iter=20)
    print("Done. Results saved to tight_model_results_*.csv")


if __name__ == "__main__":
    main()
