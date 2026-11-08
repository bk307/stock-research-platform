"""Server-side Supabase REST persistence for the V0.7 research_snapshots schema.

Never expose secret keys in GitHub, frontend components, or exception messages.
"""
from __future__ import annotations
import hashlib
import json
import math
import requests
import pandas as pd

IDENTITY = ['Screen timestamp UTC', 'Research mode', 'Strategy', 'Benchmark', 'Ticker']
MAPPING = {
    'Screen timestamp UTC': 'screen_timestamp_utc', 'Research mode': 'research_mode',
    'Strategy': 'strategy', 'Benchmark': 'benchmark', 'Ticker': 'ticker',
    'Data date': 'data_date', 'Score': 'score', 'EOD score': 'eod_score',
    'Supporting Categories': 'supporting_categories', 'Total Categories': 'total_categories',
    'Contradictions': 'contradictions', 'Readiness': 'readiness',
    'Priority': 'priority', 'Data confidence': 'data_confidence',
    'Evidence changes': 'evidence_changes', 'EOD trajectory': 'eod_trajectory',
    '5-Session EOD Δ': 'five_session_eod_delta', 'Price': 'price',
    'RSI': 'rsi', 'MFI': 'mfi', 'Data status': 'data_status',
    'Quality flags': 'quality_flags',
}

def cloud_configured(secrets):
    return bool(secrets.get('SUPABASE_URL') and (secrets.get('SUPABASE_SERVICE_ROLE_KEY') or secrets.get('SUPABASE_KEY')))

def cloud_error(exc):
    # Never surface exception strings: HTTP clients can include request context.
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return f'HTTP {exc.response.status_code} ({type(exc).__name__})'
    return type(exc).__name__

class CloudHistory:
    def __init__(self, url, key):
        self.url = str(url).rstrip('/') + '/rest/v1/research_snapshots'
        self.headers = {'apikey': str(key), 'Authorization': 'Bearer ' + str(key),
                        'Content-Type': 'application/json',
                        'Prefer': 'resolution=merge-duplicates,return=minimal'}

    @classmethod
    def from_secrets(cls, secrets):
        return cls(secrets['SUPABASE_URL'], secrets.get('SUPABASE_SERVICE_ROLE_KEY') or secrets['SUPABASE_KEY'])

    @staticmethod
    def _clean(v):
        if v is None: return None
        try:
            if pd.isna(v): return None
        except (TypeError, ValueError): pass
        if isinstance(v, pd.Timestamp): return v.isoformat()
        if hasattr(v, 'item'): v = v.item()
        if isinstance(v, float) and not math.isfinite(v): return None
        return v

    @classmethod
    def _records(cls, df):
        for raw in df.to_dict(orient='records'):
            row = {k: cls._clean(v) for k, v in raw.items()}
            ident = '|'.join(str(row.get(k, '')) for k in IDENTITY)
            out = {'snapshot_id': hashlib.sha256(ident.encode()).hexdigest()}
            for old, new in MAPPING.items():
                if old in row: out[new] = row[old]
            # Confluence exported by older versions as '2/5'.
            if 'Confluence' in row and row['Confluence'] is not None:
                parts = str(row['Confluence']).split('/')
                if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
                    out['supporting_categories'] = int(parts[0])
                    out['total_categories'] = int(parts[1])
            if out.get('data_date') is not None:
                out['data_date'] = str(out['data_date'])[:10]
            if out.get('screen_timestamp_utc') is not None:
                out['screen_timestamp_utc'] = pd.Timestamp(out['screen_timestamp_utc']).isoformat()
            yield out

    def upsert(self, df):
        records = list(self._records(df))
        for i in range(0, len(records), 100):
            r = requests.post(self.url, params={'on_conflict': 'snapshot_id'},
                              headers=self.headers, json=records[i:i+100], timeout=25)
            r.raise_for_status()
        return len(records)

    def load(self):
        rows = []
        offset = 0
        while True:
            r = requests.get(self.url, headers=self.headers,
                             params={'select': '*', 'order': 'screen_timestamp_utc.asc',
                                     'limit': 1000, 'offset': offset}, timeout=25)
            r.raise_for_status()
            page = r.json()
            for record in page:
                out = {old: record[new] for old, new in MAPPING.items() if new in record}
                if record.get('supporting_categories') is not None and record.get('total_categories') is not None:
                    out['Confluence'] = f"{record['supporting_categories']}/{record['total_categories']}"
                rows.append(out)
            if len(page) < 1000: break
            offset += len(page)
            if offset >= 100000: raise ValueError('History exceeds safe load limit')
        return pd.DataFrame(rows)
