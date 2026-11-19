import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, KFold, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
from .config import PROCESSED_DIR, MODEL_DIR, REPORT_DIR

RANDOM_STATE = 42
ALPHAS = np.logspace(-3, 3, 20)

def drop_outliers(df, cols, quantile_hi=0.99):
    mask = pd.Series(True, index=df.index)
    for col in cols:
        mask &= (df[col] <= df[col].quantile(quantile_hi))
    return df[mask].copy()

def build_candidates():
    return {
        'LinearRegression': Pipeline([('scaler', StandardScaler()),('lr', LinearRegression())]),
        'Ridge': GridSearchCV(
            Pipeline([('scaler', StandardScaler()),('ridge', Ridge())]),
            param_grid={'ridge__alpha': ALPHAS}, cv=5, scoring='r2', n_jobs=-1),
        'Lasso': GridSearchCV(
            Pipeline([('scaler', StandardScaler()),('lasso', Lasso(max_iter=100000))]),
            param_grid={'lasso__alpha': ALPHAS}, cv=5, scoring='r2', n_jobs=-1),
    }

def eval_model(model, X_tr, X_te, y_tr, y_te, kfold):
    y_tr_hat = model.predict(X_tr); y_te_hat = model.predict(X_te)
    r2_tr = r2_score(y_tr, y_tr_hat); r2_te = r2_score(y_te, y_te_hat)
    n, p = len(y_te), X_te.shape[1]
    adj = 1 - (1-r2_te)*(n-1)/max(n-p-1,1)
    cv = cross_val_score(model, X_tr, y_tr, cv=kfold, scoring='r2', n_jobs=-1)
    return {
        'r2_train': r2_tr, 'r2_test': r2_te, 'adj_r2_test': adj,
        'rmse_test': float(np.sqrt(mean_squared_error(y_te, y_te_hat))),
        'mae_test': mean_absolute_error(y_te, y_te_hat),
        'cv_r2_mean': cv.mean(), 'cv_r2_std': cv.std(),
        'gap_train_cv': r2_tr - cv.mean(),
    }

def run_regression(name, path, x_col, y_col, use_log=True):
    df = pd.read_parquet(path).dropna(subset=[x_col, y_col])
    df = df[(df[x_col] > 0) & (df[y_col] > 0)]
    if len(df) < 30:
        return None

    if use_log:
        X = np.log1p(df[[x_col]].values); y = np.log1p(df[y_col].values)
    else:
        X = df[[x_col]].values; y = df[y_col].values

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    kfold = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    candidates = build_candidates()
    rows, fitted = [], {}
    for mname, mdl in candidates.items():
        mdl.fit(X_tr, y_tr)
        met = eval_model(mdl, X_tr, X_te, y_tr, y_te, kfold)
        met.update({'dataset': name, 'model': mname})
        rows.append(met); fitted[mname] = mdl

    res_df = pd.DataFrame(rows)
    ok = res_df[res_df['gap_train_cv'] < 0.15]
    if len(ok) == 0: ok = res_df
    best = ok.sort_values('cv_r2_mean', ascending=False).iloc[0]
    best_name = best['model']; best_model = fitted[best_name]

    safe = name.lower().replace(' ','_').replace('&','dan').replace('(','').replace(')','')
    joblib.dump(best_model, MODEL_DIR / f'regressor_{safe}.pkl')

    # Koefisien
    coef_info = {}
    inner = best_model
    if hasattr(inner, 'best_estimator_'): inner = inner.best_estimator_
    if isinstance(inner, Pipeline):
        sc = inner.named_steps.get('scaler', None)
        last = inner.steps[-1][1]
        coef = getattr(last, 'coef_', None)
        if coef is not None and sc is not None and X_tr.shape[1] == 1:
            c = float(coef[0] / sc.scale_[0])
            coef_info['coef_unscaled_per_unit'] = c
            if use_log:
                coef_info['interpretasi'] = f'Elastisitas: +1% {x_col} -> +{c:.2f}% {y_col}'

    return {'name': name, 'res_df': res_df, 'best_name': best_name,
            'best_row': best.to_dict(), 'coef_info': coef_info,
            'use_log': use_log}

def run_all_regression() -> dict:
    for fname, cols in [
        ('reg_nilai_volume', ['x_volume_ton', 'y_nilai_rp_juta']),
        ('reg_produksi_rtp', ['x_rtp', 'y_produksi_ton']),
        ('reg_produksi_luas', ['x_luas_ha', 'y_produksi_ton']),
    ]:
        path = PROCESSED_DIR / f'{fname}.parquet'
        if path.exists():
            df = pd.read_parquet(path)
            df = drop_outliers(df, cols)
            df.to_parquet(PROCESSED_DIR / f'{fname}_clean.parquet', index=False)

    res_utama = run_regression(
        'Nilai vs Volume (Log-Winsorized)',
        PROCESSED_DIR / 'reg_nilai_volume_clean.parquet',
        'x_volume_ton', 'y_nilai_rp_juta', use_log=True)
    res_rtp = run_regression(
        'Produksi vs RTP (Log-Winsorized)',
        PROCESSED_DIR / 'reg_produksi_rtp_clean.parquet',
        'x_rtp', 'y_produksi_ton', use_log=True)
    res_simple = run_regression(
        'Nilai vs Volume (Raw-Simple)',
        PROCESSED_DIR / 'reg_nilai_volume_clean.parquet',
        'x_volume_ton', 'y_nilai_rp_juta', use_log=False)

    all_res = [r for r in [res_utama, res_rtp, res_simple] if r is not None]
    eval_all = pd.concat([r['res_df'] for r in all_res], ignore_index=True)
    eval_all.to_csv(REPORT_DIR / 'regression_eval.csv', index=False)

    return {'utama': res_utama, 'rtp': res_rtp, 'simple': res_simple, 'eval_all': eval_all}