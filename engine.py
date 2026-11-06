"""Transparent, experimental EOD technical screening. Not trading advice."""
from __future__ import annotations
import math
import pandas as pd
import numpy as np

MIN_BARS = 220

def indicators(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.copy().sort_index()
    required = {'Close', 'High', 'Low', 'Volume'}
    if not required.issubset(d.columns):
        raise ValueError(f'Missing OHLCV columns: {required-set(d.columns)}')
    for c in required:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    if len(d) < MIN_BARS or d[list(required)].isna().any().any() or (d['Close'] <= 0).any():
        raise ValueError('Insufficient or invalid daily history (need 220 clean sessions)')
    close, vol = d['Close'], d['Volume']
    d['sma20'] = close.rolling(20).mean()
    d['sma50'] = close.rolling(50).mean()
    d['sma200'] = close.rolling(200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    d['rsi14'] = 100 - 100/(1+rs)
    d.loc[(loss == 0) & (gain > 0), 'rsi14'] = 100
    d.loc[(loss == 0) & (gain == 0), 'rsi14'] = 50
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12-ema26
    d['macd_hist'] = macd - macd.ewm(span=9, adjust=False).mean()
    d['obv'] = (np.sign(delta.fillna(0)) * vol).cumsum()
    typical = (d['High'] + d['Low'] + close)/3
    money = typical * vol
    positive = money.where(typical.diff()>0, 0).rolling(14).sum()
    negative = money.where(typical.diff()<0, 0).rolling(14).sum()
    ratio = positive / negative.replace(0, np.nan)
    d['mfi14'] = 100 - 100/(1+ratio)
    d.loc[(negative == 0) & (positive > 0), 'mfi14'] = 100
    d.loc[(negative == 0) & (positive == 0), 'mfi14'] = 50
    d['relvol20'] = vol / vol.rolling(20).mean().replace(0, np.nan)
    prev = close.shift(1)
    tr = pd.concat([(d['High']-d['Low']), (d['High']-prev).abs(), (d['Low']-prev).abs()], axis=1).max(axis=1)
    d['atr14'] = tr.rolling(14).mean()
    return d

def score(frame: pd.DataFrame, benchmark: pd.DataFrame | None = None, direction: str = 'bull') -> dict:
    """Experimental independent-category confluence; not a validated predictive score."""
    if direction not in ('bull','bear'):
        raise ValueError('direction must be bull or bear')
    d = indicators(frame)
    x, old = d.iloc[-1], d.iloc[-11]
    bull = direction == 'bull'
    signals = {}
    signals['trend'] = bool((x.Close > x.sma50 > x.sma200) if bull else (x.Close < x.sma50 < x.sma200))
    signals['momentum'] = bool((x.rsi14 > 50 and x.macd_hist > 0) if bull else (x.rsi14 < 50 and x.macd_hist < 0))
    signals['money_flow'] = bool((x.obv > old.obv and x.mfi14 > 50) if bull else (x.obv < old.obv and x.mfi14 < 50))
    signals['structure'] = bool((x.Close > d['High'].iloc[-21:-1].max()) if bull else (x.Close < d['Low'].iloc[-21:-1].min()))
    relative_status = 'unavailable'
    if benchmark is not None:
        b = benchmark['Close'].dropna()
        joined = pd.concat([d['Close'].rename('stock'), b.rename('benchmark')],axis=1).dropna()
        if len(joined) >= 64:
            stock_return = joined.stock.iloc[-1]/joined.stock.iloc[-64]-1
            market_return = joined.benchmark.iloc[-1]/joined.benchmark.iloc[-64]-1
            relative_status = 'supportive' if ((stock_return > market_return) if bull else (stock_return < market_return)) else 'contradictory'
            signals['relative_strength'] = relative_status == 'supportive'
    confirmed = sum(signals.values())
    total = len(signals)
    extended = bool(abs(x.Close/x.sma20-1) > 2.5*x.atr14/x.Close) if pd.notna(x.atr14) else False
    readiness = 'Extended' if extended else ('Confirmed' if confirmed >= 4 and total == 5 else 'Developing' if confirmed >= 3 else 'Emerging' if confirmed >= 2 else 'No setup')
    # Displayed score is only a heuristic proportion of supported categories.
    return {'close': round(float(x.Close),2), 'score': round(100*confirmed/total), 'aligned': confirmed, 'total':total,
            'readiness':readiness, 'signals':signals, 'relative_status':relative_status,
            'rsi':round(float(x.rsi14),1), 'mfi':round(float(x.mfi14),1),
            'warnings':(['Extended relative to SMA20/ATR'] if extended else []) + (['Benchmark comparison unavailable'] if relative_status=='unavailable' else [])}
