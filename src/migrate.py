import pandas as pd
from pathlib import Path
from .config import PROCESSED_DIR, REPORT_DIR
from .db import init_schema, upsert_raw, upsert_fact, upsert_features, upsert_cluster, save_model_version

def main():
    print('='*60)
    print('  MIGRASI PARQUET -> POSTGRESQL')
    print('='*60)

    print('\n[1/4] Init schema...')
    init_schema()

    print('\n[2/4] Migrasi fact_budidaya...')
    fact_path = PROCESSED_DIR / 'fact_budidaya.parquet'
    if fact_path.exists():
        fact = pd.read_parquet(fact_path)
        upsert_fact(fact)
    print('\n[2b/4] Migrasi raw_budidaya...')
    if fact_path.exists():
        fact = pd.read_parquet(fact_path)
        upsert_raw(fact, batch_name='initial_migration')
    else:
        print('  ⚠️ fact_budidaya.parquet tidak ditemukan.')

    print('\n[3/4] Migrasi features_model...')
    feat_path = PROCESSED_DIR / 'features_model.parquet'
    if feat_path.exists():
        feat = pd.read_parquet(feat_path)
        upsert_features(feat)
    else:
        print('  ⚠️ features_model.parquet tidak ditemukan.')
    print('\n[4/4] Migrasi cluster_assignments...')
    cluster_path = REPORT_DIR / 'cluster_assignments.parquet'
    if cluster_path.exists():
        cluster = pd.read_parquet(cluster_path)
        upsert_cluster(cluster)
    else:
        print('  ⚠️ cluster_assignments.parquet tidak ditemukan.')

    try:
        eval_path = REPORT_DIR / 'regression_eval.csv'
        if eval_path.exists():
            ev = pd.read_csv(eval_path)
            # Ambil model dengan CV R² tertinggi (tanpa perlu is_best)
            best = ev.sort_values('cv_r2_mean', ascending=False).iloc[0]
            save_model_version(
                data_hash='initial_migration',
                model_name=f"{best['dataset']} — {best['model']}",
                cv_r2=float(best['cv_r2_mean']),
                notes='Initial migration from parquet.'
            )
    except Exception as e:
        print('  ⚠️ Tidak bisa catat model_versions:', e)

    print('\n' + '='*60)
    print('  ✓ MIGRASI SELESAI')
    print('='*60)


if __name__ == '__main__':
    main()