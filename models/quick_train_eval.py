import os
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

from ppg_features import from_csv_to_features

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

try:
    import shap
    HAS_SHAP = True
except Exception:
    HAS_SHAP = False


def select_top_k(X: pd.DataFrame, y: np.ndarray, k: int = 30) -> list:
    Xn = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    mi = mutual_info_regression(Xn.values, y, random_state=42)
    order = np.argsort(mi)[::-1]
    return Xn.columns[order[: min(k, Xn.shape[1])]].tolist()


def get_models():
    models = []
    models.append(("ridge", make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=3.0, random_state=42))))
    models.append(("rf", RandomForestRegressor(n_estimators=700, random_state=42, n_jobs=-1)))
    if HAS_LGBM:
        models.append(("lgbm", LGBMRegressor(n_estimators=1500, learning_rate=0.03, num_leaves=63, subsample=0.8, colsample_bytree=0.8, random_state=42)))
    if HAS_CAT:
        models.append(("catboost", CatBoostRegressor(depth=6, learning_rate=0.05, loss_function="MAE", n_estimators=1500, random_seed=42, verbose=False)))
    return models


def run_cv(X: pd.DataFrame, y: np.ndarray, feat_cols: list, target: str):
    Xn = X[feat_cols].to_numpy(dtype=float)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = []
    for name, model in get_models():
        mae_list, r2_list = [], []
        for tr, va in kf.split(Xn):
            Xtr, Xva = Xn[tr], Xn[va]
            ytr, yva = y[tr], y[va]
            model.fit(Xtr, ytr)
            p = model.predict(Xva)
            mae_list.append(mean_absolute_error(yva, p))
            r2_list.append(r2_score(yva, p))
        results.append((name, float(np.mean(mae_list)), float(np.std(mae_list)), float(np.mean(r2_list))))
    # Sort by mean MAE
    results.sort(key=lambda t: t[1])
    print(f"\nLeaderboard for {target} (sorted by MAE):")
    for name, mae_m, mae_s, r2_m in results:
        print(f"  {name:8s} | MAE {mae_m:6.3f} ± {mae_s:5.3f} | R2 {r2_m:6.3f}")
    return results


def fit_save_and_shap(X: pd.DataFrame, y: np.ndarray, feat_cols: list, model_name: str, target: str, out_dir: str = "images"):
    os.makedirs(out_dir, exist_ok=True)
    # Choose model object again
    model = None
    for name, m in get_models():
        if name == model_name:
            model = m
            break
    if model is None:
        return None
    Xn = X[feat_cols].to_numpy(dtype=float)
    model.fit(Xn, y)
    out_path = f"model_{target}_{model_name}.pkl"
    joblib.dump({"model": model, "features": feat_cols}, out_path)
    print(f"Saved best {target} model -> {out_path}")

    # Optional SHAP
    shap_path = None
    if HAS_SHAP:
        try:
            if model_name in ("lgbm", "rf", "catboost"):
                # Use a small background to speed up
                bg_idx = np.random.RandomState(42).choice(len(Xn), size=min(200, len(Xn)), replace=False)
                background = Xn[bg_idx]
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(background)
                # Summary bar plot
                import matplotlib.pyplot as plt
                plt.figure(figsize=(8, 6))
                try:
                    shap.summary_plot(shap_values, background, feature_names=feat_cols, plot_type="bar", show=False)
                except Exception:
                    # fallback: importance via absolute shap means
                    sv = np.abs(shap_values).mean(axis=0)
                    order = np.argsort(sv)[::-1][:20]
                    plt.barh([feat_cols[i] for i in order][::-1], sv[order][::-1])
                    plt.title(f"SHAP bar ({target} {model_name})")
                shap_path = os.path.join(out_dir, f"shap_{target}_{model_name}.png")
                plt.tight_layout()
                plt.savefig(shap_path, dpi=150)
                plt.close()
                print(f"Saved SHAP summary -> {shap_path}")
        except Exception as e:
            print(f"SHAP failed for {target}/{model_name}: {e}")
    return shap_path


def main():
    csv = "bp_dataset_upsampled_50Hz_filtered.csv"
    if not os.path.exists(csv):
        raise FileNotFoundError(csv)

    fs_raw = 50.0 if "upsampled_50Hz" in csv else 5.63
    feats = from_csv_to_features(csv, fs_raw=fs_raw, fs_target=50.0)

    # Apply quality gates if available
    if "morph_n_beats" in feats.columns:
        feats = feats[feats["morph_n_beats"] >= 4].copy()
    if "sqi_power_ratio" in feats.columns:
        feats = feats[feats["sqi_power_ratio"] >= 0.6].copy()
    feats = feats.reset_index(drop=True)

    # Save gated full feature set
    feats.to_csv("features_all_gated.csv", index=False)

    # Targets
    for target in ("systolic_BP", "diastolic_BP"):
        if target not in feats.columns:
            raise ValueError(f"Missing target: {target}")

    # Feature matrix
    drop_cols = ["systolic_BP", "diastolic_BP"]
    X = feats.drop(columns=[c for c in drop_cols if c in feats.columns])
    X = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Run per target
    summary = {}
    results_rows = []
    for target in ("systolic_BP", "diastolic_BP"):
        y = feats[target].to_numpy(dtype=float)
        topk = select_top_k(X, y, k=30)
        print(f"\nSelected top-{len(topk)} MI features for {target}")
        results = run_cv(X, y, topk, target)
        best_name = results[0][0]
        shap_path = fit_save_and_shap(X, y, topk, best_name, target)
        summary[target] = {"best_model": best_name, "leaderboard": results, "features": topk, "shap_plot": shap_path}

        # Append results rows for CSV
        for name, mae_m, mae_s, r2_m in results:
            results_rows.append({
                "target": target,
                "model": name,
                "mae_mean": mae_m,
                "mae_std": mae_s,
                "r2_mean": r2_m
            })

        # Save per-target full and top-k feature CSVs
        per_target_full = X.copy()
        per_target_full[target] = y
        per_target_full.to_csv(f"features_{target}_gated.csv", index=False)

        topk_df = X[topk].copy()
        topk_df[target] = y
        topk_df.to_csv(f"features_{target}_topk.csv", index=False)

    # Save leaderboard summary
    summ_path = "images/leaderboard_summary.txt"
    os.makedirs("images", exist_ok=True)
    with open(summ_path, "w", encoding="utf-8") as f:
        for target, info in summary.items():
            f.write(f"Target: {target}\n")
            f.write(f"Best: {info['best_model']}\n")
            for name, mae_m, mae_s, r2_m in info["leaderboard"]:
                f.write(f"  {name} | MAE {mae_m:.3f} ± {mae_s:.3f} | R2 {r2_m:.3f}\n")
            f.write("Features (top 30):\n")
            for feat in info["features"]:
                f.write(f"  - {feat}\n")
            f.write(f"SHAP: {info['shap_plot']}\n\n")
    print(f"Saved leaderboard summary -> {summ_path}")

    # Save results CSV
    if results_rows:
        res_df = pd.DataFrame(results_rows)
        res_df = res_df.sort_values(["target", "mae_mean"]).reset_index(drop=True)
        res_df.to_csv("model_results.csv", index=False)
        print("Saved model results -> model_results.csv")


if __name__ == "__main__":
    main()
