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
from sklearn.multioutput import MultiOutputRegressor
import joblib


def load_features(tag: str) -> pd.DataFrame:
    if tag == 'kaggle':
        path = 'kaggle_features_gated.csv'
    elif tag == 'combined':
        path = 'combined_features_gated.csv'
    elif tag == 'kaggle_tight':
        path = 'kaggle_features_gated_tight.csv'
    elif tag == 'combined_tight':
        path = 'combined_features_gated_tight.csv'
    else:
        path = tag
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    return df


def select_topk_union(X: pd.DataFrame, y_sbp: np.ndarray, y_dbp: np.ndarray, k_each: int = 25) -> List[str]:
    Xn = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    mi_sbp = mutual_info_regression(Xn.values, y_sbp, random_state=42)
    mi_dbp = mutual_info_regression(Xn.values, y_dbp, random_state=42)
    order_sbp = np.argsort(mi_sbp)[::-1][: min(k_each, Xn.shape[1])]
    order_dbp = np.argsort(mi_dbp)[::-1][: min(k_each, Xn.shape[1])]
    idx_union = np.unique(np.concatenate([order_sbp, order_dbp]))
    return Xn.columns[idx_union].tolist()


def make_models():
    models: Dict[str, Tuple[object, Dict[str, List]]]= {}
    # Ridge (multi-output native). Use pipeline for scaling
    ridge = make_pipeline(StandardScaler(with_mean=False), Ridge())
    ridge_grid = {
        'ridge__alpha': [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0],
    }
    models['ridge'] = (ridge, ridge_grid)

    # RandomForest (supports multi-output)
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    rf_grid = {
        'n_estimators': [400, 600, 800],
        'max_depth': [None, 8, 12, 16, 24],
        'min_samples_leaf': [1, 2, 3, 5],
        'max_features': ['sqrt', 0.6, 0.8, 1.0],
    }
    models['rf'] = (rf, rf_grid)

    # AdaBoost (wrap for multi-output)
    ada_base = AdaBoostRegressor(random_state=42)
    ada = MultiOutputRegressor(ada_base)
    ada_grid = {
        'estimator__n_estimators': [200, 400, 600],
        'estimator__learning_rate': [0.03, 0.05, 0.1, 0.3, 1.0],
        'estimator__loss': ['linear', 'square', 'exponential'],
    }
    models['adaboost'] = (ada, ada_grid)

    # LightGBM (wrap for multi-output)
    try:
        from lightgbm import LGBMRegressor
        lgb = MultiOutputRegressor(LGBMRegressor(random_state=42))
        lgb_grid = {
            'estimator__n_estimators': [800, 1200, 1600],
            'estimator__learning_rate': [0.02, 0.03, 0.05],
            'estimator__num_leaves': [31, 63, 127],
            'estimator__subsample': [0.7, 0.8, 1.0],
            'estimator__colsample_bytree': [0.7, 0.8, 1.0],
            'estimator__min_child_samples': [10, 20, 40],
        }
        models['lgbm'] = (lgb, lgb_grid)
    except Exception:
        pass

    # CatBoost (native multi-output via MultiRMSE)
    try:
        from catboost import CatBoostRegressor
        # Use Bernoulli bootstrap to allow subsample tuning
        cat = CatBoostRegressor(loss_function='MultiRMSE', random_seed=42, verbose=False, bootstrap_type='Bernoulli')
        cat_grid = {
            'depth': [4, 6, 8],
            'learning_rate': [0.03, 0.05, 0.1],
            'l2_leaf_reg': [3, 5, 7, 10],
            'iterations': [800, 1200, 1600],
            'subsample': [0.7, 0.8, 1.0],
        }
        models['catboost'] = (cat, cat_grid)
    except Exception:
        pass

    return models


def cv_metrics(model, X: np.ndarray, y: np.ndarray, splits=5) -> Tuple[float, float]:
    kf = KFold(n_splits=splits, shuffle=True, random_state=42)
    maes, r2s = [], []
    for tr, va in kf.split(X):
        Xtr, Xva, ytr, yva = X[tr], X[va], y[tr], y[va]
        model.fit(Xtr, ytr)
        p = model.predict(Xva)
        maes.append(mean_absolute_error(yva, p))
        r2s.append(r2_score(yva, p))
    return float(np.mean(maes)), float(np.mean(r2s))


def train_multi(tag: str, k_each: int = 25, n_iter: int = 12) -> pd.DataFrame:
    df = load_features(tag)
    # Keep numeric X
    if not {'systolic_BP', 'diastolic_BP'}.issubset(df.columns):
        raise ValueError('Targets systolic_BP, diastolic_BP missing')
    y = df[['systolic_BP', 'diastolic_BP']].to_numpy(dtype=float)
    X = df.drop(columns=['systolic_BP', 'diastolic_BP']).select_dtypes(include=[np.number])
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Select union Top-K per target
    feats = select_topk_union(X, y[:, 0], y[:, 1], k_each=k_each)
    Xn = X[feats].to_numpy(dtype=float)

    # Save topk union CSV
    out_topk = X[feats].copy()
    out_topk['systolic_BP'] = y[:, 0]
    out_topk['diastolic_BP'] = y[:, 1]
    out_topk.to_csv(f'{tag}_features_multi_topk.csv', index=False)

    models = make_models()
    rows = []
    scorer = make_scorer(mean_absolute_error, greater_is_better=False)
    for name, (est, grid) in models.items():
        try:
            # Randomized search
            rs = RandomizedSearchCV(est, grid, n_iter=n_iter, scoring=scorer, cv=5, random_state=42, n_jobs=-1, verbose=0)
            rs.fit(Xn, y)
            best = rs.best_estimator_
            mae, r2 = cv_metrics(best, Xn, y, splits=5)
            rows.append({'dataset': tag, 'model': name, 'mae_mean': mae, 'r2_mean': r2, 'best_params': str(rs.best_params_)})
            # Save model
            joblib.dump({'model': best, 'features': feats}, f'multi_model_{tag}_{name}.pkl')
        except Exception as e:
            rows.append({'dataset': tag, 'model': name, 'mae_mean': np.nan, 'r2_mean': np.nan, 'best_params': f'error: {e}'})
    res = pd.DataFrame(rows).sort_values('mae_mean')
    res.to_csv(f'multi_model_results_{tag}.csv', index=False)
    return res


def main():
    # Default to tight-gated combined if available; else fall back
    tag = 'combined_tight' if os.path.exists('combined_features_gated_tight.csv') else 'combined'
    res = train_multi(tag, k_each=25, n_iter=10)
    print(f'{tag} results:\n', res)


if __name__ == '__main__':
    main()
