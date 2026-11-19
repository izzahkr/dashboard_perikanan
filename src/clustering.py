import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
import joblib
from .config import PROCESSED_DIR, MODEL_DIR, REPORT_DIR

FITUR = ['produksi_ton', 'rtp', 'pembudidaya', 'luas_lahan_ha', 'total_pembesaran']
RANDOM_STATE = 42

def run_clustering(df: pd.DataFrame = None) -> dict:
    if df is None:
        df = pd.read_parquet(PROCESSED_DIR / 'features_model.parquet')

    df_model = df.dropna(subset=FITUR).copy()
    X_scaled = StandardScaler().fit_transform(df_model[FITUR])
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)

    hasil = []
    for k in range(2, 8):
        km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE)
        labels = km.fit_predict(X_pca)
        hasil.append({
            'k': k,
            'inertia': km.inertia_,
            'silhouette': silhouette_score(X_pca, labels),
            'davies_bouldin': davies_bouldin_score(X_pca, labels)
        })

    eval_df = pd.DataFrame(hasil)
    k_opt = int(eval_df.loc[eval_df['silhouette'].idxmax(), 'k'])
    sil_opt = eval_df['silhouette'].max()

    kmeans = KMeans(n_clusters=k_opt, n_init=50, random_state=RANDOM_STATE)
    labels = kmeans.fit_predict(X_pca)
    df_model['klaster_raw'] = labels

    profil_raw = df_model.groupby('klaster_raw')[FITUR].mean()
    urutan = profil_raw['produksi_ton'].sort_values().index.tolist()
    map_urut = {kl: i for i, kl in enumerate(urutan)}
    df_model['klaster'] = df_model['klaster_raw'].map(map_urut)

    profil = df_model.groupby('klaster')[FITUR].mean()
    profil['n_kabupaten_tahun'] = df_model['klaster'].value_counts().sort_index()
    profil['n_kabupaten_unik'] = df_model.groupby('klaster')['kabupaten'].nunique()

    def label_from_profile(row):
        if row['total_pembesaran'] > 500_000:
            return 'Spesialis Kepulauan (Rumput Laut)'
        elif row['produksi_ton'] > 30_000:
            return 'Raksasa Budidaya (Tinggi)'
        else:
            return 'Skala Menengah – Kabupaten Umum'

    label_map = {kl: label_from_profile(profil.loc[kl]) for kl in profil.index}
    df_model['label_klaster'] = df_model['klaster'].map(label_map)

    joblib.dump(kmeans, MODEL_DIR / 'kmeans.pkl')
    cols_keep = ['kabupaten', 'tahun', 'klaster', 'label_klaster'] + FITUR
    df_model[cols_keep].to_parquet(REPORT_DIR / 'cluster_assignments.parquet', index=False)
    profil.to_csv(REPORT_DIR / 'cluster_profile.csv')
    eval_df.to_csv(REPORT_DIR / 'clustering_eval.csv', index=False)

    return {
        'k_opt': k_opt,
        'silhouette': sil_opt,
        'eval_df': eval_df,
        'profil': profil,
        'label_map': label_map,
        'df': df_model,
        'kmeans': kmeans,
        'pca': pca,
        'X_pca': X_pca,
    }
