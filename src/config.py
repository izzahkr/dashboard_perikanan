from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "Data" / "raw"
PROCESSED_DIR = ROOT / "Data" / "processed"
OUTPUT_DIR = ROOT / "Output"
REPORT_DIR = OUTPUT_DIR / "reports"
MODEL_DIR = OUTPUT_DIR / "models"
FIG_DIR = OUTPUT_DIR / "figures"

for d in [PROCESSED_DIR, REPORT_DIR, MODEL_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PROVINSI_TARGET = "JAWA TIMUR"

# Link sumber data
SUMBER = {
    "produksi_jenis_budidaya": "https://opendata.jatimprov.go.id/dataset/jumlah-produksi-perikanan-budidaya-berdasarkan-jenis-budidaya",
    "rtp": "https://opendata.jatimprov.go.id/dataset/jumlah-rtp-rumah-tangga-perikanan--perusahaan-perikanan-pp-berdasarkan-jenis-budidaya",
    "luas_bersih": "https://opendata.jatimprov.go.id/dataset/luas-bersih-lahan-perikanan-budidaya-berdasarkan-jenis-budidaya",
    "luas_lahan_kkp": "https://portaldata.kkp.go.id/portals/data-statistik/lahan_budidaya/summary",
    "pembudidaya": "https://portaldata.kkp.go.id/portals/data-statistik/budidaya_ikan/summary",
    "ikan_hias": "https://portaldata.kkp.go.id/datainsight/produksi-ikan-hias",
    "pembenihan": "https://portaldata.kkp.go.id/datainsight/produksi-ikan-pembenihan",
    "pembesaran": "https://portaldata.kkp.go.id/datainsight/produksi-ikan-budidaya",
    "bps_kegiatan": "https://jatim.bps.go.id/id/statistics-table/3/WjFab0sxVjVkR3hOVUdjMWNIRnNkbWd3ZWl0bWR6MDkjMw==/produksi-perikanan-budidaya-menurut-kabupaten-kota-dan-jenis-kegiatan-di-provinsi-jawa-timur--2021.html",
    "bps_nilai": "https://jatim.bps.go.id/id/statistics-table/3/Wldsb1EyRktNMDl2VUVSalEzVllaM2xQWTFGTmR6MDkjMw%3D%3D/volume-produksi-dan-nilai-produksi-perikanan-budidaya-menurut-kabupaten-kota-dan-jenis-budidaya-di-provinsi-jawa-timur--2023.html",
}

KOMODITAS_SINONIM = {
    "GURAME; GURAMI": "GURAMI",
    "GURAME": "GURAMI",
    "MAS KOKI": "MAS",
    "UDANG VANAME": "UDANG",
    "LOBSTER PASIR": "LOBSTER AIR LAUT",
    "RUMPUT LAUT EUCHEUMA COTTONII": "RUMPUT LAUT",
    "IKAN LAINNYA": "LAINNYA",
    "BAWAL AIR TAWAR": "BAWAL",
    "LALAWAK": "TAWES",
}

JENIS_BUDIDAYA_STD = {
    "JARING APUNG": "JARING APUNG",
    "JARING APUNG LAUT": "JARING APUNG",
    "JARING APUNG TAWAR": "JARING APUNG",
    "KARAMBA": "KARAMBA",
    "KOLAM": "KOLAM",
    "KOLAM AIR TENANG": "KOLAM",
    "KOLAM AIR DERAS": "KOLAM",
    "LAUT": "LAUT",
    "LAUT LAINNYA": "LAUT",
    "MINA PADI": "MINA PADI",
    "MINAPADI SAWAH": "MINA PADI",
    "MINAPADI (SAWAH)": "MINA PADI",
    "TAMBAK": "TAMBAK",
    "TAMBAK INTENSIF": "TAMBAK",
    "TAMBAK SEMI INTENSIF": "TAMBAK",
    "TAMBAK SEMI INSENTIF": "TAMBAK",
    "TAMBAK SEDERHANA": "TAMBAK",
    "RUMPUT LAUT": "RUMPUT LAUT",
    "JARING TANCAP TAWAR": "JARING TANCAP",
}

# Parameter preprocessing dan pemodelan
CONFIG = {
    "coverage_threshold": 0.90,
    "metric_coverage_min": 0.50,
    "min_metrik_lengkap": 3,
    "min_samples_regression": 10,
    "min_kab_clustering": 10,
    "label_top_share_min": 0.20,
    "outlier_mad_k": 5.0,
    "outlier_iqr_k_fallback": 1.5,
    "suspect_scale_produksi_ton": 100_000,
    "suspect_scale_luas_ha": 100_000,
    "suspect_scale_rtp": 50_000,
}

import os

def _db_config():
    if os.getenv("PGHOST"):
        return {
            "host": os.environ["PGHOST"],
            "port": int(os.getenv("PGPORT", 5432)),
            "dbname": os.environ["PGDATABASE"],
            "user": os.environ["PGUSER"],
            "password": os.environ["PGPASSWORD"],
        }
    try:
        import streamlit as st
        return dict(st.secrets["db"])
    except Exception:
        return {"host": "localhost", "port": 5432, "dbname": "perikanan_jatim",
                "user": "postgres", "password": ""}

DB_CONFIG = _db_config()