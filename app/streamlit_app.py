import re
import sys
import json
from pathlib import Path
import streamlit.components.v1 as components

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in (HERE, HERE.parent) if (p / "src").exists()), HERE.parent)
sys.path.insert(0, str(ROOT))
try:
    from src.config import SUMBER
except Exception:
    SUMBER = {}

st.set_page_config(page_title="Dashboard Perikanan Jatim", page_icon="", layout="wide")

# ============================================================ KONSTANTA
METS = ["produksi_ton", "nilai_rp_juta", "rtp", "pembudidaya", "luas_lahan_ha", "total_pembesaran"]
LABEL = {"produksi_ton": "Produksi menurut Media (ton)", "nilai_rp_juta": "Nilai Produksi (Rp juta)",
         "rtp": "Rumah Tangga Perikanan", "pembudidaya": "Pembudidaya (orang)",
         "luas_lahan_ha": "Luas Lahan (ha)", "total_pembesaran": "Produksi Budidaya (ton)"}
SRC_KEYS = {"produksi_ton": ["produksi_jenis_budidaya"], "nilai_rp_juta": ["bps_nilai"], "rtp": ["rtp"],
            "pembudidaya": ["pembudidaya"], "luas_lahan_ha": ["luas_bersih", "luas_lahan_kkp"],
            "total_pembesaran": ["pembesaran", "bps_kegiatan"]}
SRC_NAME = {"produksi_jenis_budidaya": "OpenData Jatim - Produksi", "rtp": "OpenData Jatim - RTP",
            "luas_bersih": "OpenData Jatim - Luas Lahan", "luas_lahan_kkp": "KKP - Lahan Budidaya",
            "pembudidaya": "KKP - Pembudidaya", "ikan_hias": "KKP - Ikan Hias", "pembenihan": "KKP - Pembenihan",
            "pembesaran": "KKP - Pembesaran", "bps_kegiatan": "BPS Jatim - Jenis Kegiatan",
            "bps_nilai": "BPS Jatim - Volume & Nilai"}
FACT_COLS = ["tahun", "kabupaten", "jenis_budidaya", "metrik", "nilai", "satuan", "sumber",
             "kegiatan", "komoditas", "is_suspect_scale", "is_missing_year", "is_stale"]
FLOW = ["produksi_ton", "nilai_rp_juta", "total_pembesaran"]
STOCK = ["rtp", "pembudidaya", "luas_lahan_ha"]
FIT_KL = ["produksi_ton", "rtp", "pembudidaya", "luas_lahan_ha", "total_pembesaran"]

KOORD = {
    "Pacitan": (-8.19, 111.10), "Ponorogo": (-7.87, 111.47), "Trenggalek": (-8.05, 111.71),
    "Tulungagung": (-8.07, 111.90), "Blitar": (-8.12, 112.20), "Kediri": (-7.82, 112.01),
    "Malang": (-8.13, 112.57), "Lumajang": (-8.13, 113.22), "Jember": (-8.17, 113.70),
    "Banyuwangi": (-8.22, 114.37), "Bondowoso": (-7.91, 113.82), "Situbondo": (-7.71, 114.01),
    "Probolinggo": (-7.82, 113.22), "Pasuruan": (-7.72, 112.90), "Sidoarjo": (-7.45, 112.72),
    "Mojokerto": (-7.55, 112.45), "Jombang": (-7.55, 112.23), "Nganjuk": (-7.60, 111.90),
    "Madiun": (-7.60, 111.65), "Magetan": (-7.65, 111.33), "Ngawi": (-7.40, 111.45),
    "Bojonegoro": (-7.15, 111.88), "Tuban": (-6.90, 112.05), "Lamongan": (-7.12, 112.42),
    "Gresik": (-7.16, 112.65), "Bangkalan": (-7.05, 112.74), "Sampang": (-7.19, 113.24),
    "Pamekasan": (-7.16, 113.48), "Sumenep": (-7.01, 113.86),
    "Kota Kediri": (-7.85, 112.02), "Kota Blitar": (-8.10, 112.17), "Kota Malang": (-7.98, 112.63),
    "Kota Probolinggo": (-7.75, 113.22), "Kota Pasuruan": (-7.64, 112.90), "Kota Mojokerto": (-7.47, 112.43),
    "Kota Madiun": (-7.63, 111.52), "Kota Surabaya": (-7.26, 112.75), "Kota Batu": (-7.87, 112.52),
}

PRETTY = {
    "kabupaten": "Kabupaten/Kota", "label_klaster": "Label Klaster", "komoditas": "Komoditas",
    "produksi_ton": "Produksi (Ton)", "nilai_rp_juta": "Nilai (Rp Juta)", "rtp": "RTP",
    "pembudidaya": "Pembudidaya", "luas_lahan_ha": "Luas Lahan (Ha)", "total_pembesaran": "Total Pembesaran",
    "harga_per_kg": "Harga per Kg", "jenis_budidaya": "Jenis Budidaya", "pc1": "PC1", "pc2": "PC2",
}

SEQ_OCEAN = ["#CAF0F8", "#90E0EF", "#48CAE4", "#00B4D8", "#0077B6", "#023E8A", "#03045E"]
SEQ_SUNSET = ["#FFF3B0", "#FFD166", "#FFB703", "#FB8500", "#E85D04", "#D62828"]
CAT_LIVELY = ["#0077B6", "#F4A261", "#2A9D8F", "#E76F51", "#8338EC", "#FFBE0B", "#3A86FF", "#FB5607"]
DIV_BALANCE = ["#0077B6", "#48CAE4", "#FFFFFF", "#F4A261", "#D62828"]

px.defaults.color_discrete_sequence = CAT_LIVELY
px.defaults.color_continuous_scale = SEQ_OCEAN
MODE_UPSERT = "Tambah/perbarui data lama (UPSERT)"
MODE_REPLACE = "Ganti seluruh data (hanya upload)"
PAGES = ["Beranda Utama", "Peta", "Tipologi Wilayah", "Komoditas & Nilai", "Profil Wilayah",
         "Analisis Regresi", "Upload Data", "Metadata"]
PAGE_ICONS = ["wave", "map", "grid", "fish", "pin", "chart", "upload", "book"]
HERO = [("Ringkasan Perikanan Budidaya Jawa Timur", "Ringkasan umum kondisi perikanan budidaya melalui indikator utama, perkembangan produksi, dan kontribusi wilayah di Jawa Timur."),
        ("Peta Sebaran Wilayah", "Menampilkan persebaran produksi, nilai ekonomi, dan karakteristik perikanan budidaya pada setiap kabupaten dan kota di Jawa Timur."),
        ("Tipologi Wilayah", "Mengelompokkan kabupaten dan kota di Jawa Timur berdasarkan kemiripan karakteristik dan indikator perikanan budidaya."),
        ("Komoditas & Nilai Produksi", "Menampilkan komoditas perikanan budidaya, volume produksi, serta nilai ekonomi berdasarkan wilayah di Jawa Timur."),
        ("Profil & Perbandingan Wilayah", "Menelusuri karakteristik wilayah dan membandingkan capaian indikator perikanan budidaya antarwilayah di Jawa Timur."),
        ("Analisis Produksi dan Simulasi Skenario", "Menganalisis keterkaitan antarindikator produksi serta mengeksplorasi dampak perubahan melalui simulasi skenario."),
        ("Pembaruan Data", "Unggah data resmi terbaru dan pantau proses integrasinya ke dalam dashboard."),
        ("Metadata & Transparansi Data", "Mengenal sumber, definisi, cakupan, dan proses pengolahan data yang digunakan dalam dashboard.")]
S = st.session_state
for k, v in [("ups", []), ("mode", MODE_UPSERT), ("flag", False), ("up_n", 0), ("entered", False), ("theme", "light")]:
    S.setdefault(k, v)

THEMES = {
    "light": {
        "app_bg": "#F5F9FC", "card_bg": "#FFFFFF", "card_border": "#DBE9F0", "text": "#17324D", "text_muted": "#566E82",
        "heading": "#072F52", "accent": "#0077A8", "grid": "#E3EEF4", "axis_line": "#B7CCD9",
        "insight_bg": "#EAF9FB", "insight_br": "#17A2BE", "insight_bd": "#B9E7EE", "insight_tx": "#19556B",
        "warn_bg": "#FFF1E8", "warn_br": "#FF7A59", "warn_tx": "#8A3B1D",
        "soft": "#EEF6FA", "card2": "#F8FBFD", "ic_bg": "#DDF3F8", "ic_fg": "#007EA2", "btn_tx": "#FFFFFF",
        "sidebar_bg": "linear-gradient(180deg,#032F51 0%,#034E74 60%,#026B8E 100%)", "sidebar_tx": "#FFFFFF",
        "input_bg": "#F8FBFD", "input_bd": "#DBE9F0", "input_tx": "#17324D", "table_bg": "#FFFFFF", "table_tx": "#17324D",
        "up": "#159468", "down": "#D6453D", "na": "#7C93A4", "plotly": "plotly_white",
    },
    "dark": {
        "app_bg": "#08111F", "card_bg": "#101F31", "card_border": "#203B54", "text": "#E8F1F8", "text_muted": "#8EA6BB",
        "heading": "#F3F8FC", "accent": "#45C5DF", "grid": "#1B3248", "axis_line": "#35546E",
        "insight_bg": "#0E2D3B", "insight_br": "#45C5DF", "insight_bd": "#195063", "insight_tx": "#C4EAF0",
        "warn_bg": "#3A1F14", "warn_br": "#FF7A59", "warn_tx": "#FFD6C9",
        "soft": "#0C1828", "card2": "#13263B", "ic_bg": "#12354A", "ic_fg": "#66D5E5", "btn_tx": "#042F50",
        "sidebar_bg": "linear-gradient(180deg,#041526 0%,#062B45 60%,#064A6A 100%)", "sidebar_tx": "#E8F1F8",
        "input_bg": "#13263B", "input_bd": "#203B54", "input_tx": "#E8F1F8", "table_bg": "#101F31", "table_tx": "#E8F1F8",
        "up": "#4ADE80", "down": "#F87171", "na": "#7A8FA8", "plotly": "plotly_dark",
    },
}
T = THEMES[S["theme"]]

# ============================================================ IKON (SVG)
_IC = {
    "wave": '<path d="M3 8c2.2-2 4.3-2 6.5 0s4.3 2 6.5 0 4.3-2 5 0"/><path d="M3 14c2.2-2 4.3-2 6.5 0s4.3 2 6.5 0 4.3-2 5 0"/><path d="M5 19h14"/>',
    "map": '<path d="m3 6 5-3 8 3 5-3v15l-5 3-8-3-5 3Z"/><path d="M8 3v15M16 6v15"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "fish": '<path d="M5 12c3-5 8-6 13-2l3-3v10l-3-3c-5 4-10 3-13-2Z"/><circle cx="15" cy="11" r=".7" fill="currentColor"/><path d="M5 12 2 9v6Z"/>',
    "pin": '<path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "upload": '<path d="M12 16V3m0 0L7 8m5-5 5 5"/><path d="M4 14v6h16v-6"/>',
    "book": '<path d="M4 4h6a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H4Z"/><path d="M20 4h-4a3 3 0 0 0-3 3v13a3 3 0 0 1 3-3h4Z"/>',
    "arrow": '<path d="M5 12h14M14 7l5 5-5 5"/>',
    "filter": '<path d="M4 5h16l-6 7v6l-4 2v-8Z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "alert": '<path d="M12 3 2 21h20Z"/><path d="M12 10v5M12 18h.01"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
}


def svg(name, size=20):
    return (f'<svg class="ic" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_IC[name]}</svg>')


def _mask(name):
    from urllib.parse import quote
    raw = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.8" '
           f'stroke-linecap="round" stroke-linejoin="round">{_IC[name].replace("currentColor", "black")}</svg>')
    return f'url("data:image/svg+xml,{quote(raw)}")'


def theme_css(css):
    """Isi token __NAMA__ dengan warna tema aktif (hindari kurung kurawal ganda di f-string)."""
    return re.sub(r"__([A-Z0-9_]+)__", lambda m: T.get(m.group(1).lower(), m.group(0)), css)


# ============================================================ STYLE
_NAV_ICONS = "\n".join(
    f'[data-testid="stSidebar"] [role="radiogroup"]:has(> label:nth-child(8)) > label:nth-child({i + 1})::before '
    f'{{ -webkit-mask-image: {_mask(n)}; mask-image: {_mask(n)}; }}' for i, n in enumerate(PAGE_ICONS))

_STYLE = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: __APP_BG__; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stHeader"] svg, [data-testid="stToolbar"] svg { color: __TEXT__ !important; fill: __TEXT__ !important; }
.block-container { max-width: 1680px !important; padding: 3.2rem clamp(1.25rem, 3vw, 3rem) 3rem !important; }
svg.ic { flex: none; vertical-align: middle; }

