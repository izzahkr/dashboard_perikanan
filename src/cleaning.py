import re
import numpy as np
import pandas as pd
from pathlib import Path
import os
from .config import RAW_DIR, PROCESSED_DIR, PROVINSI_TARGET, KOMODITAS_SINONIM, JENIS_BUDIDAYA_STD

def parse_number(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    if s in {"-", "–", "—", ""}:
        return np.nan
    s = re.sub(r"\(\*\)", "", s).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return np.nan

def norm_kab(s):
    if pd.isna(s):
        return s
    s = str(s).upper().strip()
    s = re.sub(r"^(KABUPATEN|KAB\.?)\s+", "", s)
    s = re.sub(r"^(KOTA|KOTAMADYA)\s+", "KOTA ", s)
    return s.title()

def norm_komoditas(s):
    if pd.isna(s):
        return np.nan
    s = str(s).upper().strip()
    return KOMODITAS_SINONIM.get(s, s)

def norm_budidaya(s):
    if pd.isna(s):
        return np.nan
    s = str(s).upper().strip()
    return JENIS_BUDIDAYA_STD.get(s, s)

def load_opendata_long(prefix, metrik, config):
    frames = []
    for f in sorted(RAW_DIR.glob(f"{prefix}*.xlsx")):
        df = pd.read_excel(f); df["source_file"] = f.name; frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)

    df["kabupaten"]      = df["nama_kabupaten_kota"].map(norm_kab)
    df["jenis_budidaya"] = df["kategori"].map(norm_budidaya)
    df["nilai"]          = df["jumlah"].map(parse_number)
    df["tahun"]          = pd.to_numeric(df["tahun"], errors="coerce").astype("Int64")
    df["metrik"]         = metrik
    df["sumber"]         = prefix.split()[0].lower()
    df["is_missing_year"] = False
    df["is_stale"]        = False
    df["is_aggregate_row"] = (df["kode_kabupaten_kota"].astype(str) == "0")
    df["is_suspect_scale"] = False

    if metrik == "luas_lahan_ha":
        m = (df["tahun"] == df["tahun"].max()) & (df["nilai"].fillna(0) == 0)
        df.loc[m, "is_missing_year"] = True
        df.loc[m, "nilai"] = np.nan
        df["is_suspect_scale"] = df["nilai"] > config["suspect_scale_luas_ha"]
    if metrik == "rtp":
        g = df.groupby(["kabupaten", "jenis_budidaya"])["nilai"]
        df["is_stale"] = (g.transform("nunique") == 1) & (g.transform("count") >= 3)
        df["is_suspect_scale"] = df["nilai"] > config["suspect_scale_rtp"]
    if metrik == "produksi_ton":
        df["is_suspect_scale"] = df["nilai"] > config["suspect_scale_produksi_ton"]

    return df[["tahun","kabupaten","jenis_budidaya","metrik","nilai","satuan",
               "sumber","source_file","is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]]

def load_bps_kegiatan():
    frames = []
    for f in sorted(RAW_DIR.glob("Produksi Perikanan Budidaya Menurut KabupatenKota dan Jenis Kegiatan*.xlsx")):
        df = pd.read_excel(f); df["source_file"] = f.name; frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["kabupaten"] = df["Kabupaten/Kota"].map(norm_kab)
    df = df[~df["Kabupaten/Kota"].astype(str).str.upper().isin(
        {"JAWA TIMUR","KETERANGAN","ANGKA TETAP","-","NAN"})]

    col_map = {}
    for c in df.columns:
        cu = str(c).upper()
        if "PEMBESARAN" in cu:   col_map[c] = ("pembesaran", "produksi_ton")
        elif "PEMBENIHAN" in cu: col_map[c] = ("pembenihan", "volume_ribu_ekor")
        elif "IKAN HIAS" in cu:  col_map[c] = ("ikan_hias", "volume_ekor")

    long = []
    for c, (keg, met) in col_map.items():
        tmp = df[["kabupaten","source_file"]].copy()
        tmp["nilai"] = df[c].map(parse_number)
        tmp["kegiatan"] = keg; tmp["metrik"] = met; tmp["satuan"] = "mixed"
        long.append(tmp)
    if not long:
        return pd.DataFrame()

    out = pd.concat(long, ignore_index=True)
    out["tahun"]  = out["source_file"].str.extract(r"(\d{4})").astype(int)
    out["sumber"] = "bps_kegiatan"
    for f in ["is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]:
        out[f] = False
    return out[["tahun","kabupaten","kegiatan","metrik","nilai","satuan",
                "sumber","source_file","is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]]

def load_bps_nilai_wide():
    frames = []
    for f in sorted(RAW_DIR.glob("Volume Produksi dan Nilai Produksi Perikanan Budidaya Menurut KabupatenKota*.xlsx")):
        df = pd.read_excel(f); df["source_file"] = f.name; frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["kabupaten"] = df["Kabupaten/Kota"].map(norm_kab)
    df = df[~df["Kabupaten/Kota"].astype(str).str.upper().isin(
        {"JAWA TIMUR","KETERANGAN","-","NAN"})]

    long = []
    for c in df.columns:
        if c in {"Kabupaten/Kota","kabupaten","source_file"}:
            continue
        cu = str(c).upper()
        jb = next((v for k,v in JENIS_BUDIDAYA_STD.items() if k in cu), None)
        if jb is None or "JUMLAH" in cu: continue
        met = "nilai_rp" if "NILAI" in cu else ("produksi_kg" if ("PRODUKSI" in cu or "VOLUME" in cu) else None)
        if met is None: continue
        tmp = df[["kabupaten","source_file"]].copy()
        tmp["nilai"] = df[c].map(parse_number)
        tmp["jenis_budidaya"] = jb; tmp["metrik"] = met
        tmp["satuan"] = "kg" if met == "produksi_kg" else "Rp"
        long.append(tmp)

    out = pd.concat(long, ignore_index=True)
    out["tahun"]  = out["source_file"].str.extract(r"(\d{4})").astype(int)
    out["sumber"] = "bps_nilai"
    for f in ["is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]:
        out[f] = False
    return out[["tahun","kabupaten","jenis_budidaya","metrik","nilai","satuan",
                "sumber","source_file","is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]]

def load_pembudidaya():
    frames = []
    for f in sorted(RAW_DIR.glob("Pembudidaya Ikan*.xlsx")):
        df = pd.read_excel(f); df["source_file"] = f.name; frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["kabupaten"] = df["Kabupaten / Kota"].map(norm_kab)
    df["tahun"]     = pd.to_numeric(df["Tahun"], errors="coerce").astype("Int64")
    df["metrik"]    = "pembudidaya"
    df["satuan"]    = "orang"
    df["sumber"]    = "pembudidaya"
    df["nilai"]     = df["Jumlah Pembudidaya"].map(parse_number)
    for f in ["is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]:
        df[f] = False
    return df[["tahun","kabupaten","metrik","nilai","satuan","sumber","source_file",
               "is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]]

def _load_kkp(pattern, kegiatan, vol_col, metrik_vol):
    frames = []
    for f in sorted(RAW_DIR.glob(pattern)):
        df = pd.read_excel(f); df["source_file"] = f.name; frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={"Kab / Kota":"kab_raw","Kelompok Ikan":"komoditas_raw"})
    df = df[df["Provinsi"].astype(str).str.upper() == PROVINSI_TARGET]

    df["kabupaten"] = df["kab_raw"].map(norm_kab)
    df["komoditas"] = df["komoditas_raw"].map(norm_komoditas)
    df["tahun"]     = pd.to_numeric(df["Tahun"], errors="coerce").astype("Int64")

    out = []
    for met, col in [("nilai_rp_juta","Nilai (Rp. Juta)"), (metrik_vol, vol_col)]:
        if col not in df.columns: continue
        tmp = df[["tahun","kabupaten","komoditas","source_file"]].copy()
        tmp["nilai"] = df[col].map(parse_number)
        tmp["metrik"] = met
        tmp["satuan"] = "Rp Juta" if met == "nilai_rp_juta" else vol_col
        out.append(tmp)

    res = pd.concat(out, ignore_index=True)
    res["kegiatan"]        = kegiatan
    res["sumber"]          = f"kkp_{kegiatan}"
    res["is_suspect_scale"] = False
    if kegiatan == "pembenihan":
        th_max = res["tahun"].max()
        res.loc[(res["tahun"] == th_max) & (res["metrik"] == "nilai_rp_juta"),
                "is_suspect_scale"] = True
    for f in ["is_missing_year","is_stale","is_aggregate_row"]:
        res[f] = False
    return res[["tahun","kabupaten","kegiatan","komoditas","metrik","nilai","satuan",
                "sumber","source_file","is_missing_year","is_stale","is_aggregate_row","is_suspect_scale"]]

def build_fact(config) -> pd.DataFrame:
    parts = []
    parts.append(load_opendata_long("Jumlah Produksi Perikanan Budidaya Berdasarkan Jenis Budidaya","produksi_ton",config))
    parts.append(load_opendata_long("Jumlah RTP (Rumah Tangga Perikanan)","rtp",config))
    parts.append(load_opendata_long("Luas Bersih Lahan Perikanan Budidaya Berdasarkan Jenis Budidaya","luas_lahan_ha",config))
    parts.append(load_bps_kegiatan())
    parts.append(load_bps_nilai_wide())
    parts.append(_load_kkp("Produksi Perikanan Budidaya Ikan Hias*.xlsx","ikan_hias","Volume (Ekor)","volume_ekor"))
    parts.append(_load_kkp("Produksi Perikanan Budidaya Pembenihan*.xlsx","pembenihan","Volume (Ribu Ekor)","volume_ribu_ekor"))
    parts.append(_load_kkp("Produksi Perikanan Budidaya Pembesaran*.xlsx","pembesaran","Volume (ton)","produksi_ton"))
    parts.append(load_pembudidaya())

    fact = pd.concat([p for p in parts if not p.empty], ignore_index=True)
    fact = fact[~fact["is_aggregate_row"]].drop(columns=["is_aggregate_row"])
    fact.to_parquet(PROCESSED_DIR / "fact_budidaya.parquet", index=False)
    return fact