"""Optional Supabase REST persistence; server-side credentials only.

Never put service_role keys into GitHub or browser-facing UI.
"""
from __future__ import annotations
import hashlib
import json
import requests
import pandas as pd

FIELDS = ['Screen timestamp UTC','Research mode','Strategy','Benchmark','Ticker']

def cloud_configured(secrets):
    return bool(secrets.get('SUPABASE_URL') and secrets.get('SUPABASE_SERVICE_ROLE_KEY'))

def cloud_error(exc):
    # Avoid exposing request headers, tokens, or other secret-bearing exception text.
    return type(exc).__name__

class CloudHistory:
    def __init__(self, url, key):
        self.url = str(url).rstrip('/') + '/rest/v1/research_snapshots'
        self.headers = {'apikey': str(key), 'Authorization': 'Bearer ' + str(key),
                        'Content-Type':'application/json', 'Prefer':'resolution=merge-duplicates,return=minimal'}

    @classmethod
    def from_secrets(cls, secrets):
        return cls(secrets['SUPABASE_URL'], secrets['SUPABASE_SERVICE_ROLE_KEY'])

    @staticmethod
    def _records(df):
        for row in df.to_dict(orient='records'):
            normalized = {}
            for k,v in row.items():
                if pd.isna(v):
                    normalized[k] = None
                elif isinstance(v, pd.Timestamp):
                    normalized[k] = v.isoformat()
                elif hasattr(v,'item'):
                    normalized[k] = v.item()
                else:
                    normalized[k] = v
            # Stable identity: same run+strategy+mode+ticker = same record.
            ident = '|'.join(str(normalized.get(k,'')) for k in FIELDS)
            yield {'record_id': hashlib.sha256(ident.encode()).hexdigest(),
                   'run_at': str(normalized['Screen timestamp UTC']),
                   'ticker': str(normalized['Ticker']),
                   'payload': normalized}

    def upsert(self, df):
        records = list(self._records(df))
        for i in range(0,len(records),100):
            response = requests.post(self.url, params={'on_conflict':'record_id'},
                                     headers=self.headers, json=records[i:i+100], timeout=20)
            response.raise_for_status()

    def load(self):
        rows=[]
        offset=0
        while True:
            response = requests.get(self.url, headers=self.headers,
                                    params={'select':'payload','order':'run_at.asc',
                                            'limit':1000,'offset':offset}, timeout=20)
            response.raise_for_status()
            page=response.json()
            rows.extend(x['payload'] for x in page)
            if len(page)<1000: break
            offset += len(page)
            if offset>=100000: raise ValueError('History exceeds safe load limit')
        return pd.DataFrame(rows)