/* ---------- teks dasar ---------- */
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] > p,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] > ul li,
[data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
[data-testid="stAppViewContainer"] .stText,
[data-testid="stAppViewContainer"] label { color: __TEXT__ !important; }
[data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p { font-size: .8rem; font-weight: 600; }
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"], [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] * { color: __TEXT_MUTED__ !important; font-size: .8rem; }
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] ol li, [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] td,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] th, [data-testid="stAppViewContainer"] [role="radiogroup"] label p,
[data-testid="stAppViewContainer"] [data-testid="stCheckbox"] label p, [data-testid="stAppViewContainer"] [data-testid="stToggle"] label p,
[data-testid="stAppViewContainer"] [data-testid="stSelectbox"] label p, [data-testid="stAppViewContainer"] [data-testid="stNumberInput"] label p,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] em { color: __TEXT__ !important; }
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] code { color: __HEADING__ !important; background: __SOFT__ !important; border-radius: 5px; padding: 1px 6px; }
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] a { color: __ACCENT__ !important; }
[data-testid="stAppViewContainer"] [data-testid="stRadio"] [role="radiogroup"] label > div:first-child { border-color: __ACCENT__ !important; }
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2, [data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4, [data-testid="stAppViewContainer"] h5, [data-testid="stAppViewContainer"] h6,
[data-testid="stAppViewContainer"] strong { color: __HEADING__ !important; }
html { color-scheme: __SCHEME__; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"], [data-testid="stSidebar"] { background: __SIDEBAR_BG__ !important; border-right: none !important; }
section[data-testid="stSidebar"] > div, section[data-testid="stSidebar"] > div > div, [data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div, [data-testid="stSidebar"] [data-testid="stSidebarContent"],
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"], [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stSidebar"] [data-testid="stVerticalBlock"], [data-testid="stSidebar"] [data-testid="stElementContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdown"] { background: transparent !important; background-color: transparent !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { color: __SIDEBAR_TX__ !important; }
.sb-brand { display: flex; align-items: center; gap: 11px; margin: 2px 0 18px; }
.sb-mark { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; color: #fff; flex: none;
    background: linear-gradient(145deg,#00A9CE,#0071A8); box-shadow: 0 7px 18px rgba(0,150,199,.22); }
.sb-mark svg { color: #fff !important; }
.sb-brand b { display: block; font: 700 14px/1.3 Manrope, sans-serif; color: #fff !important; }
.sb-brand small { display: block; font-size: 11px; color: rgba(255,255,255,.65) !important; margin-top: 2px; }
.nav-label { text-transform: uppercase; letter-spacing: .14em; font-size: .62rem; font-weight: 700; color: rgba(255,255,255,.5) !important; margin: 16px 12px 6px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px !important; }
[data-testid="stSidebar"] [role="radiogroup"] > label { background: transparent !important; border: 0 !important; border-radius: 9px !important;
    padding: 0 12px !important; min-height: 43px; width: 100% !important; margin: 0 !important; display: flex !important; align-items: center !important;
    gap: 11px !important; position: relative; cursor: pointer; transition: background .15s ease; }
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child:not([data-testid]) { display: none !important; }
[data-testid="stSidebar"] [role="radiogroup"] > label p, [data-testid="stSidebar"] [role="radiogroup"] > label span,
[data-testid="stSidebar"] [role="radiogroup"] > label div { background: transparent !important; color: rgba(255,255,255,.74) !important;
    font-size: .84rem !important; font-weight: 600 !important; line-height: 1.3 !important; margin: 0 !important; }
[data-testid="stSidebar"] [role="radiogroup"] > label:hover { background: rgba(255,255,255,.08) !important; }
[data-testid="stSidebar"] [role="radiogroup"] > label:hover * { color: #fff !important; }
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(82,213,232,.28), rgba(255,255,255,.11)) !important;
    box-shadow: inset -3px 0 0 #71E0EC; }
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) * { color: #fff !important; }
[data-testid="stSidebar"] [role="radiogroup"]:has(> label:nth-child(8)) > label::before { content: ""; flex: none; width: 19px; height: 19px;
    background: rgba(255,255,255,.74); -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center;
    -webkit-mask-size: contain; mask-size: contain; }
[data-testid="stSidebar"] [role="radiogroup"]:has(> label:nth-child(8)) > label:hover::before,
[data-testid="stSidebar"] [role="radiogroup"]:has(> label:nth-child(8)) > label:has(input:checked)::before { background: #fff; }
__NAV_ICONS__
/* pengalih tema (segmented) */
[data-testid="stSidebar"] [role="radiogroup"]:not(:has(> label:nth-child(3))) { display: grid !important; grid-template-columns: 1fr 1fr; gap: 0 !important;
    padding: 3px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.07); border-radius: 9px; margin-bottom: 4px; }
[data-testid="stSidebar"] [role="radiogroup"]:not(:has(> label:nth-child(3))) > label { min-height: 31px !important; justify-content: center !important;
    padding: 0 !important; border-radius: 6px !important; }
[data-testid="stSidebar"] [role="radiogroup"]:not(:has(> label:nth-child(3))) > label:has(input:checked) { background: #fff !important; box-shadow: 0 2px 8px rgba(0,0,0,.15) !important; }
[data-testid="stSidebar"] [role="radiogroup"]:not(:has(> label:nth-child(3))) > label:has(input:checked) * { color: #064B70 !important; }
.side-status { background: rgba(0,20,40,.22) !important; border: 1px solid rgba(255,255,255,.1) !important; padding: 14px; border-radius: 10px; margin-top: 18px; }
.side-status .ss-h { display: flex; align-items: center; gap: 7px; font-size: .68rem; font-weight: 700; color: #A8F0E3 !important; margin-bottom: 10px; }
.live-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #35D39A; box-shadow: 0 0 0 3px rgba(53,211,154,.13); }
.side-status p { display: flex; justify-content: space-between; gap: 10px; font-size: .7rem; margin: 6px 0 0; color: rgba(255,255,255,.55) !important; }
.side-status p b { color: rgba(255,255,255,.92) !important; font-weight: 700; text-align: right; }
[data-testid="stSidebar"] .stButton > button { background: transparent !important; color: rgba(255,255,255,.8) !important;
    border: 1px solid rgba(255,255,255,.18) !important; font-size: .78rem !important; font-weight: 600 !important; justify-content: flex-start; }
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,.08) !important; }
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stButton button * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-size: .8rem !important; font-weight: 600 !important; }

/* ---------- input ---------- */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
    background-color: __INPUT_BG__ !important; border: 1px solid __INPUT_BD__ !important; border-radius: 8px !important; }
div[data-baseweb="select"] * { color: __INPUT_TX__ !important; }
ul[data-testid="stSelectboxVirtualDropdown"] { background-color: __INPUT_BG__ !important; }
ul[data-testid="stSelectboxVirtualDropdown"] li { color: __INPUT_TX__ !important; }
button[kind="pills"] { background-color: __INPUT_BG__ !important; color: __INPUT_TX__ !important; border: 1px solid __INPUT_BD__ !important; }
button[kind="pills"][aria-selected="true"] { background-color: __ACCENT__ !important; color: __BTN_TX__ !important; }
[data-testid="stAppViewContainer"] .stTextInput input, [data-testid="stAppViewContainer"] .stNumberInput input,
[data-testid="stAppViewContainer"] .stTextArea textarea { background-color: __INPUT_BG__ !important; color: __INPUT_TX__ !important; border: 1px solid __INPUT_BD__ !important; }
[data-testid="stAppViewContainer"] .stMultiSelect span[data-baseweb="tag"] { background-color: __ACCENT__ !important; color: __BTN_TX__ !important; }
[data-testid="stAppViewContainer"] .stMultiSelect span[data-baseweb="tag"] * { color: __BTN_TX__ !important; }
div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul[role="listbox"], div[data-baseweb="menu"] { background-color: __INPUT_BG__ !important; }
div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * { color: __INPUT_TX__ !important; background-color: transparent !important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] li[aria-selected="true"] { background-color: __INSIGHT_BG__ !important; }
[data-testid="stSlider"] [data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stSliderThumbValue"] * { color: #F4744A !important; font-weight: 800; }
[data-testid="stSlider"] [role="slider"] { background-color: #F4744A !important; }
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: __TEXT_MUTED__ !important; }

/* ---------- tombol ---------- */
.stButton > button, .stDownloadButton > button { background: __ACCENT__ !important; color: __BTN_TX__ !important; border: 0 !important;
    border-radius: 10px !important; font-weight: 700 !important; min-height: 2.6rem; }
.stButton > button p, .stDownloadButton > button p { color: inherit !important; font-weight: 700 !important; }
.stButton > button:hover { filter: brightness(1.08); }
.stDownloadButton > button { background: transparent !important; color: __ACCENT__ !important; border: 1px solid __ACCENT__ !important; }
.stDownloadButton > button:hover { background: __INSIGHT_BG__ !important; filter: none; }

/* ---------- kartu, panel, grafik ---------- */
[data-testid="stVerticalBlockBorderWrapper"] { border-color: __CARD_BORDER__ !important; }
[data-testid="stPlotlyChart"] { background: __CARD_BG__; border: 1px solid __CARD_BORDER__; border-radius: 12px; padding: 10px 12px; box-shadow: 0 5px 20px rgba(14,70,95,.035); }
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] { border: 0; box-shadow: none; padding: 0; }
.kpi { background: __CARD_BG__; border: 1px solid __CARD_BORDER__; border-top: 3px solid var(--c,#0077B6); border-radius: 11px; padding: 15px 14px 14px;
    box-shadow: 0 5px 18px rgba(14,72,100,.035); text-align: left; height: 100%; box-sizing: border-box; margin-bottom: 4px; }
.kpi .l { font-size: .68rem; letter-spacing: .04em; text-transform: uppercase; color: __TEXT_MUTED__ !important; font-weight: 700; min-height: 2.5em; line-height: 1.25; }
.kpi .v { font: 800 1.35rem Manrope, sans-serif; color: __HEADING__ !important; margin: 6px 0 4px; }
.kpi .d { font-size: .76rem; font-weight: 600; line-height: 1.5; color: __TEXT__ !important; }
.kpi .d b { color: __HEADING__ !important; font-weight: 800; }
/* baris 6 kartu KPI (Beranda): padat, rapi, tinggi seragam (muat sampai 4 baris teks) */
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi,
[data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi { height: 148px; padding: 12px 14px; display: flex; flex-direction: column; justify-content: center; }
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi > *,
[data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi > * { flex-shrink: 0; }
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi .l,
[data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi .l { min-height: 0; font-size: .66rem; margin: 0; }
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi .v,
[data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi .v { font-size: 1.35rem; margin: 6px 0 5px; }
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi .d,
[data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi .d { font-size: .72rem; line-height: 1.4; font-weight: 500; letter-spacing: -.01em; }
@media (max-width: 1100px) { [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(6)) .kpi,
    [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(6)) .kpi { height: auto; min-height: 148px; } }
.kpi.kc { padding: 12px 14px 10px; }
.kpi.kc .l { min-height: 0; margin-bottom: 2px; }
.kpi.kc .v { font-size: 1.12rem; margin: 3px 0 6px; }
.kpi.kc .d { font-size: .72rem; line-height: 1.45; font-weight: 500; }
[data-testid="stHorizontalBlock"]:not(:has(> [data-testid="stColumn"]:nth-child(4))):not(:has(> [data-testid="column"]:nth-child(4))) { gap: 1.25rem !important; }
.up { color: __UP__ !important; } .down { color: __DOWN__ !important; } .na { color: __NA__ !important; }
[data-testid="stMetric"] { background-color: __CARD_BG__ !important; border: 1px solid __CARD_BORDER__; border-radius: 11px; padding: 15px 16px;
    box-shadow: 0 5px 18px rgba(14,72,100,.035); min-height: 112px; }
[data-testid="stMetricValue"] { color: __HEADING__ !important; font-family: Manrope, sans-serif; font-weight: 800; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: __TEXT_MUTED__ !important; }
.insight, .warn { display: flex; gap: 10px; align-items: flex-start; padding: 11px 14px; border-radius: 8px; margin: 14px 0; font-size: .88rem; line-height: 1.55; }
.insight { background: __INSIGHT_BG__ !important; color: __INSIGHT_TX__ !important; border: 1px solid __INSIGHT_BD__; border-left: 3px solid __INSIGHT_BR__; }
.warn { background: __WARN_BG__ !important; color: __WARN_TX__ !important; border: 1px solid __WARN_BR__; border-left: 3px solid __WARN_BR__; }
.insight *, .warn * { color: inherit !important; }
.ii { flex: none; width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; background: rgba(16,157,185,.12); }
.warn .ii { background: rgba(255,122,89,.16); }
.sumber { font-size: .75rem; color: __TEXT_MUTED__ !important; margin: 8px 2px 24px; text-align: right; line-height: 1.5; }
.sumber a { color: __ACCENT__ !important; font-weight: 600; text-decoration: none; }
[data-testid="stAlert"] { background-color: __INPUT_BG__ !important; border: 1px solid __INPUT_BD__ !important; border-radius: 8px !important; color: __TEXT__ !important; }
[data-testid="stAlert"] * { color: __TEXT__ !important; }
[data-testid="stAlert"] svg { fill: __TEXT__ !important; }
[data-testid="stDataFrame"] { background-color: __TABLE_BG__ !important; border: 1px solid __CARD_BORDER__ !important; border-radius: 10px !important; overflow: hidden !important; }
__DF_DARK__
[data-testid="stFileUploader"], [data-testid="stFileUploader"] > div, [data-testid="stFileUploader"] section, [data-testid="stFileUploaderDropzone"] {
    background-color: __INPUT_BG__ !important; border: 1px dashed __INPUT_BD__ !important; border-radius: 12px !important; color: __INPUT_TX__ !important; }
[data-testid="stFileUploader"] * { color: __INPUT_TX__ !important; }
[data-testid="stFileUploader"] button { background-color: __CARD_BG__ !important; color: __HEADING__ !important; border: 1px solid __INPUT_BD__ !important; }
[data-testid="stFileUploader"] svg { fill: __TEXT_MUTED__ !important; stroke: __TEXT_MUTED__ !important; }
[data-testid="stCode"], [data-testid="stCode"] pre, [data-testid="stCode"] code { background-color: __INPUT_BG__ !important; color: __INPUT_TX__ !important; }

/* ---------- tab & expander ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 4px; }
[data-testid="stTabs"] button[data-baseweb="tab"] { color: __TEXT_MUTED__ !important; background: transparent !important; padding: 11px 16px; }
[data-testid="stTabs"] button[data-baseweb="tab"] p, [data-testid="stTabs"] button[data-baseweb="tab"] div { color: inherit !important; font-weight: 700; font-size: .85rem; }
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { color: __ACCENT__ !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: __ACCENT__ !important; height: 2px; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { background-color: __CARD_BORDER__ !important; }
[data-testid="stExpander"], [data-testid="stExpander"] details { background: __CARD_BG__ !important; border: 1px solid __CARD_BORDER__ !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: __HEADING__ !important; font-weight: 700; }

/* ---------- header halaman standar ---------- */
.ph { display: grid; grid-template-columns: 56px minmax(0,1fr) auto; gap: 20px; align-items: center; width: 100%; box-sizing: border-box;
    padding: 24px 30px; margin: 0 0 26px; border: 1px solid __CARD_BORDER__; border-radius: 16px;
    background: linear-gradient(110deg, __CARD_BG__, __SOFT__); box-shadow: 0 10px 32px rgba(18,75,105,.05); }
.ph-ic { width: 56px; height: 56px; border-radius: 15px; display: flex; align-items: center; justify-content: center; background: __IC_BG__; color: __IC_FG__; }
.ph-ic svg { color: __IC_FG__ !important; width: 26px; height: 26px; }
.ph-eb { font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 800; color: __ACCENT__ !important; margin: 0 0 5px; line-height: 1.2; }
[data-testid="stAppViewContainer"] .ph h1 { font: 800 clamp(1.6rem, 2.4vw, 2.2rem)/1.2 Manrope, sans-serif !important; letter-spacing: -.02em; margin: 0 !important; padding: 0 !important; color: __HEADING__ !important; }
[data-testid="stAppViewContainer"] .ph p { font-size: .95rem; line-height: 1.55; margin: 7px 0 0 !important; max-width: none; color: __TEXT_MUTED__ !important; }
.ph-chip { display: inline-flex; align-items: center; gap: 7px; height: 32px; padding: 0 14px; border: 1px solid __CARD_BORDER__; border-radius: 20px;
    background: __CARD_BG__; white-space: nowrap; font-size: .74rem; font-weight: 600; color: __TEXT_MUTED__ !important; }
@media (max-width: 860px) { .ph { grid-template-columns: 46px minmax(0,1fr); padding: 18px; gap: 14px; } .ph-ic { width: 46px; height: 46px; }
    .ph-chip { grid-column: 1 / -1; justify-self: start; white-space: normal; height: auto; padding: 6px 12px; } }

/* ---------- subjudul, panel, teks pengantar ---------- */
.sh { margin: 28px 0 14px; }
.sh .eb { font-size: .66rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 800; color: __ACCENT__ !important; margin-bottom: 4px; }
[data-testid="stAppViewContainer"] .sh h3 { font: 800 1.2rem/1.3 Manrope, sans-serif !important; margin: 0 !important; padding: 0 !important; color: __HEADING__ !important; }
.sh p { font-size: .88rem; line-height: 1.5; margin: 5px 0 0; color: __TEXT_MUTED__ !important; max-width: 760px; }
.ft { display: flex; align-items: center; gap: 8px; font-size: .78rem; font-weight: 700; color: __HEADING__ !important; margin: 0 0 6px; }
.ft svg { color: __ACCENT__ !important; }
.pt { display: flex; gap: 10px; align-items: flex-start; margin: 0 0 18px; }
.pt > span { flex: none; width: 24px; height: 24px; border-radius: 7px; display: flex; align-items: center; justify-content: center; background: __IC_BG__; color: __IC_FG__ !important; font-weight: 800; font-size: .75rem; }
.pt b { display: block; font: 700 .95rem Manrope, sans-serif; color: __HEADING__ !important; line-height: 1.25; }
.pt small { display: block; font-size: .76rem; color: __TEXT_MUTED__ !important; margin-top: 3px; line-height: 1.35; }
.lead { font-size: .92rem; line-height: 1.55; color: __TEXT_MUTED__ !important; margin: 4px 0 14px; max-width: 820px; }
.lead b { color: __HEADING__ !important; }
.sub { font: 700 .98rem Manrope, sans-serif; color: __HEADING__ !important; margin: 20px 0 8px; }
.sim-h { display: flex; align-items: center; gap: 14px; padding: 20px 22px; margin: 26px 0 14px; border: 1px solid __CARD_BORDER__; border-radius: 14px;
    background: linear-gradient(110deg, __CARD_BG__, __SOFT__); box-shadow: 0 10px 32px rgba(18,75,105,.05); }
.sim-i { flex: none; width: 46px; height: 46px; border-radius: 12px; display: grid; place-items: center; color: #fff; background: linear-gradient(145deg,#008BB2,#035F8B); }
.sim-i svg { color: #fff !important; }
.sim-h .eb { font-size: .64rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 800; color: __ACCENT__ !important; }
.sim-h h3 { font: 800 1.2rem Manrope, sans-serif !important; color: __HEADING__ !important; margin: 3px 0 !important; padding: 0 !important; }
.sim-h p { font-size: .84rem; color: __TEXT_MUTED__ !important; margin: 0; }
.mchip { margin-left: auto; padding: 7px 12px; border-radius: 16px; background: __IC_BG__; color: __IC_FG__ !important; font-size: .72rem; font-weight: 700; white-space: nowrap; }
@media (max-width: 760px) { .sim-h { flex-wrap: wrap; } .mchip { margin-left: 0; } }

/* ---------- tabel ---------- */
.dtbl-w { overflow-x: auto; border: 1px solid __CARD_BORDER__; border-radius: 10px; background: __TABLE_BG__; margin: 6px 0 16px; }
.dtbl-w table { width: 100%; border-collapse: collapse; font-size: .85rem; color: __TABLE_TX__ !important; }
.dtbl-w th { background: __SOFT__ !important; color: __HEADING__ !important; padding: 11px 16px; text-align: left !important; font-weight: 800; font-size: .7rem;
    letter-spacing: .04em; text-transform: uppercase; border-bottom: 1px solid __CARD_BORDER__; white-space: nowrap; vertical-align: middle; }
.dtbl-w td { background: __TABLE_BG__ !important; color: __TABLE_TX__ !important; padding: 11px 16px; border-bottom: 1px solid __CARD_BORDER__; text-align: left; vertical-align: top; line-height: 1.45; }
.dtbl-w td:first-child { font-weight: 700; color: __HEADING__ !important; }
.dtbl-w tr:last-child td { border-bottom: 0; }
.dtbl-w tbody tr:hover td { background: __SOFT__ !important; }
.dtbl-w a { color: __ACCENT__ !important; font-weight: 600; text-decoration: none; }

/* ---------- kartu metodologi ---------- */
.mg { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; margin: 4px 0 18px; }
.mc { display: flex; gap: 14px; align-items: flex-start; padding: 20px; background: __CARD_BG__; border: 1px solid __CARD_BORDER__; border-radius: 12px; }
.mc .mn { flex: none; width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: __IC_BG__; color: __IC_FG__ !important; font: 800 .8rem Manrope, sans-serif; }
.mc b { display: block; font: 700 .98rem Manrope, sans-serif; color: __HEADING__ !important; margin: 2px 0 6px; line-height: 1.3; }
.mc p { margin: 0; font-size: .86rem; line-height: 1.6; color: __TEXT_MUTED__ !important; }
.mc p i, .mc p b { color: inherit !important; display: inline; font-size: inherit; margin: 0; font-family: inherit; }

/* ---------- footer ---------- */
.dfoot { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-top: 48px; padding-top: 18px; border-top: 1px solid __CARD_BORDER__; font-size: .72rem; color: __TEXT_MUTED__ !important; }
</style>
"""
_df_dark = "[data-testid='stDataFrame'] > div { filter: invert(.92) hue-rotate(180deg); }" if S["theme"] == "dark" else ""
st.markdown(theme_css(_STYLE.replace("__NAV_ICONS__", _NAV_ICONS).replace("__DF_DARK__", _df_dark)
                      .replace("__SCHEME__", "dark" if S["theme"] == "dark" else "light")), unsafe_allow_html=True)


# ============================================================ HELPER
def _axfix(a):
    a.update(tickfont=dict(color=T["text"], size=12), gridcolor=T["grid"], linecolor=T["axis_line"],
             showline=True, zeroline=False)
    a.update(title_font=dict(size=13, color=T["heading"]))


def _pretty(name):
    if name in PRETTY:
        return PRETTY[name]
    if "_" not in name:
        return name if not name.islower() else name.capitalize()
    return name.replace("_", " ").title()


_HOVER_RE = re.compile(r"(^|<br>|<b>)([A-Za-z][A-Za-z0-9_]*)=")
def _fix_hover(tpl):
    return _HOVER_RE.sub(lambda m: m.group(1) + _pretty(m.group(2)) + " = ", tpl) if tpl else tpl


def _fix_title(t):
    return _pretty(t) if t and re.fullmatch(r"[a-z][a-z0-9_]*", t) else t


def prettify_fig(fig):
    for tr in fig.data:
        if getattr(tr, "hovertemplate", None):
            tr.hovertemplate = _fix_hover(tr.hovertemplate)
    for fr in (fig.frames or []):
        for tr in fr.data:
            if getattr(tr, "hovertemplate", None):
                tr.hovertemplate = _fix_hover(tr.hovertemplate)
    for ax in (fig.for_each_xaxis, fig.for_each_yaxis):
        ax(lambda a: a.update(title_text=_fix_title(a.title.text)) if a.title.text else None)
    try:
        if fig.layout.legend.title.text:
            fig.layout.legend.title.text = _fix_title(fig.layout.legend.title.text)
    except Exception:
        pass
    try:
        cb = fig.layout.coloraxis.colorbar.title.text
        if cb:
            fig.layout.coloraxis.colorbar.title.text = _fix_title(cb)
    except Exception:
        pass
    fig.for_each_annotation(
        lambda a: a.update(text=re.sub(r"^([a-z][a-z0-9_]*)=", lambda m: _pretty(m.group(1)) + " = ", a.text or ""))
    )
    return fig


def show(fig):
    prettify_fig(fig)
    fig.update_layout(
        template=T["plotly"], margin=dict(l=24, r=24, t=112, b=40), font=dict(color=T["text"], size=12),
        title=dict(x=0, xref="container", xanchor="left", y=1, yref="container", yanchor="top", pad=dict(t=26, l=24, b=0)),
        paper_bgcolor=T["card_bg"], plot_bgcolor=T["card_bg"],
        title_font=dict(size=17, color=T["heading"]), legend=dict(font=dict(color=T["text"], size=12)),
        hoverlabel=dict(font_size=13),
    )
    fig.for_each_xaxis(_axfix)
    fig.for_each_yaxis(_axfix)
    fig.for_each_annotation(lambda x: x.update(font=dict(color=T["heading"], size=13)))
    try:
        fig.update_coloraxes(colorbar=dict(tickfont=dict(color=T["text"])))
    except Exception:
        pass
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def periode(ys):
    ys = sorted(ys)
    if len(ys) == 1:
        return str(ys[0])
    return f"{ys[0]}–{ys[-1]}" if ys == list(range(ys[0], ys[-1] + 1)) else ", ".join(map(str, ys))


def region_agg(F):
    fl = F.groupby("kabupaten")[FLOW].sum(min_count=1)
    st_ = F.sort_values("tahun").groupby("kabupaten")[STOCK].last()
    return fl.join(st_).reset_index()


def table(df, **kw):
    """Tabel HTML yang menyatu dengan tema (tanpa iframe) sehingga tinggi mengikuti isi dan Dark Mode konsisten."""
    if isinstance(df, pd.DataFrame):
        rename_dict = {
            "kabupaten": "Kabupaten/Kota", "label_klaster": "Label Klaster", "produksi_ton": "Produksi (Ton)",
            "nilai_rp_juta": "Nilai (Rp Juta)", "rtp": "RTP", "pembudidaya": "Pembudidaya",
            "luas_lahan_ha": "Luas Lahan (Ha)", "total_pembesaran": "Total Pembesaran", "tahun": "Tahun",
            "klaster": "Klaster", "file": "Nama File", "format": "Format", "baris": "Jumlah Baris",
            "wilayah": "Wilayah", "Dataset": "Dataset", "Tautan": "Tautan", "Variabel": "Variabel",
        }
        df_renamed = df.rename(columns=rename_dict)
        html_table = df_renamed.to_html(index=False, escape=False, border=0)
        html_table = re.sub(r"\s*\n\s*", "", html_table)
        st.markdown(f'<div class="dtbl-w">{html_table}</div>', unsafe_allow_html=True)
    else:
        st.write(df)


def human(v, prefix="", unit=""):
    if v is None or pd.isna(v):
        return "n/a"
    for lim, s in ((1e12, "T"), (1e9, "M"), (1e6, "Jt"), (1e3, "rb")):
        if abs(v) >= lim:
            return f"{prefix}{v / lim:,.2f} {s} {unit}".strip()
    return f"{prefix}{v:,.0f} {unit}".strip()


CH = 440  # tinggi standar grafik yang berdampingan


def kpi2(col, label, text, sub_html, color="#0077B6", pad=0, compact=False):
    sub_html += "<br>&nbsp;" * max(0, pad - 1 - sub_html.count("<br>"))  # samakan jumlah baris antar-kartu
    col.markdown(f'<div class="kpi{" kc" if compact else ""}" style="--c:{color}"><div class="l">{label}</div><div class="v">{text}</div>'
                 f'<div class="d">{sub_html}</div></div>', unsafe_allow_html=True)


def sumber(keys, note=""):
    parts = [f'<a href="{SUMBER[k]}" target="_blank">{SRC_NAME.get(k, k)}</a>' if k in SUMBER else SRC_NAME.get(k, k)
             for k in keys]
    if S.get("upload_names"):
        parts.append("Data upload: " + ", ".join(S["upload_names"]))
    st.markdown(f'<div class="sumber">Sumber: {" · ".join(parts)}{" · " + note if note else ""}</div>',
                unsafe_allow_html=True)


def section(title, desc=None, eyebrow=None):
    """Subjudul bagian yang seragam di semua halaman."""
    st.markdown('<div class="sh">' + (f'<div class="eb">{eyebrow}</div>' if eyebrow else "") + f'<h3>{title}</h3>'
                + (f'<p>{desc}</p>' if desc else "") + '</div>', unsafe_allow_html=True)


def panel_title(no, title, desc=""):
    st.markdown(f'<div class="pt"><span>{no}</span><div><b>{title}</b>' + (f'<small>{desc}</small>' if desc else "")
                + '</div></div>', unsafe_allow_html=True)


def lead(txt):
    st.markdown(f'<div class="lead">{txt}</div>', unsafe_allow_html=True)


def subhead(txt):
    st.markdown(f'<div class="sub">{txt}</div>', unsafe_allow_html=True)


def insight(txt, warn=False):
    st.markdown(f'<div class="{"warn" if warn else "insight"}"><span class="ii">{svg("alert" if warn else "info", 15)}</span>'
                f'<div>{txt}</div></div>', unsafe_allow_html=True)


def filter_title():
    st.markdown(f'<div class="ft">{svg("filter", 15)}Filter data</div>', unsafe_allow_html=True)


def sim_head(title, desc, chip=""):
    st.markdown(f'<div class="sim-h"><div class="sim-i">{svg("chart", 24)}</div><div><div class="eb">What-If Analysis</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>' + (f'<span class="mchip">{chip}</span>' if chip else "") + '</div>',
                unsafe_allow_html=True)


def toggle_theme():
    n = "light" if S["theme"] == "dark" else "dark"
    S["theme"] = n
    S["theme_radio"] = n


def clean_fact(df):
    df = df.copy()
    for c in FACT_COLS:
        if c not in df:
            df[c] = False if c.startswith("is_") else None
    for c in ("is_suspect_scale", "is_missing_year", "is_stale"):
        df[c] = df[c].fillna(False).astype(bool)
    df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
    df = df.dropna(subset=["tahun", "kabupaten"])
    df["tahun"] = df["tahun"].astype(int)
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    return df[FACT_COLS]


SRC_DB = {
    "jumlah": "OpenData Jatim · Produksi & RTP per jenis budidaya",
    "luas": "OpenData Jatim · Luas lahan per jenis budidaya",
    "pembudidaya": "KKP · Jumlah pembudidaya",
    "bps_nilai": "BPS Jatim · Volume & nilai per jenis budidaya",
    "bps_kegiatan": "BPS Jatim · Volume per jenis kegiatan",
    "kkp_pembesaran": "KKP · Pembesaran (volume & nilai per komoditas)",
    "kkp_pembenihan": "KKP · Pembenihan (benih per komoditas)",
    "kkp_ikan_hias": "KKP · Ikan hias (per komoditas)",
}
SRC_DB_KEY = {"jumlah": "produksi_jenis_budidaya", "luas": "luas_bersih", "pembudidaya": "pembudidaya",
              "bps_nilai": "bps_nilai", "bps_kegiatan": "bps_kegiatan", "kkp_pembesaran": "pembesaran",
              "kkp_pembenihan": "pembenihan", "kkp_ikan_hias": "ikan_hias"}
METRIK_NAME = {"produksi_ton": "Produksi (ton)", "produksi_kg": "Produksi (kg)", "nilai_rp": "Nilai produksi (Rp)",
               "nilai_rp_juta": "Nilai produksi (Rp juta)", "rtp": "Rumah tangga perikanan (RTP)",
               "pembudidaya": "Pembudidaya (orang)", "luas_lahan_ha": "Luas lahan (ha)",
               "volume_ekor": "Volume (ekor)", "volume_ribu_ekor": "Volume (ribu ekor)"}
GATE_MIN_COV, GATE_MIN_TOT = 0.7, 0.4


def short(v):
    if v is None or pd.isna(v):
        return ""
    if abs(v) >= 1e6:
        return f"{v / 1e6:,.2f} Jt"
    if abs(v) >= 1e3:
        return f"{v / 1e3:,.0f} rb"
    return f"{v:,.0f}"


def juta_unit(vmax):
    if vmax >= 1e6:
        return 1e6, "Rp triliun"
    if vmax >= 1e3:
        return 1e3, "Rp miliar"
    return 1.0, "Rp juta"


def gate_years(feat):
    ok, why = {}, {}
    for m in METS:
        s = feat[["tahun", m]].dropna()
        s = s[s[m] > 0]
        if s.empty:
            ok[m], why[m] = [], {}
            continue
        g = s.groupby("tahun")[m].agg(n="size", tot="sum")
        cov = g.n >= GATE_MIN_COV * g.n.max()
        ref = g.tot[cov].median()
        good = cov & (g.tot >= GATE_MIN_TOT * ref)
        ok[m] = [int(y) for y in g.index[good]]
        why[m] = {int(y): ("cakupan wilayah terlalu sedikit" if not cov[y] else "total jauh lebih kecil dari tahun lain")
                  for y in g.index[~good]}
    return ok, why


UPLOAD_SRC = {
    "RTP menurut jenis budidaya (OpenData Jatim)": ("https://opendata.jatimprov.go.id/dataset/jumlah-rtp-rumah-tangga-perikanan--perusahaan-perikanan-pp-berdasarkan-jenis-budidaya", "2020–2024"),
    "Produksi menurut jenis budidaya (OpenData Jatim)": ("https://opendata.jatimprov.go.id/dataset/jumlah-produksi-perikanan-budidaya-berdasarkan-jenis-budidaya", "2020–2025"),
    "Luas lahan menurut jenis budidaya (OpenData Jatim)": ("https://opendata.jatimprov.go.id/dataset/luas-bersih-lahan-perikanan-budidaya-berdasarkan-jenis-budidaya", "2020–2024 (2024 kosong)"),
    "Pembudidaya ikan (KKP)": ("https://portaldata.kkp.go.id/portals/data-statistik/budidaya_ikan/summary", "2020–2024"),
    "Luas lahan budidaya (KKP)": ("https://portaldata.kkp.go.id/portals/data-statistik/lahan_budidaya/summary", "2020–2024"),
    "Produksi pembesaran (KKP)": ("https://portaldata.kkp.go.id/datainsight/produksi-ikan-budidaya", "2020–2024"),
    "Produksi pembenihan (KKP)": ("https://portaldata.kkp.go.id/datainsight/produksi-ikan-pembenihan", "2020–2024"),
    "Produksi ikan hias (KKP)": ("https://portaldata.kkp.go.id/datainsight/produksi-ikan-hias", "2020–2024"),
    "Produksi menurut jenis kegiatan (BPS Jatim)": ("https://jatim.bps.go.id/id/statistics-table/3/WjFab0sxVjVkR3hOVUdjMWNIRnNkbWd3ZWl0bWR6MDkjMw==/produksi-perikanan-budidaya-menurut-kabupaten-kota-dan-jenis-kegiatan-di-provinsi-jawa-timur--2021.html?year=2021", "2020–2022"),
    "Volume & nilai produksi (BPS Jatim)": ("https://jatim.bps.go.id/id/statistics-table/3/Wldsb1EyRktNMDl2VUVSalEzVllaM2xQWTFGTmR6MDkjMw%3D%3D/volume-produksi-dan-nilai-produksi-perikanan-budidaya-menurut-kabupaten-kota-dan-jenis-budidaya-di-provinsi-jawa-timur--2023.html", "2023–2024"),
}
_U = list(UPLOAD_SRC)
LINK_BY_SUMBER = {"luas": _U[2], "pembudidaya": _U[3], "kkp_pembesaran": _U[5], "kkp_pembenihan": _U[6],
                  "kkp_ikan_hias": _U[7], "bps_kegiatan": _U[8], "bps_nilai": _U[9]}


def link_for(sumber_, metrik_):
    if sumber_ == "jumlah":
        return UPLOAD_SRC[_U[0] if metrik_ == "rtp" else _U[1]][0]
    k = LINK_BY_SUMBER.get(sumber_)
    return UPLOAD_SRC[k][0] if k else None


def raw_dir():
    try:
        import src.config as cfg
        for n in ("RAW_DIR", "RAW_DATA_DIR", "DATA_RAW_DIR", "DATA_DIR"):
            if hasattr(cfg, n):
                return Path(getattr(cfg, n))
    except Exception:
        pass
    return ROOT / "Data"


def usable(df):
    return df if S["flag"] else df[~df.is_suspect_scale & ~df.is_missing_year]


# ============================================================ AKSES DATABASE
def _read(sql):
    from sqlalchemy import text
    from src.db import get_engine
    with get_engine().connect() as c:
        return pd.read_sql(text(sql), c)


@st.cache_data(ttl=300, show_spinner="Memuat data dari database...")
def load_db():
    out, notes = {}, []
    out["dim"] = _read("SELECT * FROM dim_kabupaten")
    out["fact"] = _read("""SELECT f.tahun, k.nama_kabupaten AS kabupaten, f.jenis_budidaya, f.metrik, f.nilai, f.satuan,
                                  f.sumber, f.kegiatan, f.komoditas, f.is_suspect_scale, f.is_missing_year, f.is_stale
                           FROM fact_budidaya f JOIN dim_kabupaten k ON f.kabupaten_id = k.kabupaten_id""")
    for t in ("features_model", "cluster_assignments", "model_versions", "raw_budidaya"):
        try:
            out[t] = _read(f"SELECT * FROM {t}")
        except Exception as e:
            out[t] = None
            notes.append(f"Tabel {t} tidak terbaca: {type(e).__name__}")
    return out, notes


def read_report(fname):
    try:
        from src.config import REPORT_DIR
        p = Path(REPORT_DIR) / fname
        return pd.read_csv(p) if p.exists() else None
    except Exception:
        return None


DB_ERR = None
try:
    DB, DB_NOTES = load_db()
except Exception as e:
    DB, DB_NOTES, DB_ERR = None, [], f"{type(e).__name__}: {e}"
base_src = "PostgreSQL"
ups, mode = [], MODE_UPSERT
if DB_ERR:
    st.error("**Database tidak dapat dibaca.** Dashboard hanya menampilkan data dari database dan tidak memakai data cadangan.")
    st.code(DB_ERR)
    st.caption("Periksa koneksi database dan konfigurasi proyek, lalu muat ulang halaman.")
    st.stop()

dim_name = DB["dim"].set_index("kabupaten_id")["nama_kabupaten"]


def with_names(df):
    if df is None:
        return None
    df = df.copy()
    if "kabupaten" not in df.columns and "kabupaten_id" in df.columns:
        df["kabupaten"] = df["kabupaten_id"].map(dim_name)
    if "tahun" in df.columns:
        df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
    return df.dropna(subset=["kabupaten", "tahun"]).astype({"tahun": int}) if "kabupaten" in df.columns else df


fact = clean_fact(DB["fact"])
feat = with_names(DB["features_model"])
clu = with_names(DB["cluster_assignments"])
mv = DB["model_versions"]
if feat is None or feat.empty:
    st.error("Data fitur wilayah belum tersedia di database. Unggah data di menu **Upload Data** atau jalankan pembaruan data terlebih dahulu.")
    st.stop()
_sh = {c: "sh::" + c[len("share_"):].replace("_", " ").upper() for c in feat.columns if c.startswith("share_")}
feat = feat.rename(columns=_sh)
for c in METS:
    if c not in feat:
        feat[c] = np.nan
feat = feat[["kabupaten", "tahun"] + METS + list(_sh.values())].copy()
_mk = usable(fact[(fact.sumber == "jumlah") & (fact.metrik == "produksi_ton")])
_mk = _mk.groupby(["kabupaten", "tahun"], as_index=False)["nilai"].sum(min_count=1).rename(columns={"nilai": "produksi_ton"})
BRIDGED = sorted(int(y) for y in set(_mk.tahun) if y > feat.tahun.max())
if BRIDGED:
    _add = _mk[_mk.tahun.isin(BRIDGED)].copy()
    for _c in feat.columns:
        if _c not in _add:
            _add[_c] = np.nan
    feat = pd.concat([feat, _add[feat.columns]], ignore_index=True)
feat_raw = feat.copy()
VALID, GATE_WHY = gate_years(feat)
for m in METS:
    feat.loc[~feat.tahun.isin(VALID[m]), m] = np.nan
for c in _sh.values():
    feat.loc[~feat.tahun.isin(VALID["total_pembesaran"]), c] = np.nan
has_data = bool(feat[METS].notna().any().any())
years = sorted(int(y) for y in feat[feat[METS].notna().any(axis=1)].tahun.unique()) if has_data else []
feat = feat[feat.tahun.isin(years)]
cluster_years = sorted(int(y) for y in clu.tahun.unique()) if clu is not None and len(clu) and "klaster" in clu else []

# ========== REVISI 4: TAHUN FILTER DINAMIS (data + tahun berjalan) ==========
def _filter_years():
    base = set(years)
    now_y = pd.Timestamp.now().year
    # tahun berjalan selalu tersedia (agar user bisa pilih walau data belum masuk)
    base.add(now_y)
    # untuk memungkinkan persiapan tahun depan, aktifkan baris di bawah:
    # base.add(now_y + 1)
    return sorted(base)

YEARS_FILTER = _filter_years() if has_data else []


def get_cluster(ty):
    if ty not in cluster_years:
        return None
    d = clu[clu.tahun == ty].copy()
    if "label_klaster" not in d:
        d["label_klaster"] = "Tipologi " + d["klaster"].astype(str)
    miss = [c for c in FIT_KL if c not in d]
    extra = miss + [c for c in feat.columns if c.startswith("sh::")]
    d = d.merge(feat_raw[["kabupaten", "tahun"] + extra], on=["kabupaten", "tahun"], how="left") if extra else d
    pcols = [c for c in FIT_KL if c in d and d[c].notna().any()]
    shc = [c for c in d.columns if c.startswith("sh::") and d[c].notna().any()]
    lab = d.groupby("klaster")["label_klaster"].first()
    if lab.duplicated(keep=False).any():
        lab = pd.Series({k: f"{v} (K{int(k) + 1})" for k, v in lab.items()})
        d["label_klaster"] = d["klaster"].map(lab)
    names = lab.to_dict()
    prof = d.groupby("klaster")[pcols].mean()
    shp = d.groupby("klaster")[shc].mean() if shc else pd.DataFrame(index=prof.index)
    domin = {cl: ([c.split("::")[1].title() for c in shp.loc[cl].dropna().sort_values(ascending=False).index[:2]] if shc else [])
             for cl in prof.index}
    uncl = sorted(set(feat_raw[feat_raw.tahun == ty].kabupaten) - set(d.kabupaten))
    return dict(df=d, names=names, prof=prof, shp=shp, domin=domin, shc=shc, sizes=d.groupby("klaster").size(), uncl=uncl)


def hidden_note(ms):
    bits = [f"{LABEL[m].split(' (')[0]} ({periode(list(GATE_WHY[m]))})" for m in ms if GATE_WHY.get(m)]
    return ("Tahun dengan data belum lengkap tidak ditampilkan: " + "; ".join(bits) + ". Rincian di menu Metadata.") if bits else ""


# ============================================================ ALUR PEMBARUAN
def sync_table(df, table):
    from sqlalchemy import text, inspect
    from src.db import get_engine
    eng = get_engine()
    cols = [c["name"] for c in inspect(eng).get_columns(table)]
    d = df.copy()
    dropped = 0
    if "kabupaten_id" in cols and "kabupaten_id" not in d and "kabupaten" in d:
        ids = dict(zip(DB["dim"]["nama_kabupaten"], DB["dim"]["kabupaten_id"]))
        d["kabupaten_id"] = d["kabupaten"].map(ids)
        dropped = int(d["kabupaten_id"].isna().sum())
        d = d.dropna(subset=["kabupaten_id"])
        d["kabupaten_id"] = d["kabupaten_id"].astype(int)
    d = d[[c for c in d.columns if c in cols]]
    if "updated_at" in cols and "updated_at" not in d:
        d["updated_at"] = pd.Timestamp.now()
    with eng.begin() as c:
        c.execute(text(f"DELETE FROM {table}"))
        d.to_sql(table, c, if_exists="append", index=False)
    return len(d), dropped


def run_update(raw_bytes, raw_name, log):
    import contextlib, io
    out = {"ok": False}
    log("Menyimpan data mentah")
    dst = raw_dir()
    dst.mkdir(parents=True, exist_ok=True)
    tgt = dst / raw_name
    if tgt.exists():
        tgt.rename(tgt.with_suffix(tgt.suffix + ".bak"))
    tgt.write_bytes(raw_bytes)
    log("Pembersihan data, pembuatan fitur, klasterisasi, dan regresi")
    from src.pipeline import run_all
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = run_all()
    out["log"] = buf.getvalue()
    log("Menyimpan data terintegrasi dan fitur ke database")
    from src.db import upsert_fact, upsert_features
    upsert_fact(res["fact"])
    upsert_features(res["features"])
    log("Menyimpan hasil klasterisasi")
    cdf = res["clustering"]["df"]
    out["cluster_rows"], out["cluster_dropped"] = sync_table(
        cdf[["kabupaten", "tahun", "klaster", "label_klaster"] + [c for c in FIT_KL if c in cdf]], "cluster_assignments")
    out["ok"] = True
    return out


# ============================================================ PETA WILAYAH (CHOROPLETH)
import zlib as _zlib, base64 as _b64
GEO_B64 = "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"


@st.cache_data(show_spinner=False)
def load_geojson():
    """Batas 38 kabupaten/kota Jawa Timur (sudah disederhanakan). Tertanam di kode, tidak butuh berkas atau internet."""
    return json.loads(_zlib.decompress(_b64.b64decode(GEO_B64)))


def _gid(name):
    n = re.sub(r"^(kabupaten|kab\.?)\s+", "", str(name).strip(), flags=re.I)
    n = re.sub(r"^kota\s+", "Kota ", n, flags=re.I)
    return {f["id"].lower(): f["id"] for f in load_geojson()["features"]}.get(n.lower())


PETA_UNK = []          # nama wilayah yang tidak punya bentuk di peta (diisi oleh peta())
_SEQ = [[i / (len(SEQ_OCEAN) - 1), c] for i, c in enumerate(SEQ_OCEAN)]


def _txt_on(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#0B1B2B" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


def peta(M, vcol, kategori_col, mode, judul, tinggi=560, labels=14, vlabel="", cmap=None):
    """Peta area berwarna (choropleth) per kabupaten/kota, dengan nama wilayah, legenda, dan tema terang/gelap.
    mode='sequential': gradasi warna menurut nilai vcol. mode='categorical': warna per kategori (mis. tipologi)."""
    global PETA_UNK
    GEO = load_geojson()
    ids = [f["id"] for f in GEO["features"]]
    dark = S.get("theme") == "dark"
    new = hasattr(go, "Choroplethmap")
    Ch = go.Choroplethmap if new else go.Choroplethmapbox
    Sc = go.Scattermap if new else go.Scattermapbox
    gray, edge = ("#3B4755", "#0C1C2E") if dark else ("#DCE2E8", "#FFFFFF")
    fig = go.Figure()
    fig.add_trace(Ch(geojson=GEO, featureidkey="properties.nama", locations=ids, z=[0] * len(ids), colorscale=[[0, gray], [1, gray]],
                     showscale=False, hoverinfo="skip", marker=dict(line=dict(width=.8, color=edge))))
    M = M.copy()
    M["gid"] = M["kabupaten"].map(_gid)
    PETA_UNK = sorted(M[M.gid.isna()].kabupaten.unique())
    M = M.dropna(subset=["gid"])
    lab_light, lab_dark = [], []
    if mode == "sequential" and len(M):
        zmax = float(M[vcol].max()) or 1.0
        fig.add_trace(Ch(geojson=GEO, featureidkey="properties.nama", locations=M.gid, z=M[vcol], text=M.kabupaten, zmin=0, zmax=zmax,
                         colorscale=_SEQ, marker=dict(opacity=.95, line=dict(width=.9, color=edge)),
                         colorbar=dict(title=dict(text=vlabel), thickness=13, len=.45, x=.01, xanchor="left", y=.04, yanchor="bottom"),
                         hovertemplate="<b>%{text}</b><br>" + (vlabel or "Nilai") + ": %{z:,.0f}<extra></extra>"))
        for _, r_ in M.nlargest(labels, vcol).iterrows():
            (lab_dark if r_[vcol] / zmax < .5 else lab_light).append(r_.kabupaten)
    elif len(M):
        cats = list(dict.fromkeys(M[kategori_col]))
        cm = cmap or {c: CAT_LIVELY[i % len(CAT_LIVELY)] for i, c in enumerate(cats)}
        for cname in cats:
            g = M[M[kategori_col] == cname]
            col = cm[cname]
            fig.add_trace(Ch(geojson=GEO, featureidkey="properties.nama", locations=g.gid, z=[1] * len(g), text=g.kabupaten, showscale=False,
                             colorscale=[[0, col], [1, col]], marker=dict(opacity=.95, line=dict(width=.9, color=edge)),
                             hovertemplate="<b>%{text}</b><br>" + str(cname) + "<extra></extra>"))
            fig.add_trace(Sc(lat=[None], lon=[None], mode="markers", marker=dict(size=12, color=col), name=str(cname), showlegend=True))
            (lab_light if _txt_on(col) == "#FFFFFF" else lab_dark).extend(g.kabupaten.tolist())
    for names, tc in ((lab_light, "#FFFFFF"), (lab_dark, "#0B1B2B")):
        pts = [(KOORD[n][0], KOORD[n][1], n) for n in names if n in KOORD]
        if pts:
            fig.add_trace(Sc(lat=[p[0] for p in pts], lon=[p[1] for p in pts], mode="text",
                             text=[p[2].replace("Kota ", "") + ("*" if p[2].startswith("Kota") else "") for p in pts],
                             textfont=dict(size=10, color=tc), hoverinfo="skip", showlegend=False))
    lay = dict(style="carto-darkmatter" if dark else "carto-positron", center=dict(lat=-7.4, lon=113.2), zoom=7.0)
    fig.update_layout(**({"map": lay} if new else {"mapbox": lay}), height=tinggi, margin=dict(l=0, r=0, t=44, b=0),
                      title=dict(text=judul, font=dict(size=16, color=T["heading"])),
                      legend=dict(orientation="h", y=0.01, x=0.99, xanchor="right", yanchor="bottom",
                                  bgcolor="rgba(12,28,46,.75)" if dark else "rgba(255,255,255,.8)"))
    return fig


# ============================================================ LANDING PAGE
def sbtn(target, label, **kw):
    try:
        return target.button(label, width="stretch", **kw)
    except TypeError:
        return target.button(label, use_container_width=True, **kw)


def open_page(page=None):
    S["entered"] = True
    if page:
        S["nav"] = page


def landing():
    # Warna hero mengikuti tema (tidak lagi biru penuh)
    _dark = S["theme"] == "dark"
    _hero_bg = "linear-gradient(135deg,#0F2236 0%,#0B2A40 100%)" if _dark else "linear-gradient(135deg,#FFFFFF 0%,#E4F5F9 100%)"
    _hero_orb = "rgba(69,197,223,.10)" if _dark else "rgba(0,119,168,.08)"
    _W = '[data-testid="stVerticalBlockBorderWrapper"]'
    _css = """<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display:none !important; }
    .block-container { max-width:1280px !important; padding-top:1.4rem !important; }
    /* wadah/kolom Streamlit: tanpa border & latar (hanya kartu yang diberi gaya di bawah) */
    __W__ { border:0 !important; background:transparent !important; box-shadow:none !important; }
    /* nav atas */
    [data-testid="stHorizontalBlock"]:has(.ln-brand) { align-items:center; padding-bottom:14px; margin-bottom:22px; border-bottom:1px solid __CARD_BORDER__; }
    .ln-brand { display:flex; align-items:center; gap:11px; }
    .ln-brand b { display:block; font:700 14px/1.3 Manrope,sans-serif; color:__HEADING__ !important; }
    .ln-brand small { display:block; font-size:11px; color:__TEXT_MUTED__ !important; margin-top:2px; }
    [data-testid="stHorizontalBlock"]:has(.ln-brand) .stButton > button { background:transparent !important; color:__HEADING__ !important;
        border:1px solid __CARD_BORDER__ !important; min-height:2.3rem; font-size:.8rem; box-shadow:none; }
    /* hero */
    [data-testid="stElementContainer"]:has(.lh-m) { display:none; }
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) { border:1px solid __CARD_BORDER__ !important; border-radius:22px; padding:52px 56px 48px; position:relative; overflow:hidden;
        background:__HERO_BG__ !important; box-shadow:0 14px 40px rgba(14,70,95,.07); }
    __W__:has(.lh-m):not(:has(__W__ .lh-m))::before { content:""; position:absolute; width:380px; height:380px; border-radius:50%; right:-90px; top:-120px; background:__HERO_ORB__; pointer-events:none; }
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) .stButton > button { min-height:2.8rem; font-size:.86rem; border-radius:10px !important; }
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) [data-testid="stColumn"]:nth-child(1) .stButton > button,
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) [data-testid="column"]:nth-child(1) .stButton > button { background:#F4744A !important; color:#FFFFFF !important; border:0 !important; box-shadow:0 8px 20px rgba(244,116,74,.28); }
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) [data-testid="stColumn"]:nth-child(2) .stButton > button,
    __W__:has(.lh-m):not(:has(__W__ .lh-m)) [data-testid="column"]:nth-child(2) .stButton > button { background:transparent !important; color:__ACCENT__ !important; border:1px solid __ACCENT__ !important; box-shadow:none; }
    .lh-kick { display:flex; align-items:center; gap:10px; font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:__ACCENT__ !important; }
    .lh-kick i { width:24px; height:2px; background:__ACCENT__; display:inline-block; }
    .lh-copy h1 { font:800 clamp(2rem,3.4vw,3.2rem)/1.12 Manrope,sans-serif !important; letter-spacing:-.035em; margin:16px 0 !important; padding:0 !important; color:__HEADING__ !important; max-width:860px; }
    .lh-copy h1 em { font-style:normal; color:__ACCENT__ !important; }
    .lh-copy p { max-width:700px; color:__TEXT_MUTED__ !important; font-size:1rem; line-height:1.7; margin:0 0 16px; }
    .lh-tags { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 22px; }
    .lh-tags span { background:__IC_BG__; border:1px solid __CARD_BORDER__; padding:4px 13px; border-radius:20px; font-size:.76rem; font-weight:600; color:__IC_FG__ !important; }
    /* seksi */
    .lsec { margin:52px 0 20px; }
    .lsec .lab { font-size:.66rem; text-transform:uppercase; letter-spacing:.18em; font-weight:800; color:__ACCENT__ !important; }
    .lsec h2 { font:800 1.6rem Manrope,sans-serif !important; color:__HEADING__ !important; margin:6px 0 4px !important; padding:0 !important; }
    .lsec p { font-size:.9rem; color:__TEXT_MUTED__ !important; margin:0; }
    /* kartu fitur: semua sama ukuran */
    __W__:has(.fc):not(:has(__W__ .fc)) { background:__CARD_BG__ !important; border:1px solid __CARD_BORDER__ !important; border-radius:14px; padding:6px 8px 2px;
        box-shadow:0 5px 20px rgba(14,70,95,.05); transition:transform .2s ease, box-shadow .2s ease; }
    __W__:has(.fc):not(:has(__W__ .fc)):hover { transform:translateY(-3px); box-shadow:0 16px 36px rgba(14,70,95,.10); }
    .fc { height:178px; padding:12px 4px 0; overflow:hidden; box-sizing:border-box; }
    .fc .fi { width:44px; height:44px; border-radius:12px; display:grid; place-items:center; margin-bottom:16px; }
    .fc h3 { font:700 1rem/1.3 Manrope,sans-serif !important; color:__HEADING__ !important; margin:0 0 6px !important; padding:0 !important; }
    .fc p { font-size:.84rem; line-height:1.55; color:__TEXT_MUTED__ !important; margin:0; }
    __W__:has(.fc):not(:has(__W__ .fc)) .stButton > button { background:transparent !important; color:__ACCENT__ !important; border:0 !important; box-shadow:none;
        justify-content:flex-start; padding:0 4px; min-height:2.2rem; font-size:.82rem; }
    /* proses */
    .lp { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; }
    .lp > div { position:relative; min-height:190px; padding:24px; background:__CARD_BG__; border:1px solid __CARD_BORDER__; border-radius:14px; box-sizing:border-box; }
    .lp .no { position:absolute; right:20px; top:16px; font:700 .7rem Manrope,sans-serif; color:__NA__ !important; }
    .lp .pi { color:__ACCENT__ !important; margin-bottom:18px; }
    .lp h3 { font:700 1rem/1.3 Manrope,sans-serif !important; color:__HEADING__ !important; margin:0 0 6px !important; padding:0 !important; }
    .lp p { font-size:.84rem; line-height:1.55; color:__TEXT_MUTED__ !important; margin:0; }
    .chips a, .chips span { display:inline-block; margin:4px 6px 0 0; padding:5px 13px; border-radius:16px; background:__IC_BG__; color:__IC_FG__ !important; font-size:.78rem; font-weight:600; text-decoration:none; }
    .lfoot { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; margin-top:52px; padding-top:22px; border-top:1px solid __CARD_BORDER__; font-size:.74rem; color:__TEXT_MUTED__ !important; }
    @media (max-width:1000px){ .lp{grid-template-columns:1fr 1fr;} }
    @media (max-width:560px){ .lp{grid-template-columns:1fr;} .fc{height:auto; min-height:150px;} __W__:has(.lh-m):not(:has(__W__ .lh-m)){padding:30px 22px;} }
    </style>"""
    _css = _css.replace("__W__", _W).replace("__HERO_BG__", _hero_bg).replace("__HERO_ORB__", _hero_orb)
    st.markdown(theme_css(_css), unsafe_allow_html=True)

    n1, n2 = st.columns([5, 1.3])
    n1.markdown(f'<div class="ln-brand"><div class="sb-mark">{svg("fish", 22)}</div><div><b>Perikanan Jatim</b><small>Dashboard Budidaya</small></div></div>',
                unsafe_allow_html=True)
    sbtn(n2, "Light mode" if _dark else "Dark mode", on_click=toggle_theme, key="land_theme")

    with st.container(border=True):
        st.markdown('<span class="lh-m"></span>', unsafe_allow_html=True)
        st.markdown('<div class="lh-copy"><div class="lh-kick"><i></i>Dashboard data perikanan budidaya · Jawa Timur</div>'
                    '<h1>Eksplorasi <em>Data Perikanan</em><br>Budidaya Jawa Timur</h1>'
                    '<p>Memahami kondisi perikanan budidaya melalui data yang terintegrasi. Eksplorasi persebaran produksi, identifikasi karakteristik '
                    'wilayah, dan manfaatkan analisis data untuk mendukung pengembangan potensi perikanan Jawa Timur.</p>'
                    '<div class="lh-tags"><span>Peta interaktif</span><span>Tipologi wilayah</span><span>Analisis regresi</span><span>Data dinamis</span></div></div>',
                    unsafe_allow_html=True)
        b1, b2, _ = st.columns([1.1, 1.3, 3.6])
        sbtn(b1, "Mulai Menjelajah  →", on_click=open_page, key="enter_btn")
        sbtn(b2, "Pelajari Sumber Data", on_click=open_page, args=(PAGES[7],), key="enter_src")

    st.markdown('<div class="lsec"><div class="lab">Eksplorasi data</div><h2>Apa yang bisa kamu temukan?</h2>'
                '<p>Pilih langsung menu yang ingin dibuka.</p></div>', unsafe_allow_html=True)
    feats = [(0, "wave", "Beranda Utama", "Angka kunci, tren produksi, dan wilayah teratas.", "#007C9D"),
             (1, "map", "Peta", "Sebaran produksi, nilai, dan tipologi wilayah.", "#376FCC"),
             (2, "grid", "Tipologi", "Kelompok daerah dengan karakter budidaya yang mirip.", "#168264"),
             (3, "fish", "Komoditas", "Jenis ikan, nilai produksi, benih, dan ikan hias.", "#E56A42"),
             (5, "chart", "Regresi", "Seberapa kuat volume menjelaskan nilai produksi?", "#6C55C8")]
    for col, (pg, ic, nm, ds, colr) in zip(st.columns(5), feats):
        with col.container(border=True):
            st.markdown(f'<div class="fc"><div class="fi" style="background:{colr}22;color:{colr}">{svg(ic, 22)}</div><h3>{nm}</h3><p>{ds}</p></div>',
                        unsafe_allow_html=True)
            sbtn(st, "Buka halaman  →", on_click=open_page, args=(PAGES[pg],), key=f"go_{pg}")

    st.markdown('<div class="lsec"><div class="lab">Proses terpercaya</div><h2>Dari data mentah menjadi wawasan</h2>'
                '<p>Setiap angka di dashboard melewati alur yang sama.</p></div>', unsafe_allow_html=True)
    _steps = [("database", "Pengumpulan Data", "Menghimpun data perikanan budidaya dari sumber resmi, seperti Open Data Jatim, KKP, dan BPS Jawa Timur."),
              ("filter", "Pembersihan Data", "Menyeragamkan format, satuan, dan identitas wilayah serta menangani data kosong dan anomali."),
              ("chart", "Analisis Data", "Mengidentifikasi karakteristik wilayah melalui klasterisasi K-Means dan menganalisis hubungan antarvariabel menggunakan regresi."),
              ("grid", "Visualisasi Data", "Menyajikan hasil pengolahan dalam bentuk grafik, peta interaktif, dan informasi yang diperbarui berdasarkan data terbaru.")]
    st.markdown('<div class="lp">' + "".join(
        f'<div><span class="no">0{i}</span><div class="pi">{svg(ic, 24)}</div><h3>{t_}</h3><p>{d_}</p></div>'
        for i, (ic, t_, d_) in enumerate(_steps, 1)) + '</div>', unsafe_allow_html=True)

    chips = "".join(f'<a href="{SUMBER[k]}" target="_blank">{n}</a>' if k in SUMBER else f"<span>{n}</span>" for k, n in SRC_NAME.items())
    st.markdown(f'<div class="lsec"><div class="lab">Sumber data</div><h2>Bersumber dari lembaga resmi</h2></div><div class="chips">{chips}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="lfoot"><div class="ln-brand"><div class="sb-mark">{svg("fish", 20)}</div><div><b>Perikanan Jatim</b>'
                '<small>Data untuk pembangunan berkelanjutan</small></div></div>'
                '<span>Dashboard Perikanan Budidaya Jawa Timur · data diolah dari sumber resmi di atas</span></div>', unsafe_allow_html=True)


if not S["entered"]:
    landing()
    st.stop()

# ============================================================ SIDEBAR
with st.sidebar:
    st.markdown(f'<div class="sb-brand"><div class="sb-mark">{svg("fish", 22)}</div><div><b>Perikanan Jatim</b>'
                '<small>Dashboard Budidaya</small></div></div>', unsafe_allow_html=True)
    S["theme_radio"] = S["theme"]  # selalu sinkron dengan tema aktif (juga setelah diubah dari landing)
    st.radio("Tampilan", ["light", "dark"], format_func=lambda x: "Light" if x == "light" else "Dark",
             horizontal=True, key="theme_radio", label_visibility="collapsed",
             on_change=lambda: S.update(theme=S["theme_radio"]))
    st.markdown('<div class="nav-label">Menu utama</div>', unsafe_allow_html=True)
    page = st.radio("Menu", PAGES, label_visibility="collapsed", key="nav")
    st.markdown(f'<div class="side-status"><div class="ss-h"><span class="live-dot"></span>Data tersinkronisasi</div>'
                f'<p><span>Sumber</span><b>{base_src}</b></p>'
                f'<p><span>Tahun data</span><b>{(str(years[0]) + "–" + str(years[-1])) if years else "-"}</b></p>'
                f'<p><span>Wilayah</span><b>{feat.kabupaten.nunique() if has_data else 0} kab/kota</b></p></div>', unsafe_allow_html=True)
    sbtn(st, "←  Halaman awal", on_click=lambda: S.update(entered=False), key="to_landing")
pi = PAGES.index(page)


def hero(i):
    """Header standar untuk seluruh menu: ikon, label, judul, deskripsi, dan chip sumber data."""
    t, sub = HERO[i]
    src = f"Sumber aktif: {base_src}" + (f" + {len(ups)} upload" if ups else "")
    st.markdown(f'<div class="ph"><div class="ph-ic">{svg(PAGE_ICONS[i], 24)}</div><div><div class="ph-eb">Dashboard Perikanan Budidaya</div>'
                f'<h1>{t}</h1><p>{sub}</p></div><div class="ph-chip"><span class="live-dot"></span>{src}</div></div>',
                unsafe_allow_html=True)


# ============================================================ FILTER SERAGAM
from types import SimpleNamespace as _NS


def focus_year(ys, var=None):
    """Tahun untuk grafik satu-tahun: tahun terbaru yang dipilih. Return None jika tidak ada data valid."""
    ok = set(VALID.get(var or "total_pembesaran", []))
    c = [y for y in ys if y in ok]
    return max(c) if c else None


def _year_ctl(container, key, single=False, opts=None, default=None):
    """REVISI 1: Selalu pakai dropdown (selectbox/multiselect), bukan pills."""
    opts = list(opts if opts is not None else YEARS_FILTER)
    k = f"{key}_{len(opts)}_{opts[-1] if opts else 0}"
    if single:
        dflt = default if default in opts else (opts[-1] if opts else None)
        if dflt is None:
            return None
        return container.selectbox("Tahun", opts, index=opts.index(dflt), key=k)
    hp = ("Pilih satu atau beberapa tahun. Grafik yang menampilkan satu tahun memakai tahun terbaru "
          "yang dipilih dan datanya tersedia.")
    v = container.multiselect("Tahun", opts, default=list(opts), key=k, help=hp, placeholder="Semua tahun")
    return sorted(v) if v else list(opts)


def fbar(prefix, kab=True, single=False, year_opts=None, extra=None, var=None, kab_label="Wilayah (kabupaten/kota)",
         kab_max=None, kab_default=None, kab_placeholder="Semua wilayah"):
    """Satu baris filter yang sama di semua menu: Tahun | Wilayah | kontrol khusus halaman."""
    with st.container(border=True):
        filter_title()
        n = 1 + (1 if kab else 0) + (1 if extra else 0)
        cs = st.columns({1: [1], 2: [3, 2], 3: [3, 2, 2]}[n])
        opts = list(year_opts if year_opts is not None else YEARS_FILTER)
        yv = _year_ctl(cs[0], f"{prefix}_yr", single, opts, focus_year(opts, var) if single else None)
        i, sel, ev = 1, [], None
        if kab:
            kw = {"max_selections": kab_max} if kab_max else {}
            sel = cs[i].multiselect(kab_label, sorted(feat.kabupaten.unique()), default=kab_default, placeholder=kab_placeholder,
                                    key=f"{prefix}_kab", **kw)
            i += 1
        if extra:
            lab, eopts, fmt, key = extra
            ev = cs[i].selectbox(lab, eopts, format_func=fmt, key=key)
    ys = [yv] if single else yv
    if single:
        ty = yv
    else:
        ty = focus_year(ys or [], var)
    return _NS(ys=ys if ys else opts, ty=ty, sel=sel, extra=ev)


def filter_bar(prefix, extra=None):
    ns = fbar(prefix, extra=extra)
    return (ns.ys, ns.sel, ns.extra) if extra else (ns.ys, ns.sel)


def scope(p, rng=True, kab=True, extra=None, extra2=None):
    """Kembalian: (yr, ty, sel, in_sel, F, FACT, extra_val, False). rng=False -> halaman satu tahun."""
    ns = fbar(p, kab=kab, single=not rng, extra=extra)
    ys = ns.ys if rng else list(years)
    msk = (lambda x: x.isin(ns.sel)) if ns.sel else (lambda x: pd.Series(True, index=x.index))
    return ((ys[0], ys[-1]), ns.ty, ns.sel, msk, feat[feat.tahun.isin(ys) & msk(feat.kabupaten)],
            fact[fact.tahun.isin(ys) & msk(fact.kabupaten)], ns.extra, False)


if not has_data and pi != 6:
    hero(pi)
    st.warning("Belum ada data. Buka menu **Upload Data** untuk mengunggah data, atau periksa koneksi database.")
    st.stop()


METS_UI = ["total_pembesaran", "nilai_rp_juta", "rtp", "pembudidaya", "luas_lahan_ha", "produksi_ton"]


def kom_table(Fx, source="kkp_pembesaran", vm="produksi_ton", nm="nilai_rp_juta", gate=True):
    k = usable(Fx[(Fx.sumber == source) & Fx.komoditas.notna()])
    key = ["tahun", "kabupaten", "komoditas"]
    d = pd.concat([k[k.metrik == vm].groupby(key)["nilai"].sum().rename("vol"),
                   k[k.metrik == nm].groupby(key)["nilai"].sum().rename("nil")], axis=1).reset_index()
    if gate and source == "kkp_pembesaran":
        d.loc[~d.tahun.isin(VALID["total_pembesaran"]), "vol"] = np.nan
        d.loc[~d.tahun.isin(VALID["total_pembesaran"]), "nil"] = np.nan
    return d


def donut(df, names, values, title, height=400):
    fig = px.pie(df, names=names, values=values, hole=.56, color_discrete_sequence=CAT_LIVELY, title=title, height=height)
    fig.update_traces(textinfo="percent", textposition="inside", sort=False,
                      textfont=dict(size=13, color="white"),
                      marker=dict(line=dict(color=T["card_bg"], width=2)),
                      hovertemplate="%{label}: %{value:,.0f} (%{percent})<extra></extra>")
    fig.update_layout(legend=dict(orientation="v", y=0.5, x=1.02))
    return fig


# ============================================================ 1. BERANDA UTAMA
if pi == 0:
    hero(0)
    ys, sel, rank_m = filter_bar("ov", extra=("Peringkat berdasarkan", METS_UI, LABEL.get, "rank_m"))
    kpi_area = st.container()
    in_sel = (lambda x: x.isin(sel)) if sel else (lambda x: pd.Series(True, index=x.index))
    F = feat[feat.tahun.isin(ys) & in_sel(feat.kabupaten)]
    Fk = feat[in_sel(feat.kabupaten)]
    if F.empty or not F[METS].notna().any(axis=1).any():
        insight("<b>Belum ada data lengkap untuk tahun yang dipilih.</b> Coba pilih tahun lain atau unggah data baru di menu Upload Data.", warn=True)
    per = periode(ys)
    tot = F.groupby("tahun")[METS].sum(min_count=1)
    tot_all = Fk.groupby("tahun")[METS].sum(min_count=1)
    R = region_agg(F)

    specs = [("total_pembesaran", "Total Produksi Budidaya", lambda v: human(v, unit="Ton"), "#0096C7"),
             ("nilai_rp_juta", "Total Nilai Produksi (BPS)", lambda v: human(v * 1e6, "Rp "), "#FF7A59"),
             ("rtp", "Rumah Tangga Perikanan", human, "#2A9D8F"),
             ("pembudidaya", "Pembudidaya", human, "#8338EC"),
             ("luas_lahan_ha", "Luas Lahan", lambda v: human(v, unit="Ha"), "#FB5607"),
             ("produksi_ton", "Produksi menurut Media", lambda v: human(v, unit="Ton"), "#3A86FF")]
    with kpi_area:
        cols = st.columns(6)
        for col, (m, lab, fmt, colr) in zip(cols, specs):
            sr = tot[m].dropna()
            if sr.empty:
                kpi2(col, lab, "n/a", '<span class="na">tidak ada data lengkap pada filter ini</span>', colr, pad=3)
                continue
            if m in FLOW:
                v = sr.sum()
                sub = f'<span class="na">Akumulasi {periode(list(sr.index))}</span>'
                if len(sr) > 1:
                    sub += f'<br><span class="na">rata-rata {fmt(v / len(sr))}/tahun</span>'
            else:
                v = sr.iloc[-1]
                sub = f'<span class="na">Posisi tahun {sr.index[-1]}</span>'
            if len(ys) == 1:
                pv = tot_all[m].get(ys[0] - 1, np.nan)
                if pd.notna(pv) and pv != 0:
                    g = (tot_all[m].get(ys[0]) - pv) / abs(pv) * 100
                    sub += f'<br><span class="{"up" if g >= 0 else "down"}">{"▲" if g >= 0 else "▼"} {g:+.1f}% vs {ys[0] - 1}</span>'
            elif len(sr) > 1 and m in STOCK:
                g = (sr.iloc[-1] - sr.iloc[0]) / abs(sr.iloc[0]) * 100 if sr.iloc[0] else np.nan
                if pd.notna(g):
                    sub += f'<br><span class="{"up" if g >= 0 else "down"}">{"▲" if g >= 0 else "▼"} {g:+.1f}% vs {sr.index[0]}</span>'
            kpi2(col, lab, fmt(v), sub, colr, pad=3)
        st.caption("Produksi & nilai dijumlahkan lintas tahun terpilih; RTP, pembudidaya, dan luas lahan adalah posisi (stok), "
                   "jadi ditampilkan untuk tahun terakhir agar tidak terhitung berulang. " + hidden_note(METS_UI))
        if any(y in years for y in BRIDGED):
            st.caption(f"Tahun {periode([y for y in BRIDGED if y in years])}: baru tersedia data produksi menurut media budidaya; "
                       "variabel lain belum tersedia untuk tahun tersebut.")

    tp = R["total_pembesaran"].sum()
    top = R.nlargest(3, "total_pembesaran")
    if len(top) and tp > 0:
        insight(f"<b>Konsentrasi:</b> 3 wilayah teratas ({', '.join(top.kabupaten)}) menyumbang "
                f"<b>{top.total_pembesaran.sum() / tp * 100:.0f}%</b> volume produksi budidaya periode {per}.")

    l, r = st.columns([3, 2])
    with l:
        ta = tot_all[tot_all[["total_pembesaran", "nilai_rp_juta"]].notna().any(axis=1)]
        if len(ta):
            fig = go.Figure()
            fig.add_bar(x=ta.index, y=ta.total_pembesaran, name="Produksi (ton)",
                        marker_color=["#0077B6" if y in ys else "#BFE6F2" for y in ta.index],
                        text=[short(v) for v in ta.total_pembesaran], textposition="outside",
                        textfont=dict(color=T["heading"], size=12), cliponaxis=False)
            n = ta.nilai_rp_juta.dropna()
            div, ulab = juta_unit(n.max()) if len(n) else (1.0, "Rp juta")
            fig.add_scatter(x=n.index, y=n / div, name=f"Nilai ({ulab})", yaxis="y2", mode="lines+markers+text",
                            text=[f"{v:,.1f}" for v in n / div], textposition="top center",
                            textfont=dict(color="#C2410C", size=12),
                            line=dict(color="#D62828", width=4),
                            marker=dict(size=11, color="#D62828", line=dict(color="white", width=2)))
            fig.update_layout(title="<b>Tren Produksi & Nilai Produksi Budidaya</b><br><sup>batang gelap = tahun terpilih di filter</sup>",
                              hovermode="x unified", height=CH, bargap=.35,
                              yaxis=dict(title=dict(text="Produksi (ton)", font=dict(color="#0077B6"))),
                              yaxis2=dict(title=dict(text=f"Nilai ({ulab})", font=dict(color="#C2410C")), overlaying="y",
                                          side="right", showgrid=False),
                              xaxis=dict(type="category"), legend=dict(orientation="h", y=1.14, x=1, xanchor="right"))
            show(fig)
            sumber(["pembesaran", "bps_nilai"], "volume = KKP Pembesaran, nilai = BPS; dua sumber berbeda, tidak untuk dihitung rasio")
        else:
            st.info("Belum ada data tren produksi/nilai untuk tahun yang dipilih.")
    with r:
        rk = R.dropna(subset=[rank_m]).nlargest(10, rank_m).sort_values(rank_m)
        if len(rk):
            fig = px.bar(rk, x=rank_m, y="kabupaten", orientation="h", color=rank_m, color_continuous_scale=SEQ_OCEAN,
                         title=f"<b>10 Wilayah Teratas {LABEL[rank_m]}</b><br><sup>periode {per}</sup>", height=CH,
                         labels={rank_m: LABEL[rank_m], "kabupaten": ""})
            fig.update_traces(text=rk[rank_m].map(human), textposition="outside",
                              textfont=dict(color=T["heading"], size=12), cliponaxis=False)
            fig.update_layout(coloraxis_showscale=False, xaxis=dict(showticklabels=False, title=""))
            show(fig)
            sumber(SRC_KEYS[rank_m])
        else:
            st.info("Belum ada data lengkap untuk variabel ini pada filter yang dipilih.")

    PR = {"Produksi per pembudidaya (ton/orang)": ("total_pembesaran", "pembudidaya", "ton/orang", 1),
          "Nilai produksi per pembudidaya (Rp juta/orang)": ("nilai_rp_juta", "pembudidaya", "Rp juta/orang", 1),
          "Produksi per hektar lahan (ton/ha)": ("produksi_ton", "luas_lahan_ha", "ton/ha", 5)}
    _hl, _hr = st.columns(2)
    _hl.markdown('<div class="pt" style="margin-top:6px"><div><b>Kontribusi wilayah</b>'
                 '<small>Porsi tiap wilayah terhadap total Jawa Timur.</small></div></div>', unsafe_allow_html=True)
    pk = _hr.selectbox("Ukuran produktivitas", list(PR), key="prod_m")
    l, r = st.columns(2)
    with l:
        tcol = "nilai_rp_juta" if R["nilai_rp_juta"].notna().any() else "total_pembesaran"
        tm = R.dropna(subset=[tcol])
        tm = tm[tm[tcol] > 0].sort_values(tcol, ascending=False)
        if len(tm):
            tp15 = tm.head(15)[["kabupaten", tcol]]
            rest = tm[tcol].iloc[15:].sum()
            if rest > 0:
                tp15 = pd.concat([tp15, pd.DataFrame({"kabupaten": ["Wilayah lainnya"], tcol: [rest]})], ignore_index=True)
            tp15["Provinsi"] = "Jawa Timur"
            fig = px.treemap(tp15, path=["Provinsi", "kabupaten"], values=tcol, color=tcol, color_continuous_scale=SEQ_SUNSET,
                             title=f"<b>Kontribusi Wilayah {LABEL[tcol].split(' (')[0]}</b><br><sup>periode {periode(sorted(F[F[tcol].notna()].tahun.unique()))} · makin luas kotak, makin besar kontribusi</sup>",
                             height=CH)
            fig.update_traces(textinfo="label+percent root", textfont=dict(size=13))
            fig.update_layout(coloraxis_showscale=False)
            show(fig)
            sumber(SRC_KEYS[tcol])
    with r:
        num, den, unit, dmin = PR[pk]
        P = F.dropna(subset=[num, den])
        P = P[P[den] >= dmin]
        if len(P):
            P = P.assign(v=P[num] / P[den]).groupby("kabupaten")["v"].mean().nlargest(10).sort_values().reset_index()
            fig = px.bar(P, x="v", y="kabupaten", orientation="h", color="v", color_continuous_scale=SEQ_SUNSET, height=CH,
                         title=f"<b>Produktivitas 10 Wilayah Tertinggi</b><br><sup>{unit} · rata-rata per tahun, periode {per}</sup>",
                         labels={"v": unit, "kabupaten": ""})
            fig.update_traces(text=P.v.map(lambda x: f"{x:,.1f}"), textposition="outside",
                              textfont=dict(color=T["heading"], size=12), cliponaxis=False)
            fig.update_layout(coloraxis_showscale=False, xaxis=dict(showticklabels=False, title=""))
            show(fig)
            st.caption("Makin tinggi = tiap pembudidaya (atau tiap hektar) menghasilkan lebih banyak. Wilayah dengan komoditas "
                       "bervolume besar seperti rumput laut cenderung tinggi pada ukuran volume.")
            sumber(SRC_KEYS[num] + SRC_KEYS[den])
        else:
            st.info("Data pembilang/penyebut belum lengkap untuk ukuran ini pada filter yang dipilih.")


# ============================================================ 2. PETA
if pi == 1:
    hero(1)
    ns = fbar("mp", kab=False, extra=("Variabel peta", METS_UI, LABEL.get, "map_v"))
    pm = ns.extra
    ty = focus_year(ns.ys, pm)
    if ty is None:
        st.info(f"Belum ada data **{LABEL[pm].split(' (')[0]}** untuk tahun yang dipilih "
                f"({periode(ns.ys) if ns.ys else '-'}). Pilih tahun lain atau unggah data di menu Upload Data.")
        st.stop()
    M = feat[feat.tahun == ty].dropna(subset=[pm])
    if M.empty:
        av = VALID.get(pm, [])
        st.info("Variabel ini belum tersedia untuk tahun yang dipilih." + (f" Tahun yang tersedia: {periode(av)}." if av else ""))
    else:
        nm_ = LABEL[pm].split(" (")[0]
        l, r = st.columns([3, 1])
        with l:
            show(peta(M, pm, None, "sequential", f"<b>{LABEL[pm]} · {ty}</b>", 620, vlabel=nm_))
            sumber(SRC_KEYS[pm], "wilayah abu-abu = belum ada data · * = kota")
        with r:
            mx, mn = M.loc[M[pm].idxmax()], M.loc[M[pm].idxmin()]
            kpi2(r, "Tertinggi", human(mx[pm]), f'<span class="na">{mx.kabupaten}</span>', "#023E8A")
            kpi2(r, "Terendah", human(mn[pm]), f'<span class="na">{mn.kabupaten}</span>', "#00B4D8")
            kpi2(r, "Median wilayah", human(M[pm].median()), f'<span class="na">dari {len(M)} wilayah</span>', "#FB8500")
            kpi2(r, "Cakupan data", f"{len(M)} / {feat.kabupaten.nunique()}", '<span class="na">wilayah yang memiliki data</span>', "#2A9D8F")
        if ty != max(ns.ys):
            st.caption(f"Menampilkan {ty}: tahun terbaru yang dipilih dan memiliki data {nm_.lower()}.")
        kosong = sorted(set(feat.kabupaten) - set(M.kabupaten))
        if kosong:
            st.caption(f"Belum ada data {nm_.lower()} pada {ty} untuk {len(kosong)} wilayah: {', '.join(kosong)}.")
        if PETA_UNK:
            insight(f"Wilayah yang namanya tidak dikenali oleh peta (tidak tampil): <b>{', '.join(PETA_UNK)}</b>.", warn=True)

        # ---- REVISI 2: TABEL DATA PETA + UNDUH CSV ----
        section(f"Tabel Data {LABEL[pm]} {ty}", "Diurutkan dari nilai tertinggi. Tabel dapat diunduh dalam format CSV.")
        tbl = (M[["kabupaten", "tahun", pm]]
               .sort_values(pm, ascending=False)
               .reset_index(drop=True))
        tbl.index = tbl.index + 1
        tbl_show = tbl.rename(columns={"kabupaten": "Kabupaten/Kota", "tahun": "Tahun", pm: PRETTY.get(pm, LABEL[pm])})
        table(tbl_show)
        c_dl1, c_dl2 = st.columns(2)
        c_dl1.download_button(
            f"Unduh tabel peta tahun {ty} (CSV)",
            tbl_show.to_csv(index=False).encode("utf-8"),
            f"peta_{pm}_{ty}.csv", "text/csv", key=f"dl_map_{pm}_{ty}")
        all_tbl = (feat[["kabupaten", "tahun", pm]].dropna(subset=[pm])
                   .sort_values(["tahun", "kabupaten"]).reset_index(drop=True))
        c_dl2.download_button(
            "Unduh semua tahun (CSV)",
            all_tbl.to_csv(index=False).encode("utf-8"),
            f"peta_{pm}_semua_tahun.csv", "text/csv", key=f"dl_map_all_{pm}")


# ============================================================ 3. TIPOLOGI WILAYAH
if pi == 2:
    hero(2)
    if not cluster_years:
        st.warning("Hasil klasterisasi belum tersedia. Unggah data di menu **Upload Data** atau jalankan pembaruan data terlebih dahulu.")
    else:
        # gunakan selectbox tahun (single) khusus menu tipologi
        _kb = st.container(border=True)
        with _kb:
            filter_title()
        ty_sel = _year_ctl(_kb, "kl", single=True, opts=(YEARS_FILTER or cluster_years), default=cluster_years[-1])
        ty = ty_sel
        CL = get_cluster(ty)
        if CL is None:
            insight(f"<b>Tipologi tahun {ty} belum dapat ditampilkan.</b> Hasil klasterisasi baru tersedia untuk tahun {periode(cluster_years)}. "
                    "Pilih salah satu tahun tersebut, atau perbarui data di menu Upload Data.", warn=True)
            st.stop()
        d, names = CL["df"], CL["names"]
        ids = sorted(names)
        cmap = {names[i]: CAT_LIVELY[i % len(CAT_LIVELY)] for i in ids}
        n_total = feat_raw[feat_raw.tahun == ty].kabupaten.nunique()
        n_cl = d.kabupaten.nunique()
        insight(f"<b>Cara membaca:</b> {n_cl} dari {n_total} wilayah pada {ty} dikelompokkan menjadi "
                f"<b>{len(ids)} tipologi</b> berdasarkan kemiripan produksi, RTP, pembudidaya, luas lahan, dan produksi pembesaran. "
                "Wilayah dalam satu tipologi memiliki karakter budidaya yang mirip sehingga bisa diberi kebijakan serupa.")
        if CL["uncl"]:
            insight(f"<b>{len(CL['uncl'])} wilayah belum masuk klaster</b> pada {ty} karena datanya belum lengkap "
                    f"(salah satu/lebih dari: produksi menurut media, RTP, pembudidaya, luas lahan, produksi pembesaran kosong): "
                    f"<b>{', '.join(CL['uncl'])}</b>.<br>", warn=True)
        cols = st.columns(len(ids))
        vk = "total_pembesaran" if "total_pembesaran" in CL["prof"] else CL["prof"].columns[0]
        for col, i in zip(cols, ids):
            g = d[d.klaster == i]
            contoh = ", ".join(g.sort_values(vk, ascending=False).kabupaten.head(3))
            sub = ('<span class="na">Rata-rata per wilayah:</span><br>'
                   + "".join(f'{lab}: <b>{human(CL["prof"].loc[i, c_], unit=u)}</b><br>' for c_, lab, u in
                             (("produksi_ton", "Produksi", "ton"), ("total_pembesaran", "Pembesaran", "ton"),
                              ("pembudidaya", "Pembudidaya", ""), ("luas_lahan_ha", "Luas lahan", "ha")) if c_ in CL["prof"])
                   + (f'Komoditas dominan: <b>{" & ".join(CL["domin"][i])}</b><br>' if CL["domin"].get(i) else "")
                   + f'<span class="na">Contoh: {contoh}</span>')
            kpi2(col, names[i], f"{len(g)} wilayah", sub, CAT_LIVELY[i % len(CAT_LIVELY)], pad=7, compact=True)
        l, r = st.columns(2)
        with l:
            M = d.assign(tahun=ty).copy()
            fig = peta(M, vk, "label_klaster", "categorical", f"<b>Sebaran Tipologi Wilayah ({ty})</b>", 470, labels=40,
                       cmap={names[i]: CAT_LIVELY[i % len(CAT_LIVELY)] for i in ids})
            show(fig)
            sumber(["produksi_jenis_budidaya", "rtp", "pembudidaya", "pembesaran"], "klasterisasi: K-Means")
        with r:
            if CL["shc"]:
                sh = CL["shp"].copy()
                sh.columns = [c.split("::")[1].title() for c in sh.columns]
                sh["Lainnya"] = (1 - sh.sum(axis=1)).clip(lower=0)
                sh.index = [names[i] for i in sh.index]
                lg = (sh * 100).reset_index(names="Tipologi").melt(id_vars="Tipologi", var_name="Komoditas", value_name="Porsi (%)")
                fig = px.bar(lg, x="Porsi (%)", y="Tipologi", color="Komoditas", orientation="h", barmode="stack", height=470,
                             color_discrete_sequence=CAT_LIVELY,
                             title="<b>Komoditas Dominan di Tiap Tipologi</b><br><sup>porsi volume produksi pembesaran rata-rata (%)</sup>",
                             category_orders={"Tipologi": [names[i] for i in ids]})
                fig.update_layout(yaxis_title="", legend=dict(orientation="h", y=-0.15))
                show(fig)
                sumber(["pembesaran"])
            else:
                st.info("Komposisi komoditas belum tersedia untuk tahun ini.")
        pf = CL["prof"].copy()
        pf.index = [names[i] for i in pf.index]
        lg = pf.reset_index(names="Tipologi").melt(id_vars="Tipologi", var_name="v", value_name="Rata-rata")
        lg["v"] = lg.v.map({"produksi_ton": "Produksi (ton)", "total_pembesaran": "Pembesaran (ton)",
                            "pembudidaya": "Pembudidaya (orang)", "rtp": "RTP", "luas_lahan_ha": "Luas lahan (ha)"})
        l3, r3 = st.columns([1, 2])
        with l3:
            cnt = pd.DataFrame({"Tipologi": [names[i] for i in ids], "Wilayah": [int(CL["sizes"][i]) for i in ids]})
            fig = px.pie(cnt, names="Tipologi", values="Wilayah", hole=.56, height=520, color="Tipologi",
                         color_discrete_map=cmap, title="<b>Proporsi Wilayah per Tipologi</b>")
            fig.update_traces(textinfo="value+percent", textfont=dict(size=13, color="white"),
                              marker=dict(line=dict(color=T["card_bg"], width=2)))
            fig.update_layout(legend=dict(orientation="h", y=-0.1, title=""))
            show(fig)
        with r3:
            fig = px.bar(lg, x="Tipologi", y="Rata-rata", color="Tipologi", facet_col="v", facet_col_wrap=3,
                         color_discrete_map=cmap, height=520,
                         title="<b>Karakter Tiap Tipologi</b><br><sup>rata-rata per wilayah (satuan asli)</sup>")
            fig.update_yaxes(matches=None, showticklabels=True, title="")
            fig.update_xaxes(showticklabels=False, title="")
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            fig.update_layout(showlegend=False)
            show(fig)
        section(f"Anggota Tipologi {ty}", "Daftar kabupaten/kota beserta tipologi dan indikator utamanya.")
        mem = d.sort_values(["klaster", vk], ascending=[True, False]).copy()
        out = pd.DataFrame({"Kabupaten/Kota": mem.kabupaten.values, "Tipologi": mem.label_klaster.values})
        for c_, n_ in (("produksi_ton", "Produksi (ton)"), ("total_pembesaran", "Pembesaran (ton)"),
                       ("pembudidaya", "Pembudidaya"), ("rtp", "RTP"), ("luas_lahan_ha", "Luas (ha)")):
            if c_ in mem and mem[c_].notna().any():
                out[n_] = mem[c_].round(0).map(lambda x: "-" if pd.isna(x) else f"{x:,.0f}").values
        table(out)
        if CL["uncl"]:
            st.markdown("**Wilayah belum terklasifikasi:** " + ", ".join(CL["uncl"]))
        with st.expander("Detail metodologi (untuk analis)"):
            ev = read_report("clustering_eval.csv")
            if ev is not None and "silhouette" in ev:
                best = ev.loc[ev.silhouette.idxmax()]
                c = st.columns(3)
                c[0].metric("Jumlah tipologi (k)", int(best["k"]))
                c[1].metric("Silhouette", f"{best['silhouette']:.3f}", help=">0.5 kuat, 0.25–0.5 sedang, <0.25 lemah")
                c[2].metric("Wilayah-tahun terklasifikasi", len(clu))
                fig = go.Figure(go.Scatter(x=ev.k, y=ev.silhouette, mode="lines+markers", line=dict(color="#0077B6", width=3)))
                fig.update_layout(title="<b>Pemilihan k (silhouette)</b>", xaxis_title="k", yaxis_title="silhouette", height=320)
                show(fig)
            else:
                st.caption("Metrik evaluasi klasterisasi belum tersedia.")
            st.caption("Metode: variabel distandarkan, direduksi dengan PCA 2 dimensi, lalu dikelompokkan dengan K-Means. "
                       "Nama tipologi ditentukan oleh aturan ambang pada proses klasterisasi.")


# ============================================================ 4. KOMODITAS & NILAI
if pi == 3:
    hero(3)
    yr, ty, sel, in_sel, F, FACT, ukur, _ = scope(
        "km",
        extra=("Ukur berdasarkan", ["Volume produksi (ton)", "Nilai produksi (Rp)"],
               lambda x: x, "km_u"))
    if ty is None:
        st.info("Belum ada data komoditas untuk tahun yang dipilih. Coba pilih tahun lain atau unggah data baru.")
        st.stop()
    t_kons, t_benih, t_hias = st.tabs(["Budidaya Konsumsi (Pembesaran)", "Pembenihan", "Ikan Hias"])
    with t_kons:
        kt = kom_table(FACT)
        kt = kt[kt.komoditas != "LAINNYA"]
        use_v = ukur.startswith("Volume")
        mc = "vol" if use_v else "nil"
        div, ulab = (1.0, "ton") if use_v else (juta_unit(kt.nil.max() if kt.nil.notna().any() else 0)[0],
                                                juta_unit(kt.nil.max() if kt.nil.notna().any() else 0)[1])
        lbl = "Volume (ton)" if use_v else f"Nilai ({ulab})"
        k0 = kt[kt.tahun == ty].dropna(subset=[mc])
        l, r = st.columns(2)
        with l:
            k1 = k0.groupby("komoditas")[mc].sum().nlargest(10).sort_values().div(div).reset_index()
            if len(k1):
                fig = px.bar(k1, x=mc, y="komoditas", orientation="h", color=mc, color_continuous_scale=SEQ_OCEAN,
                             height=400, title=f"<b>10 Komoditas Terbesar {lbl.split(' (')[0]} ({ty})</b>",
                             labels={mc: lbl, "komoditas": ""})
                fig.update_traces(text=k1[mc].map(lambda x: f"{x:,.1f}" if x < 100 else f"{x:,.0f}"),
                                  textposition="outside", textfont=dict(color=T["heading"], size=12), cliponaxis=False)
                fig.update_layout(coloraxis_showscale=False, xaxis=dict(showticklabels=False, title=""))
                show(fig)
            else:
                st.info(f"Data komoditas {ukur.split(' (')[0].lower()} belum lengkap untuk {ty}.")
            sumber(["pembesaran"], "komoditas 'Lainnya' tidak ditampilkan")
        with r:
            hk = k0.dropna(subset=["vol", "nil"]).groupby("komoditas")[["vol", "nil"]].sum()
            hk = hk[hk.vol > 0]
            hk["harga"] = hk.nil * 1e6 / (hk.vol * 1000)
            hk = hk[hk.harga.between(500, 500_000)].nlargest(12, "vol").sort_values("harga").reset_index()
            if len(hk):
                fig = px.bar(hk, x="harga", y="komoditas", orientation="h", color="harga", color_continuous_scale=SEQ_SUNSET,
                             height=400, title=f"<b>Harga Rata-rata per Kg Komoditas Utama ({ty})</b><br><sup>nilai produksi ÷ volume produksi</sup>",
                             labels={"harga": "Rp/kg", "komoditas": ""})
                fig.update_traces(text=hk.harga.map(lambda x: f"Rp {x:,.0f}"), textposition="outside",
                                  textfont=dict(color=T["heading"], size=12), cliponaxis=False)
                fig.update_layout(coloraxis_showscale=False, xaxis=dict(showticklabels=False, title=""))
                show(fig)
            else:
                st.info("Harga rata-rata per komoditas belum dapat dihitung untuk tahun ini.")
            sumber(["pembesaran"], "harga = nilai ÷ volume, dari sumber yang sama")

        l, r = st.columns(2)
        with l:
            kt2 = kt.dropna(subset=[mc])
            if kt2.tahun.nunique() > 1:
                topk = kt2.groupby("komoditas")[mc].sum().nlargest(6).index
                t1 = kt2[kt2.komoditas.isin(topk)].groupby(["tahun", "komoditas"])[mc].sum().div(div).reset_index()
                fig = px.line(t1, x="tahun", y=mc, color="komoditas", markers=True, height=430,
                              color_discrete_sequence=CAT_LIVELY,
                              title=f"<b>Tren 6 Komoditas Terbesar</b><br><sup>{lbl}</sup>", labels={mc: lbl})
                fig.update_layout(xaxis=dict(dtick=1))
                show(fig)
                sumber(["pembesaran"])
            else:
                st.info("Tren membutuhkan data lengkap minimal dua tahun.")
        with r:
            top_w = k0.groupby("kabupaten")[mc].sum().nlargest(10).index
            if len(top_w):
                top_k = k0.groupby("komoditas")[mc].sum().nlargest(6).index
                c0 = k0[k0.kabupaten.isin(top_w)].copy()
                c0["kom"] = np.where(c0.komoditas.isin(top_k), c0.komoditas, "Lainnya")
                c0 = c0.groupby(["kabupaten", "kom"])[mc].sum().reset_index()
                c0["porsi"] = c0[mc] / c0.groupby("kabupaten")[mc].transform("sum") * 100
                order = list(k0.groupby("kabupaten")[mc].sum().loc[top_w].sort_values().index)
                fig = px.bar(c0, x="porsi", y="kabupaten", color="kom", orientation="h", barmode="stack", height=430,
                             color_discrete_sequence=CAT_LIVELY,
                             title=f"<b>Komposisi Komoditas di 10 Wilayah Terbesar ({ty})</b><br><sup>diurutkan menurut {lbl.split(' (')[0].lower()}; porsi dalam %</sup>",
                             labels={"porsi": "Porsi (%)", "kabupaten": "", "kom": "Komoditas"},
                             category_orders={"kabupaten": order})
                fig.update_layout(legend=dict(orientation="h", y=-0.14))
                show(fig)
                sumber(["pembesaran"])

    def benih_tab(source, vmetrik, vlabel, tag):
        d = usable(FACT[FACT.sumber == source])
        v, n = d[d.metrik == vmetrik], d[d.metrik == "nilai_rp_juta"]
        if v.empty:
            st.info("Data belum tersedia pada filter ini.")
            return
        vt = v[v.tahun == ty]
        if vt.empty:
            st.info(f"Tidak ada data pada {ty}. Tahun tersedia: {periode(sorted(v.tahun.unique()))}.")
            return
        a, b = st.columns(2)
        k1 = vt.assign(komoditas=vt.komoditas.fillna("Tidak dirinci")).groupby("komoditas")["nilai"].sum().nlargest(10).sort_values().reset_index()
        w1 = vt.groupby("kabupaten")["nilai"].sum().nlargest(10).sort_values().reset_index()
        for col, dfp, yc, ttl in ((a, k1, "komoditas", f"10 Komoditas Terbesar ({ty})"),
                                  (b, w1, "kabupaten", f"10 Wilayah Terbesar ({ty})")):
            with col:
                fig = px.bar(dfp, x="nilai", y=yc, orientation="h", color="nilai", color_continuous_scale=SEQ_OCEAN,
                             height=400, title=f"<b>{ttl}</b><br><sup>{vlabel}</sup>", labels={"nilai": vlabel, yc: ""})
                fig.update_traces(text=dfp.nilai.map(short), textposition="outside",
                                  textfont=dict(color=T["heading"], size=12), cliponaxis=False)
                fig.update_layout(coloraxis_showscale=False, xaxis=dict(showticklabels=False, title=""))
                show(fig)
        nt = n[n.tahun == ty].nilai.sum()
        if nt > 0:
            insight(f"Total nilai {tag} {ty}: <b>{human(nt * 1e6, 'Rp ')}</b> dari {vt.kabupaten.nunique()} wilayah.")
        sumber([SRC_DB_KEY[source]])

    with t_benih:
        benih_tab("kkp_pembenihan", "volume_ribu_ekor", "Volume (ribu ekor)", "pembenihan")
    with t_hias:
        benih_tab("kkp_ikan_hias", "volume_ekor", "Volume (ekor)", "ikan hias")


# ============================================================ 5. PROFIL WILAYAH
if pi == 4:
    hero(4)
    ns = fbar("pw", kab=True, single=True, var="total_pembesaran", kab_label="Pilih wilayah (maks. 4; yang pertama jadi fokus)",
              kab_max=4, kab_default=sorted(feat.kabupaten.unique())[:1], kab_placeholder="Pilih wilayah")
    ty, pick = ns.ty, ns.sel
    if ty is None:
        st.info("Belum ada data untuk tahun yang dipilih.")
        st.stop()
    KP = ["total_pembesaran", "nilai_rp_juta", "rtp", "pembudidaya", "luas_lahan_ha"]
    if pick:
        foc = pick[0]
        cur = feat[feat.tahun == ty]
        row = cur[cur.kabupaten == foc]
        c = st.columns(5)
        for col, m in zip(c, KP):
            v = row[m].iloc[0] if len(row) else np.nan
            rank = cur[m].rank(ascending=False)[row.index[0]] if len(row) and pd.notna(v) else None
            col.metric(LABEL[m].split(" (")[0], human(v) if pd.notna(v) else "n/a",
                       f"peringkat {int(rank)}/{cur[m].notna().sum()}" if rank else None, delta_color="off")
        st.caption(hidden_note(KP))
        if not bool(len(row) and row[KP].notna().any(axis=1).iloc[0]):
            insight(f"<b>Data {foc} untuk tahun {ty} belum tersedia.</b> Indikator ditampilkan sebagai n/a dan grafik yang bergantung pada "
                    "tahun ini tidak dapat ditampilkan. Pilih tahun lain, atau cek menu Metadata untuk ketersediaan data.", warn=True)
        CLp = get_cluster(ty)
        if CLp is None:
            _tp = f"hasil klasterisasi tahun {ty} belum tersedia"
        else:
            _g = CLp["df"][CLp["df"].kabupaten == foc]
            _tp = _g.label_klaster.iloc[0] if len(_g) else "belum terklasifikasi (data belum lengkap)"
        lead(f"<b>Tipologi {foc} ({ty}):</b> {_tp}")
        l, r = st.columns([3, 2])
        with l:
            TR = ["total_pembesaran", "nilai_rp_juta", "rtp", "pembudidaya"]
            lg = feat[feat.kabupaten.isin(pick)].melt(id_vars=["kabupaten", "tahun"], value_vars=TR,
                                                       var_name="metrik", value_name="nilai").dropna()
            lg["metrik"] = lg.metrik.map(LABEL)
            if len(lg):
                fig = px.line(lg, x="tahun", y="nilai", color="kabupaten", facet_col="metrik", facet_col_wrap=2,
                              markers=True, color_discrete_sequence=CAT_LIVELY,
                              title=f"<b>Tren Indikator Utama · {', '.join(pick)}</b><br><sup>seluruh tahun yang datanya tersedia</sup>", height=520)
                fig.update_yaxes(matches=None, showticklabels=True, title="")
                fig.update_xaxes(dtick=1, title="")
                fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                show(fig)
            else:
                st.info(f"Data indikator utama untuk {', '.join(pick)} belum tersedia, sehingga tren tidak dapat ditampilkan.")
            sumber(sum([SRC_KEYS[m] for m in TR], []))
        with r:
            med = cur[KP].median()
            rows = []
            for kb in pick:
                r_ = cur[cur.kabupaten == kb]
                for m in KP:
                    v = r_[m].iloc[0] if len(r_) else np.nan
                    if pd.notna(v) and pd.notna(med[m]) and med[m] > 0 and v > 0:
                        rows.append(dict(Wilayah=kb, Indikator=LABEL[m].split(" (")[0],
                                         rasio=v / med[m], nilai=human(v)))
            if rows:
                cm = pd.DataFrame(rows)
                cm["plot"] = cm.rasio.clip(.05, 20)
                cm["kali"] = cm.rasio.map(lambda x: f"{x:.1f}× median")
                fig = px.scatter(cm, x="plot", y="Indikator", color="Wilayah",
                                 hover_data={"nilai": True, "kali": True, "plot": False},
                                 color_discrete_sequence=CAT_LIVELY,
                                 title=f"<b>Posisi {', '.join(pick)} terhadap Median Jawa Timur ({ty})</b><br><sup>garis putus-putus = median (1×) · titik di kanan = di atas median</sup>",
                                 height=520)
                fig.update_traces(marker=dict(size=16, line=dict(color="white", width=1.5)))
                fig.update_xaxes(type="log", tickvals=[.1, .25, .5, 1, 2, 5, 10],
                                 ticktext=["0,1×", "¼×", "½×", "1×", "2×", "5×", "10×"], title="")
                fig.update_yaxes(title="")
                fig.add_vline(x=1, line_dash="dash", line_color="#9AA0A6")
                show(fig)
                sumber(["pembesaran", "rtp", "pembudidaya", "luas_bersih"])
            else:
                st.info(f"Data {', '.join(pick)} untuk {ty} belum tersedia, sehingga perbandingan dengan median tidak dapat ditampilkan.")
        d1, d2 = st.columns(2)
        with d1:
            shr = feat[(feat.kabupaten == foc) & (feat.tahun == ty)]
            shc_ = [c for c in feat.columns if c.startswith("sh::")]
            if len(shr) and shr[shc_].notna().any(axis=None):
                v_ = shr[shc_].iloc[0].dropna()
                v_.index = [c.split("::")[1].title() for c in v_.index]
                v_["Lainnya"] = max(0.0, 1 - v_.sum())
                v_ = v_[v_ > 0]
                show(donut(pd.DataFrame({"Komoditas": v_.index, "Porsi": v_.values}), "Komoditas", "Porsi",
                           f"<b>Komoditas Utama di {foc} ({ty})</b><br><sup>porsi volume produksi pembesaran</sup>",
                           height=380))
                sumber(["pembesaran"])
            else:
                st.info(f"Komposisi komoditas {foc} belum tersedia untuk {ty}.")
        with d2:
            jbw = usable(fact[(fact.kabupaten == foc) & (fact.sumber == "jumlah") &
                              (fact.metrik == "produksi_ton") & fact.jenis_budidaya.notna()])
            jbw = jbw[jbw.tahun.isin(VALID["produksi_ton"])]
            by_ = ty if ty in set(jbw.tahun) else (max(jbw.tahun) if len(jbw) else None)
            gw = jbw[jbw.tahun == by_].groupby("jenis_budidaya")["nilai"].sum() if by_ else pd.Series(dtype=float)
            gw = gw[gw > 0].reset_index()
            if len(gw):
                show(donut(gw, "jenis_budidaya", "nilai",
                           f"<b>Media Budidaya di {foc} ({by_})</b><br><sup>porsi produksi (ton)</sup>", height=380))
                sumber(["produksi_jenis_budidaya"])
            else:
                st.info(f"Produksi menurut media budidaya {foc} belum tersedia.")
    else:
        insight("<b>Pilih minimal satu wilayah</b> pada filter di atas untuk menampilkan profil dan perbandingannya.", warn=True)


# ============================================================ 6. ANALISIS REGRESI & SIMULASI
if pi == 5:
    hero(5)
    ev = read_report("regression_eval.csv")
    insight("<b>Analisis Lanjutan: Mengapa Nilai Produksi Berbeda-beda?</b><br>"
            "Halaman ini menjawab pertanyaan strategis: <b>Jika produksi naik, apakah nilai ikut naik? Seberapa besar dampaknya?</b> "
            "Model yang dilatih pada proses pengolahan data digunakan sebagai dasar estimasi.")
    if ev is None or ev.empty or "cv_r2_mean" not in ev:
        st.warning("Hasil evaluasi regresi belum tersedia. Unggah data di menu **Upload Data** atau jalankan pembaruan data terlebih dahulu.")
    else:
        main_ds = [d for d in ev.dataset.unique() if "raw" not in d.lower() and "rtp" not in d.lower()]
        if not main_ds:
            main_ds = list(ev.dataset.unique())
        main = main_ds[0]
        best = ev[ev.dataset == main].sort_values("cv_r2_mean", ascending=False).iloc[0]
        elastisitas = 1.0
        if "coef" in best.index and pd.notna(best["coef"]):
            elastisitas = float(best["coef"])

        # ---- Alasan pemilihan model (dibanding runner-up) ----
        model_rows = ev[ev.dataset == main].sort_values("cv_r2_mean", ascending=False)
        runner_up = model_rows.iloc[1] if len(model_rows) > 1 else None
        alasan_model = f"R² tertinggi ({best['cv_r2_mean'] * 100:.0f}%)"
        if runner_up is not None:
            alasan_model += (f" dibanding {runner_up['model']} ({runner_up['cv_r2_mean'] * 100:.0f}%) "
                             "pada validasi silang yang sama")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Kekuatan Hubungan (R²)",
            f"{best['cv_r2_mean'] * 100:.0f}%",
            help=(
                f"Angka ini menunjukkan bahwa sekitar {best['cv_r2_mean'] * 100:.0f}% variasi nilai produksi "
                "antarwilayah dapat dijelaskan oleh volume produksi. "
                "Sisanya dipengaruhi faktor lain seperti jenis komoditas, harga jual, dan kualitas produk. "
                "Nilai R² dihitung dari validasi silang, bukan dari data latih."
            ),
        )
        c2.metric(
            "Elastisitas (estimasi)",
            f"{elastisitas:.2f}",
            help=(
                f"Estimasi statistik: jika volume produksi naik 10%, nilai produksi diperkirakan naik sekitar "
                f"{elastisitas * 10:.1f}% - dengan asumsi faktor lain tetap. "
                "Ini bukan jaminan kenaikan aktual; hasil nyata dapat berbeda karena harga pasar, "
                "komposisi komoditas, dan kondisi wilayah."
            ),
        )
        c3.metric(
            "Model Terbaik",
            best["model"],
            help=(
                f"{best['model']} dipilih karena {alasan_model}. "
                "Model ini paling baik menjelaskan hubungan volume dan nilai produksi "
                "pada data historis yang tersedia."
            ),
        )

        # ---- Caption permanen di bawah KPI ----
        st.caption(
            f"R² {best['cv_r2_mean'] * 100:.0f}% berarti model menjelaskan {best['cv_r2_mean'] * 100:.0f}% "
            "variasi nilai produksi; sisanya dijelaskan faktor lain (komoditas, harga, kualitas). "
            f"Elastisitas {elastisitas:.2f} adalah estimasi statistik, bukan jaminan kenaikan aktual. "
            f"Model {best['model']} dipilih karena {alasan_model}."
        )

        if best["cv_r2_mean"] > 0.7:
            st.success("**Temuan Kunci:** Volume produksi adalah faktor **dominan** penentu nilai. "
                       "Fokus pada peningkatan volume (tonase) akan sangat efektif meningkatkan pendapatan wilayah.")
        elif best["cv_r2_mean"] > 0.4:
            st.info("**Temuan Kunci:** Volume produksi berpengaruh **cukup kuat**, namun harga komoditas (jenis ikan) juga "
                    "memegang peranan penting. Diversifikasi komoditas bernilai tinggi perlu dipertimbangkan.")
        else:
            st.warning("**Temuan Kunci:** Hubungan volume dan nilai **lemah**. Artinya, peningkatan volume belum tentu "
                       "meningkatkan nilai secara signifikan. Faktor lain (kualitas, harga jual, jenis komoditas) lebih dominan.")

        sim_head("Simulator Proyeksi Dampak Produksi",
                 "Ubah skenario kenaikan volume produksi untuk melihat estimasi dampaknya terhadap nilai produksi Jawa Timur.",
                 f"Model {best['model']} · R² {best['cv_r2_mean'] * 100:.0f}%")
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            with st.container(border=True):
                panel_title("1", "Tentukan skenario", "Geser slider untuk mengubah asumsi kenaikan volume.")
                kenaikan = st.slider("Kenaikan Volume Produksi (%)", 0, 100, 10, step=5)
                _yn = max(VALID["nilai_rp_juta"], default=None)
                nilai_now = feat[feat.tahun == _yn]["nilai_rp_juta"].sum(skipna=True) * 1e6 if _yn else 0
                st.caption(f"Dasar perhitungan: total nilai produksi tahun {_yn}." if _yn else "Data nilai produksi belum tersedia.")
                nilai_new = nilai_now * (1 + (kenaikan / 100 * elastisitas))
                delta = nilai_new - nilai_now
                st.metric("Estimasi Total Nilai Produksi Baru", f"Rp {human(nilai_new)}", delta=f"Rp {human(delta)}")
                st.caption("*Estimasi kasar berdasarkan elastisitas model; hasil nyata dapat berbeda.")
        with col_s2:
            with st.container(border=True):
                panel_title("2", "Hasil proyeksi", "Perbandingan nilai produksi saat ini dengan hasil simulasi.")
                fig_sim = go.Figure(go.Bar(
                    x=["Nilai Saat Ini", f"Simulasi (+{kenaikan}%)"],
                    y=[nilai_now, nilai_new],
                    text=[f"Rp {human(nilai_now)}", f"Rp {human(nilai_new)}"],
                    textposition="outside",
                    marker_color=["#0077B6", "#FB8500"],
                ))
                fig_sim.update_layout(title="<b>Perbandingan Nilai Produksi (Simulasi)</b>",
                                      height=320, yaxis_title="Rp", showlegend=False, margin=dict(t=40, b=10))
                show(fig_sim)

        with st.expander("Detail Teknis & Perbandingan Model"):
            g_ = ev.assign(Dataset=ev.dataset.map(lambda x: x.replace("_", " ").title()),
                           cv=(ev.cv_r2_mean * 100).round(1))
            fig = px.bar(g_, x="Dataset", y="cv", color="model", barmode="group", height=400,
                         color_discrete_sequence=CAT_LIVELY,
                         title="<b>Perbandingan Performa Model (R²)</b>",
                         labels={"cv": "R² (%)", "model": "Model"})
            fig.update_traces(texttemplate="%{y:.0f}%", textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_title="", legend=dict(orientation="h", y=-0.2, title=""))
            show(fig)
            st.dataframe(ev[["dataset", "model", "cv_r2_mean", "r2_test"]].round(3))
            if mv is not None and len(mv):
                subhead("Riwayat versi model")
                st.dataframe(mv.tail(10))


# ============================================================ 7. UPLOAD DATA
if pi == 6:
    hero(6)
    insight("Unggah data mentah terbaru, lalu dashboard memprosesnya <b>berurutan dan otomatis</b>: "
            "pembersihan data → pembuatan fitur → klasterisasi → regresi → penyimpanan ke database → tampilan diperbarui.")
    t_up, t_st = st.tabs(["Unggah & Proses", "Riwayat & Status"])
    with t_up:
        if S.get("up_before"):
            n0, y0 = S.pop("up_before")
            if len(fact) != n0 or tuple(years) != tuple(y0):
                st.success(f"Dashboard diperbarui. Baris data: {n0:,} → {len(fact):,} · tahun: "
                           f"{periode(list(y0)) if y0 else '-'} → {periode(years)}.")
            else:
                st.warning("Proses selesai, tetapi isi data tidak berubah. Periksa apakah jenis data yang dipilih "
                           "sesuai dengan data yang diunggah.")
        sk = st.selectbox("1. Jenis data yang diunggah", list(UPLOAD_SRC), key="up_src")
        url_, thn_ = UPLOAD_SRC[sk]
        st.caption(f"Cakupan tahun: **{thn_}** · unduh data terbaru dari [sumber resmi]({url_})")
        fl = st.file_uploader("2. Data mentah (CSV / Excel)", type=["csv", "xlsx", "xls"], key="up_file")
        ok_file = False
        if fl is not None:
            try:
                raw = pd.read_csv(fl, sep=None, engine="python") if fl.name.lower().endswith(".csv") else pd.read_excel(fl)
                fl.seek(0)
            except Exception as e:
                raw = None
                st.error(f"Data tidak dapat dibaca: {type(e).__name__}: {e}")
            if raw is not None:
                if raw.empty:
                    st.error("Data kosong.")
                else:
                    ok_file = True
                    tcols = [c for c in raw.columns if "tahun" in str(c).lower()]
                    pool = pd.Series(list(raw.columns) + (raw[tcols].stack().tolist() if tcols else []))
                    yrs = sorted({int(v) for v in pd.to_numeric(pool, errors="coerce").dropna() if 2000 <= v <= 2100})
                    m = st.columns(3)
                    m[0].metric("Baris", f"{len(raw):,}")
                    m[1].metric("Kolom", len(raw.columns))
                    m[2].metric("Tahun terdeteksi", periode(yrs) if yrs else "tidak terdeteksi")
                    st.dataframe(raw.head(8))
        subhead("Proses & perbarui dashboard")
        st.caption("Proses dapat memakan waktu beberapa menit (termasuk pencarian model regresi). "
                   "Jangan menutup halaman saat berjalan.")
        if st.button("Proses & perbarui dashboard", key="up_run", disabled=not ok_file):
            import traceback
            S["up_before"] = (len(fact), tuple(years))
            ok_run = False
            box = st.status("Memproses data...", expanded=True) if hasattr(st, "status") else st.container()
            try:
                res = run_update(fl.getvalue(), fl.name, lambda t_: box.write("• " + t_ + " ..."))
                ok_run = res["ok"]
                if hasattr(box, "update"):
                    box.update(label="Selesai", state="complete")
                if res.get("cluster_dropped"):
                    st.warning(f"{res['cluster_dropped']} baris klasterisasi dilewati karena nama wilayahnya belum terdaftar.")
            except Exception as e:
                S.pop("up_before", None)
                if hasattr(box, "update"):
                    box.update(label="Gagal", state="error")
                st.error(f"Proses berhenti: {type(e).__name__}: {e}")
                with st.expander("Detail teknis"):
                    st.code(traceback.format_exc()[-1800:])
            if ok_run:
                st.cache_data.clear()
                st.rerun()
    with t_st:
        fm_raw = DB["features_model"]
        upd = pd.to_datetime(fm_raw["updated_at"], errors="coerce").max() if fm_raw is not None and "updated_at" in fm_raw else None
        c = st.columns(4)
        c[0].metric("Baris data terintegrasi", f"{len(fact):,}")
        c[1].metric("Rentang tahun", periode(years) if years else "-")
        c[2].metric("Wilayah", feat.kabupaten.nunique())
        c[3].metric("Terakhir diperbarui", f"{upd:%d %b %Y}" if pd.notna(upd) else "n/a")
        rw = DB.get("raw_budidaya")
        tabel = pd.DataFrame([
            ("Data mentah", len(rw) if rw is not None else 0, "Data hasil unggahan sebelum diolah"),
            ("Data terintegrasi", len(DB["fact"]), "Hasil pembersihan dan penyatuan semua sumber"),
            ("Fitur wilayah", len(fm_raw) if fm_raw is not None else 0, "Ringkasan per kabupaten/kota dan tahun"),
            ("Hasil klasterisasi", len(clu) if clu is not None else 0, "Tipologi wilayah"),
            ("Riwayat model", len(mv) if mv is not None else 0, "Versi model regresi"),
        ], columns=["Data", "Baris", "Isi"])
        table(tabel)
        if rw is not None and len(rw) and "upload_batch" in rw:
            subhead("Riwayat pembaruan data")
            g = rw.groupby("upload_batch").agg(
                Baris=("nilai", "size"),
                Tahun=("tahun", lambda x_: periode(sorted({int(v) for v in x_.dropna()})) if x_.notna().any() else "-"),
                Sumber=("sumber", lambda x_: ", ".join(sorted({str(v) for v in x_.dropna()})[:5])))
            if "uploaded_at" in rw:
                g["Waktu"] = pd.to_datetime(rw.groupby("upload_batch")["uploaded_at"].max(), errors="coerce").dt.strftime("%d %b %Y %H:%M")
            table(g.reset_index().rename(columns={"upload_batch": "Batch"}))
        for n_ in DB_NOTES:
            st.caption("" + n_)
        if st.button("Muat ulang dari database", key="up_reload"):
            st.cache_data.clear()
            st.rerun()


# ============================================================ 8. METADATA
if pi == 7:
    hero(7)
    t_kamus, t_sumber, t_ada, t_met = st.tabs(["Kamus Data", "Sumber Data", "Ketersediaan Data", "Metodologi & Catatan"])
    nw = lambda m: int(feat_raw.loc[feat_raw[m].fillna(0) > 0, "kabupaten"].nunique()) if m in feat_raw else 0
    with t_kamus:
        lead("Daftar variabel yang dipakai di dashboard beserta arti, satuan, dan sumbernya.")
        kamus = pd.DataFrame([
            ("Produksi Budidaya", "Volume hasil budidaya pembesaran seluruh komoditas", "ton", "Arus (dijumlahkan antar tahun)",
             "KKP · Pembesaran", f"{nw('total_pembesaran')} wilayah. Rumput laut bervolume sangat besar"),
            ("Nilai Produksi", "Nilai rupiah hasil budidaya menurut BPS", "Rp juta", "Arus", "BPS Jatim",
             "Hanya tersedia untuk tahun tertentu (lihat tab Ketersediaan Data)"),
            ("Produksi menurut Media", "Volume produksi per media budidaya (kolam, tambak, laut, dll.)", "ton", "Arus",
             "OpenData Jatim", f"Hanya {nw('produksi_ton')} wilayah; angka berbeda dari Produksi Budidaya karena sumber & cakupan berbeda"),
            ("Rumah Tangga Perikanan (RTP)", "Rumah tangga yang mengusahakan budidaya", "RTP",
             "Stok (posisi tahun tertentu)", "OpenData Jatim", f"{nw('rtp')} wilayah"),
            ("Pembudidaya", "Jumlah orang pembudidaya ikan", "orang", "Stok", "KKP · Pembudidaya", f"{nw('pembudidaya')} wilayah"),
            ("Luas Lahan", "Luas area budidaya", "hektar", "Stok", "OpenData Jatim", f"{nw('luas_lahan_ha')} wilayah"),
            ("Harga rata-rata per kg", "Nilai produksi ÷ volume produksi komoditas", "Rp/kg", "Turunan",
             "KKP Pembesaran / BPS", "Hanya dihitung bila nilai dan volume dari sumber yang sama"),
            ("Produktivitas", "Produksi atau nilai dibagi jumlah pembudidaya / luas lahan", "ton/orang, Rp juta/orang, ton/ha",
             "Turunan", "Gabungan", "Rata-rata per tahun"),
            ("Porsi komoditas", "Persentase volume suatu komoditas terhadap total produksi wilayah", "%", "Turunan",
             "KKP · Pembesaran", "Dasar penentuan tipologi wilayah"),
            ("Tipologi wilayah", "Kelompok wilayah dengan karakter budidaya mirip (K-Means)", "kategori", "Hasil analisis",
             "Hasil klasterisasi", "Dihitung pada proses pengolahan data; dashboard hanya menampilkan"),
            ("Volume benih", "Jumlah benih yang dihasilkan unit pembenihan", "ribu ekor", "Arus", "KKP · Pembenihan", ""),
            ("Volume ikan hias", "Jumlah ikan hias yang dihasilkan", "ekor", "Arus", "KKP · Ikan hias", ""),
        ], columns=["Variabel", "Arti", "Satuan", "Jenis", "Sumber", "Catatan"])
        table(kamus)
        st.download_button("Unduh kamus data (CSV)", kamus.to_csv(index=False).encode(), "kamus_data.csv", "text/csv")
    with t_sumber:
        lead("Cakupan sebenarnya di database/data aktif untuk setiap sumber dan metrik.")
        sm = (fact.groupby(["sumber", "metrik"])
              .agg(satuan=("satuan", lambda s: s.dropna().iloc[0] if s.notna().any() else "-"),
                   tahun_min=("tahun", "min"), tahun_max=("tahun", "max"),
                   wilayah=("kabupaten", "nunique"), baris=("nilai", "size")).reset_index())
        sm["Dataset"] = sm.sumber.map(lambda s: SRC_DB.get(s, s))
        sm["Variabel"] = sm.metrik.map(lambda m: METRIK_NAME.get(m, m))
        sm["Tahun"] = sm.tahun_min.astype(str) + "–" + sm.tahun_max.astype(str)
        sm["Tautan"] = [(f'<a href="{u}" target="_blank">buka</a>' if u else "-")
                        for u in (link_for(s_, m_) for s_, m_ in zip(sm.sumber, sm.metrik))]
        table(sm[["Dataset", "Variabel", "satuan", "Tahun", "wilayah", "baris", "Tautan"]]
              .rename(columns={"satuan": "Satuan"}))
        st.caption(f"Sumber aktif: {base_src}" + (f" + {len(ups)} upload" if ups else "") +
                   f" · dimuat {pd.Timestamp.now():%d %b %Y %H:%M}")
    with t_ada:
        lead("Dashboard hanya menampilkan tahun yang datanya <b>cukup lengkap</b>. "
             "Tahun yang tidak lengkap tetap tercatat di sini.")
        yy = sorted(int(y) for y in feat_raw.tahun.unique())
        rows = []
        for m in METS_UI:
            row = {"Variabel": LABEL[m]}
            for y in yy:
                n_ = int((feat_raw.loc[feat_raw.tahun == y, m].fillna(0) > 0).sum())
                row[str(y)] = f"✓ {n_}" if y in VALID[m] else (f"! {n_}" if n_ else "—")
            rows.append(row)
        table(pd.DataFrame(rows))
        st.caption("✓ = ditampilkan (angka = jumlah wilayah yang datanya ada) · ! = ada data tetapi belum lengkap, disembunyikan · — = tidak ada data.")
        rw = DB.get("raw_budidaya")
        if rw is not None and len(rw) and {"sumber", "metrik", "tahun", "nilai"} <= set(rw.columns):
            subhead("Data mentah di database (termasuk tahun yang belum masuk analisis)")
            rg = rw.assign(nol=(rw.nilai.fillna(0) == 0)).groupby(["sumber", "metrik", "tahun"]).agg(
                n=("nilai", "size"), nol=("nol", "mean")).reset_index()
            rg["sel"] = [("!" if z >= .5 else "✓") + f" {n}" + (f" · {z * 100:.0f}% nol" if z >= .5 else "")
                         for n, z in zip(rg.n, rg.nol)]
            pv = rg.pivot_table(index=["sumber", "metrik"], columns="tahun", values="sel", aggfunc="first").fillna("—").reset_index()
            pv["sumber"] = pv.sumber.map(lambda s_: SRC_DB.get(s_, s_))
            pv["metrik"] = pv.metrik.map(lambda m_: METRIK_NAME.get(m_, m_))
            pv.columns = [str(c) for c in pv.columns]
            table(pv.rename(columns={"sumber": "Dataset", "metrik": "Variabel"}))
            st.caption("Angka = jumlah baris. ! = sebagian besar nilainya nol (data tahun tersebut belum terisi).")
        alasan = [f"**{LABEL[m]}** {y}: {w}" for m in METS_UI for y, w in GATE_WHY[m].items()]
        if alasan:
            subhead("Alasan tahun disembunyikan")
            st.markdown("  \n".join(alasan))
    with t_met:
        section("Bagaimana data menjadi wawasan?",
                "Ringkasan proses pengolahan agar hasil dashboard tetap konsisten, dapat dipahami, dan transparan.")
        _mt = [
            ("Alur Data", "Data mentah dari sumber resmi → pembersihan → data terintegrasi di database → pembuatan fitur → "
                          "klasterisasi → regresi → dashboard. Dashboard hanya <b>membaca</b> hasilnya lalu merangkum dan memvisualisasikannya."),
            ("Pembersihan Data", "Baris yang diberi tanda <i>skala janggal</i> atau <i>tahun kosong</i> saat pembersihan tidak ikut diolah. "
                                 "Fitur disimpan per kabupaten/kota dan tahun, dengan nilai ekstrem dipangkas (winsorize 1–99%), "
                                 "sehingga angka total pada fitur bisa sedikit berbeda dari penjumlahan langsung data mentah."),
            ("Kelengkapan Tahun", f"Tahun ditampilkan untuk sebuah variabel bila cakupan wilayahnya minimal {GATE_MIN_COV * 100:.0f}% dari tahun terbaik "
                                  f"dan totalnya minimal {GATE_MIN_TOT * 100:.0f}% dari median tahun lain, agar data yang belum lengkap tidak terbaca "
                                  "sebagai penurunan nyata. Ini hanya penyaring tampilan."),
            ("Mengapa Ada Beberapa Angka Produksi?", "<i>Produksi Budidaya (pembesaran)</i> berasal dari KKP, <i>Produksi menurut Media</i> dari "
                                                     "OpenData Jatim, dan <i>Nilai Produksi</i> dari BPS. Sumbernya berbeda sehingga tidak dijumlahkan "
                                                     "atau dibandingkan langsung. Harga per kg hanya dihitung dari volume dan nilai yang sama sumbernya."),
            ("Tipologi Wilayah", "K-Means pada produksi, RTP, pembudidaya, luas lahan, dan produksi pembesaran (distandarkan, lalu PCA 2 dimensi). "
                                 "Nama tipologi berasal dari aturan ambang. Hanya wilayah-tahun dengan kelima variabel lengkap yang terklasifikasi."),
            ("Analisis Regresi", "Model Linear, Ridge, dan Lasso dibandingkan; model terbaik dipilih dari validasi silang. "
                                 "Hasilnya bersifat statistik, bukan sebab-akibat."),
            ("Peta", "Peta ditampilkan sebagai choropleth bila data batas wilayah kabupaten/kota tersedia; jika tidak, dipakai peta titik "
                     "(scatter ring) dengan warna kontras pada peta dasar terang."),
            ("Keterbatasan", "Koordinat peta adalah titik pusat perkiraan wilayah."),
        ]
        st.markdown('<div class="mg">' + "".join(
            f'<div class="mc"><span class="mn">{i:02d}</span><div><b>{t_}</b><p>{d_}</p></div></div>'
            for i, (t_, d_) in enumerate(_mt, 1)) + '</div>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        d1.download_button("Unduh fitur aktif (CSV)",
                           feat.drop(columns=[c for c in feat.columns if c.startswith("sh::")]).to_csv(index=False).encode(),
                           "fitur_aktif.csv", "text/csv")
st.markdown('<div class="dfoot"><span>Dashboard Perikanan Budidaya Jawa Timur</span><span>Data diolah dari sumber resmi pemerintah</span></div>',
            unsafe_allow_html=True)