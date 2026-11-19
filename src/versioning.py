import json, hashlib
from datetime import datetime
from pathlib import Path
from src.config import MODEL_DIR

def hash_df(df) -> str:
    return hashlib.md5(df.to_csv(index=False).encode()).hexdigest()[:10]

def save_run(meta: dict, prefix: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = MODEL_DIR / f"{prefix}_{ts}.json"
    path.write_text(json.dumps(meta, indent=2, default=str))
    return path

def list_runs(prefix: str):
    return sorted(MODEL_DIR.glob(f"{prefix}_*.json"))

def detect_changes(old_df, new_df, key_cols=['kabupaten', 'tahun']):
    old_keys = set(map(tuple, old_df[key_cols].values))
    new_keys = set(map(tuple, new_df[key_cols].values))
    added = new_keys - old_keys
    updated = new_keys & old_keys
    removed = old_keys - new_keys
    return {'added': added, 'updated': updated, 'removed': removed,
            'n_added': len(added), 'n_updated': len(updated), 'n_removed': len(removed)}

def upsert_data(existing_path: Path, new_df: pd.DataFrame, key_cols=['kabupaten', 'tahun']):
    if existing_path.exists():
        old_df = pd.read_parquet(existing_path)
        mask = ~old_df.set_index(key_cols).index.isin(new_df.set_index(key_cols).index)
        combined = pd.concat([old_df[mask], new_df], ignore_index=True)
    else:
        combined = new_df.copy()
    combined.to_parquet(existing_path, index=False)
    return combined

import pandas as pd

def upsert_fact(existing_path: Path, new_df: pd.DataFrame,
                key_cols=['kabupaten', 'tahun', 'metrik', 'jenis_budidaya']):

    if existing_path.exists():
        old_df = pd.read_parquet(existing_path)
        n_before = len(old_df)
        
        new_keys = new_df[key_cols].drop_duplicates()
        merged = old_df.merge(new_keys, on=key_cols, how='left', indicator=True)
        old_filtered = merged[merged['_merge'] == 'left_only'].drop(columns='_merge')
        
        combined = pd.concat([old_filtered, new_df], ignore_index=True)
        n_after = len(combined)
        
        print(f'UPSERT: {n_before} → {n_after} baris '
              f'(update {n_before - len(old_filtered)}, insert {len(new_df) - (n_before - len(old_filtered))})')
    else:
        combined = new_df.copy()
        print(f'INSERT: {len(combined)} baris (file baru)')
    
    combined.to_parquet(existing_path, index=False)
    return combined


def upsert_features(existing_path: Path, new_df: pd.DataFrame,
                    key_cols=['kabupaten', 'tahun']):
    return upsert_fact(existing_path, new_df, key_cols=key_cols)


def save_snapshot(df: pd.DataFrame, version: int, prefix: str = 'fact'):
    version_dir = existing_path.parent / 'versions' if existing_path else MODEL_DIR
    version_dir.mkdir(parents=True, exist_ok=True)
    path = version_dir / f'{prefix}_v{version}.parquet'
    df.to_parquet(path, index=False)
    return path