from pathlib import Path
import pandas as pd
from .config import PROCESSED_DIR, MODEL_DIR, REPORT_DIR, FIG_DIR
from .cleaning import build_fact
from .features import build_features_model
from .clustering import run_clustering
from .regression import run_all_regression

CONFIG = {
    "coverage_threshold": 0.90,
    "metric_coverage_min": 0.50,
    "min_metrik_lengkap": 3,
    "outlier_mad_k": 5.0,
    "outlier_iqr_k_fallback": 1.5,
    "suspect_scale_produksi_ton": 100_000,
    "suspect_scale_luas_ha": 100_000,
    "suspect_scale_rtp": 50_000,
}

def run_all():
    print('=== STEP 1: Cleaning & Integrasi ===')
    fact = build_fact(CONFIG)
    print(f'  fact shape: {fact.shape}')

    print('\n=== STEP 2: Buat Fitur ===')
    feat = build_features_model(fact)
    print(f'  features shape: {feat.shape}')

    print('\n=== STEP 3: Clustering ===')
    clust = run_clustering(feat)
    print(f'  k optimal: {clust["k_opt"]}, silhouette: {clust["silhouette"]:.4f}')
    for kl, lbl in clust['label_map'].items():
        n = (clust['df']['klaster'] == kl).sum()
        print(f'  K{kl} ({lbl}): {n} baris')

    print('\n=== STEP 4: Regresi ===')
    reg = run_all_regression()
    for key in ['utama', 'rtp', 'simple']:
        r = reg[key]
        if r:
            br = r['best_row']
            print(f'  {r["name"]}: CV R² = {br["cv_r2_mean"]:.4f}')

    print('\n=== SELESAI ===')
    return {'fact': fact, 'features': feat, 'clustering': clust, 'regression': reg}

if __name__ == '__main__':
    run_all()