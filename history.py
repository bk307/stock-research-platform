"""Portable CSV history: session-local until user downloads and restores file."""
from __future__ import annotations
import io
import pandas as pd

REQUIRED = {'Screen timestamp UTC', 'Strategy', 'Research mode', 'Ticker', 'Score'}
MAX_IMPORT_BYTES = 5_000_000
MAX_ROWS = 250_000


def import_history(data: bytes) -> pd.DataFrame:
    if len(data) > MAX_IMPORT_BYTES:
        raise ValueError('History file exceeds 5 MB import limit')
    df = pd.read_csv(io.BytesIO(data))
    if not REQUIRED.issubset(df.columns):
        raise ValueError(f'Missing history columns: {sorted(REQUIRED - set(df.columns))}')
    if len(df) > MAX_ROWS:
        raise ValueError('Too many history rows')
    df['Screen timestamp UTC'] = pd.to_datetime(df['Screen timestamp UTC'], utc=True, errors='coerce')
    if df['Screen timestamp UTC'].isna().any():
        raise ValueError('Invalid UTC timestamp in history')
    df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
    if df['Score'].isna().any():
        raise ValueError('Invalid score in history')
    df['Ticker'] = df['Ticker'].astype(str).str.upper().str.strip()
    return df


def merge_history(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    frames = [x for x in (existing, new) if x is not None and not x.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined['Screen timestamp UTC'] = pd.to_datetime(combined['Screen timestamp UTC'], utc=True, errors='coerce')
    keys = ['Screen timestamp UTC', 'Strategy', 'Research mode', 'Ticker']
    return (combined.drop_duplicates(subset=keys, keep='last')
            .sort_values(keys).reset_index(drop=True))
