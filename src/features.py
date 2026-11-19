import numpy as np
import pandas as pd
from pathlib import Path
from .config import PROCESSED_DIR

FITUR_NUM = ["produksi_ton", "nilai_rp_juta", "rtp", "pembudidaya",
             "luas_lahan_ha", "total_pembesaran"]

def build_features_model(fact: pd.DataFrame) -> pd.DataFrame:
    f = fact[fact["tahun"].notna()].copy()
    f = f[(~f["is_suspect_scale"]) & (~f["is_missing_year"])]

    prod = (f[(f["sumber"]=="jumlah") & (f["metrik"]=="produksi_ton")]
            .groupby(["kabupaten","tahun"])["nilai"].sum(min_count=1).rename("produksi_ton"))
    rtp = (f[f["metrik"]=="rtp"]
           .groupby(["kabupaten","tahun"])["nilai"].sum(min_count=1).rename("rtp"))
    pemb = (f[f["metrik"]=="pembudidaya"]
            .groupby(["kabupaten","tahun"])["nilai"].sum(min_count=1).rename("pembudidaya"))
    luas = (f[f["metrik"]=="luas_lahan_ha"]
            .groupby(["kabupaten","tahun"])["nilai"].sum(min_count=1).rename("luas_lahan_ha"))

    feat = pd.concat([prod, rtp, pemb, luas], axis=1).reset_index()

    pemb2 = f[(f["kegiatan"] == "pembesaran") & (f["metrik"] == "produksi_ton")]
    base = (pemb2.groupby(["kabupaten","tahun"])["nilai"]
            .sum().rename("total_pembesaran").reset_index())
    feat = feat.merge(base, on=["kabupaten","tahun"], how="left")

    if len(pemb2) > 0:
        share_df = (pemb2.groupby(["kabupaten","tahun"])["nilai"]
                    .sum().rename("total_pembesaran_check").reset_index())
        share_df = share_df.set_index(["kabupaten","tahun"])
        for kom in ["RUMPUT LAUT","UDANG","BANDENG","LELE","NILA","GURAMI","PATIN"]:
            s = (pemb2[pemb2["komoditas"] == kom]
                 .groupby(["kabupaten","tahun"])["nilai"].sum()
                 .rename(f"share_{kom.lower().replace(' ','_')}"))
            share_df = share_df.join(s, how="left")
        share_df = share_df.drop(columns=["total_pembesaran_check"])
        share_df = share_df.fillna(0)
        share_cols = [c for c in share_df.columns if c.startswith("share_")]
        total_series = feat.set_index(["kabupaten","tahun"])["total_pembesaran"]
        for c in share_cols:
            share_df[c] = share_df[c] / total_series.replace(0, np.nan)
        feat = feat.merge(share_df.reset_index(), on=["kabupaten","tahun"], how="left")

    nilai = (f[(f["metrik"]=="nilai_rp") & (f["sumber"]=="bps_nilai")]
             .groupby(["kabupaten","tahun"])["nilai"].sum(min_count=1).div(1e6)
             .rename("nilai_rp_juta"))
    feat = feat.merge(nilai.reset_index(), on=["kabupaten","tahun"], how="left")

    feat = feat[feat["tahun"].between(2020, 2024)].copy()
    for c in FITUR_NUM:
        if c in feat.columns:
            lo, hi = feat[c].quantile([0.01, 0.99])
            feat[c] = feat[c].clip(lo, hi)

    feat.to_parquet(PROCESSED_DIR / "features_model.parquet", index=False)
    return feat