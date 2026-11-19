# Project Analisis Data

Template proyek untuk membaca, membersihkan, mengeksplorasi, mengelompokkan, dan membuat model regresi dari dataset Excel/CSV.

## Struktur
- `data/raw/`: letakkan file Excel asli di sini (misalnya 46 file `.xlsx`).
- `data/processed/`: hasil cleaning dalam format CSV.
- `src/`: fungsi inti yang dipakai skrip.
- `scripts/`: skrip pipeline untuk cleaning, EDA, clustering, dan regresi.
- `app/streamlit_app.py`: dashboard Streamlit sederhana.
- `output/`: laporan, model, dan visualisasi.

## Instalasi
Disarankan memakai virtual environment.

### Windows
```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Cara menjalankan
1. Salin semua file Excel mentah ke `data/raw/`.
2. Jalankan cleaning:
   ```bash
   python scripts/01_cleaning.py
   ```
3. Buat ringkasan EDA:
   ```bash
   python scripts/02_eda_features.py
   ```
4. Jalankan clustering interaktif:
   ```bash
   python scripts/03_clustering.py
   ```
5. Jalankan regresi interaktif:
   ```bash
   python scripts/04_regression.py
   ```
6. Jalankan dashboard:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Catatan
- Folder `data/raw/` dibuat kosong karena file Excel asli belum disertakan dalam template ZIP ini. Salin 46 file asli ke folder tersebut setelah ekstraksi.
- Periksa nama dan tipe kolom terlebih dahulu sebelum memilih fitur/target untuk clustering atau regresi.
- Hasil analisis perlu divalidasi sebelum digunakan untuk kesimpulan.
