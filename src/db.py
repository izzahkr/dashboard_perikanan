import pandas as pd
from sqlalchemy import create_engine, text
from .config import DB_CONFIG


def get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(
        url,
        connect_args={} if DB_CONFIG["host"] == "localhost" else {"sslmode": "require"},
    )


def init_schema():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_kabupaten (
                kabupaten_id SERIAL PRIMARY KEY,
                nama_kabupaten VARCHAR(100) UNIQUE NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_budidaya (
                id SERIAL PRIMARY KEY,
                upload_batch VARCHAR(50),
                kabupaten VARCHAR(100),
                tahun INTEGER,
                jenis_budidaya VARCHAR(50),
                metrik VARCHAR(50),
                nilai FLOAT,
                satuan VARCHAR(20),
                sumber VARCHAR(50),
                uploaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_budidaya (
                id SERIAL PRIMARY KEY,
                kabupaten_id INTEGER REFERENCES dim_kabupaten(kabupaten_id),
                tahun INTEGER NOT NULL,
                jenis_budidaya VARCHAR(50),
                metrik VARCHAR(50) NOT NULL,
                nilai FLOAT,
                satuan VARCHAR(20),
                sumber VARCHAR(50),
                kegiatan VARCHAR(50),
                komoditas VARCHAR(50),
                is_suspect_scale BOOLEAN DEFAULT FALSE,
                is_missing_year BOOLEAN DEFAULT FALSE,
                is_stale BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (kabupaten_id, tahun, jenis_budidaya, metrik, kegiatan, komoditas)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS features_model (
                id SERIAL PRIMARY KEY,
                kabupaten_id INTEGER REFERENCES dim_kabupaten(kabupaten_id),
                tahun INTEGER NOT NULL,
                produksi_ton FLOAT,
                nilai_rp_juta FLOAT,
                rtp FLOAT,
                pembudidaya FLOAT,
                luas_lahan_ha FLOAT,
                total_pembesaran FLOAT,
                share_rumput_laut FLOAT,
                share_udang FLOAT,
                share_bandeng FLOAT,
                share_lele FLOAT,
                share_nila FLOAT,
                share_gurami FLOAT,
                share_patin FLOAT,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (kabupaten_id, tahun)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cluster_assignments (
                id SERIAL PRIMARY KEY,
                kabupaten_id INTEGER REFERENCES dim_kabupaten(kabupaten_id),
                tahun INTEGER NOT NULL,
                klaster INTEGER,
                label_klaster VARCHAR(100),
                produksi_ton FLOAT,
                rtp FLOAT,
                pembudidaya FLOAT,
                luas_lahan_ha FLOAT,
                total_pembesaran FLOAT,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (kabupaten_id, tahun)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_versions (
                version_id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                data_hash VARCHAR(20),
                model_name VARCHAR(100),
                cv_r2 FLOAT,
                notes TEXT
            );
        """))

    print('✓ Schema initialized.')


def upsert_kabupaten(df: pd.DataFrame):
    engine = get_engine()
    uniq = df['kabupaten'].dropna().unique()
    with engine.begin() as conn:
        for nama in uniq:
            conn.execute(text("""
                INSERT INTO dim_kabupaten (nama_kabupaten) VALUES (:nama)
                ON CONFLICT (nama_kabupaten) DO NOTHING;
            """), {'nama': nama})
    print(f'✓ dim_kabupaten: {len(uniq)} kabupaten di-cek.')


def get_kabupaten_map() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql("SELECT kabupaten_id, nama_kabupaten FROM dim_kabupaten", conn)


def upsert_raw(df: pd.DataFrame, batch_name: str = 'manual_upload'):
    engine = get_engine()
    df = df.copy()
    df['upload_batch'] = batch_name
    cols = ['upload_batch', 'kabupaten', 'tahun', 'jenis_budidaya', 'metrik', 'nilai', 'satuan', 'sumber']
    df = df[[c for c in cols if c in df.columns]]
    df.to_sql('raw_budidaya', engine, if_exists='append', index=False)
    print(f'✓ raw_budidaya: {len(df)} baris di-append (batch={batch_name}).')


def upsert_fact(df: pd.DataFrame) -> int:
    engine = get_engine()
    upsert_kabupaten(df)
    kab_map = get_kabupaten_map()
    df = df.merge(kab_map, left_on='kabupaten', right_on='nama_kabupaten', how='left')

    n_insert, n_update = 0, 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            if pd.isna(row['kabupaten_id']):
                continue
            res = conn.execute(text("""
                INSERT INTO fact_budidaya
                    (kabupaten_id, tahun, jenis_budidaya, metrik, nilai, satuan,
                     sumber, kegiatan, komoditas, is_suspect_scale, is_missing_year, is_stale)
                VALUES
                    (:kab_id, :tahun, :jenis, :metrik, :nilai, :satuan,
                     :sumber, :kegiatan, :komoditas, :suspect, :missing, :stale)
                ON CONFLICT (kabupaten_id, tahun, jenis_budidaya, metrik, kegiatan, komoditas)
                DO UPDATE SET
                    nilai = EXCLUDED.nilai, satuan = EXCLUDED.satuan,
                    sumber = EXCLUDED.sumber,
                    is_suspect_scale = EXCLUDED.is_suspect_scale,
                    is_missing_year = EXCLUDED.is_missing_year,
                    is_stale = EXCLUDED.is_stale,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted;
            """), {
                'kab_id': int(row['kabupaten_id']),
                'tahun': int(row['tahun']),
                'jenis': row.get('jenis_budidaya'),
                'metrik': row['metrik'],
                'nilai': None if pd.isna(row['nilai']) else float(row['nilai']),
                'satuan': row.get('satuan'),
                'sumber': row.get('sumber'),
                'kegiatan': row.get('kegiatan'),
                'komoditas': row.get('komoditas'),
                'suspect': bool(row.get('is_suspect_scale', False)),
                'missing': bool(row.get('is_missing_year', False)),
                'stale': bool(row.get('is_stale', False)),
            })
            if res.fetchone()[0]:
                n_insert += 1
            else:
                n_update += 1
    print(f'✓ fact_budidaya: {n_insert} inserted, {n_update} updated.')
    return n_insert + n_update


def upsert_features(df: pd.DataFrame) -> int:
    engine = get_engine()
    upsert_kabupaten(df)
    kab_map = get_kabupaten_map()
    df = df.merge(kab_map, left_on='kabupaten', right_on='nama_kabupaten', how='left')

    n_insert, n_update = 0, 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            if pd.isna(row['kabupaten_id']):
                continue
            res = conn.execute(text("""
                INSERT INTO features_model
                    (kabupaten_id, tahun, produksi_ton, nilai_rp_juta, rtp, pembudidaya,
                     luas_lahan_ha, total_pembesaran, share_rumput_laut, share_udang,
                     share_bandeng, share_lele, share_nila, share_gurami, share_patin)
                VALUES
                    (:kab_id, :tahun, :prod, :nilai, :rtp, :pemb, :luas, :tot,
                     :s_rl, :s_ud, :s_bd, :s_ll, :s_nl, :s_gr, :s_pt)
                ON CONFLICT (kabupaten_id, tahun)
                DO UPDATE SET
                    produksi_ton = EXCLUDED.produksi_ton,
                    nilai_rp_juta = EXCLUDED.nilai_rp_juta,
                    rtp = EXCLUDED.rtp,
                    pembudidaya = EXCLUDED.pembudidaya,
                    luas_lahan_ha = EXCLUDED.luas_lahan_ha,
                    total_pembesaran = EXCLUDED.total_pembesaran,
                    share_rumput_laut = EXCLUDED.share_rumput_laut,
                    share_udang = EXCLUDED.share_udang,
                    share_bandeng = EXCLUDED.share_bandeng,
                    share_lele = EXCLUDED.share_lele,
                    share_nila = EXCLUDED.share_nila,
                    share_gurami = EXCLUDED.share_gurami,
                    share_patin = EXCLUDED.share_patin,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted;
            """), {
                'kab_id': int(row['kabupaten_id']),
                'tahun': int(row['tahun']),
                'prod': row.get('produksi_ton'),
                'nilai': row.get('nilai_rp_juta'),
                'rtp': row.get('rtp'),
                'pemb': row.get('pembudidaya'),
                'luas': row.get('luas_lahan_ha'),
                'tot': row.get('total_pembesaran'),
                's_rl': row.get('share_rumput_laut'),
                's_ud': row.get('share_udang'),
                's_bd': row.get('share_bandeng'),
                's_ll': row.get('share_lele'),
                's_nl': row.get('share_nila'),
                's_gr': row.get('share_gurami'),
                's_pt': row.get('share_patin'),
            })
            if res.fetchone()[0]:
                n_insert += 1
            else:
                n_update += 1
    print(f'✓ features_model: {n_insert} inserted, {n_update} updated.')
    return n_insert + n_update


def upsert_cluster(df: pd.DataFrame) -> int:
    engine = get_engine()
    upsert_kabupaten(df)
    kab_map = get_kabupaten_map()
    df = df.merge(kab_map, left_on='kabupaten', right_on='nama_kabupaten', how='left')

    n_insert, n_update = 0, 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            if pd.isna(row['kabupaten_id']):
                continue
            res = conn.execute(text("""
                INSERT INTO cluster_assignments
                    (kabupaten_id, tahun, klaster, label_klaster,
                     produksi_ton, rtp, pembudidaya, luas_lahan_ha, total_pembesaran)
                VALUES
                    (:kab_id, :tahun, :klaster, :label,
                     :prod, :rtp, :pemb, :luas, :tot)
                ON CONFLICT (kabupaten_id, tahun)
                DO UPDATE SET
                    klaster = EXCLUDED.klaster,
                    label_klaster = EXCLUDED.label_klaster,
                    produksi_ton = EXCLUDED.produksi_ton,
                    rtp = EXCLUDED.rtp,
                    pembudidaya = EXCLUDED.pembudidaya,
                    luas_lahan_ha = EXCLUDED.luas_lahan_ha,
                    total_pembesaran = EXCLUDED.total_pembesaran,
                    updated_at = NOW()
                RETURNING (xmax = 0) AS inserted;
            """), {
                'kab_id': int(row['kabupaten_id']),
                'tahun': int(row['tahun']),
                'klaster': int(row['klaster']),
                'label': row.get('label_klaster'),
                'prod': row.get('produksi_ton'),
                'rtp': row.get('rtp'),
                'pemb': row.get('pembudidaya'),
                'luas': row.get('luas_lahan_ha'),
                'tot': row.get('total_pembesaran'),
            })
            if res.fetchone()[0]:
                n_insert += 1
            else:
                n_update += 1
    print(f'✓ cluster_assignments: {n_insert} inserted, {n_update} updated.')
    return n_insert + n_update


def save_model_version(data_hash: str, model_name: str, cv_r2: float, notes: str = ''):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO model_versions (data_hash, model_name, cv_r2, notes)
            VALUES (:hash, :model, :r2, :notes);
        """), {'hash': data_hash, 'model': model_name, 'r2': cv_r2, 'notes': notes})
    print(f'✓ model_versions: {model_name} (R²={cv_r2:.4f}) dicatat.')

# QUERY DASHBOARD
def query_fact(tahun: int = None) -> pd.DataFrame:
    engine = get_engine()
    q = """
        SELECT f.tahun, k.nama_kabupaten AS kabupaten, f.jenis_budidaya,
               f.metrik, f.nilai, f.satuan, f.sumber, f.kegiatan, f.komoditas
        FROM fact_budidaya f
        JOIN dim_kabupaten k ON f.kabupaten_id = k.kabupaten_id
    """
    params = {}
    if tahun:
        q += " WHERE f.tahun = :tahun"
        params['tahun'] = int(tahun)
    with engine.connect() as conn:
        return pd.read_sql(text(q), conn, params=params)


def query_cluster(tahun: int = None) -> pd.DataFrame:
    engine = get_engine()
    q = """
        SELECT c.tahun, k.nama_kabupaten AS kabupaten, c.klaster, c.label_klaster,
               c.produksi_ton, c.rtp, c.pembudidaya, c.luas_lahan_ha, c.total_pembesaran
        FROM cluster_assignments c
        JOIN dim_kabupaten k ON c.kabupaten_id = k.kabupaten_id
    """
    params = {}
    if tahun:
        q += " WHERE c.tahun = :tahun"
        params['tahun'] = int(tahun)

    with engine.connect() as conn:
        return pd.read_sql(text(q), conn, params=params)


def query_features(tahun: int = None) -> pd.DataFrame:
    engine = get_engine()
    q = """
        SELECT f.tahun, k.nama_kabupaten AS kabupaten, f.produksi_ton, f.nilai_rp_juta,
               f.rtp, f.pembudidaya, f.luas_lahan_ha, f.total_pembesaran,
               f.share_rumput_laut, f.share_udang, f.share_bandeng,
               f.share_lele, f.share_nila, f.share_gurami, f.share_patin
        FROM features_model f
        JOIN dim_kabupaten k ON f.kabupaten_id = k.kabupaten_id
    """
    params = {}
    if tahun:
        q += " WHERE f.tahun = :tahun"
        params['tahun'] = int(tahun)
    with engine.connect() as conn:
        return pd.read_sql(text(q), conn, params=params)