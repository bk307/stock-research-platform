"""Experimental daily OHLCV confluence engine. Not a validated trading signal."""
from __future__ import annotations
import numpy as np
import pandas as pd

MIN_BARS = 220
CATEGORIES = ('trend', 'momentum', 'money_flow', 'structure', 'relative_strength')


def indicators(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.copy().sort_index()
    required = ['Close', 'High', 'Low', 'Volume']
    if not set(required).issubset(d.columns):
        raise ValueError(f'Missing OHLCV columns: {set(required)-set(d.columns)}')
    for col in required:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    if (len(d) < MIN_BARS or d[required].isna().any().any() or
            (d['Close'] <= 0).any() or (d['Volume'] < 0).any() or
            (d['High'] < d['Low']).any()):
        raise ValueError('Need at least 220 valid daily OHLCV sessions')
    c, v = d['Close'], d['Volume']
    for n in (20, 50, 200):
        d[f'sma{n}'] = c.rolling(n).mean()
    delta = c.diff()
    # Wilder RSI with simple-average seed; data providers may use different seeds.
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    avg_up = pd.Series(np.nan, index=d.index, dtype=float)
    avg_down = avg_up.copy()
    avg_up.iloc[14] = up.iloc[1:15].mean()
    avg_down.iloc[14] = down.iloc[1:15].mean()
    for i in range(15, len(d)):
        avg_up.iloc[i] = (avg_up.iloc[i-1] * 13 + up.iloc[i]) / 14
        avg_down.iloc[i] = (avg_down.iloc[i-1] * 13 + down.iloc[i]) / 14
    rs = avg_up / avg_down.replace(0, np.nan)
    d['rsi14'] = 100 - 100 / (1 + rs)
    d.loc[(avg_down == 0) & (avg_up > 0), 'rsi14'] = 100
    d.loc[(avg_down == 0) & (avg_up == 0), 'rsi14'] = 50
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    d['macd_hist'] = macd - macd.ewm(span=9, adjust=False).mean()
    d['obv'] = (np.sign(delta.fillna(0)) * v).cumsum()
    typical = (d['High'] + d['Low'] + c) / 3
    flow = typical * v
    positive = flow.where(typical.diff() > 0, 0).rolling(14).sum()
    negative = flow.where(typical.diff() < 0, 0).rolling(14).sum()
    ratio = positive / negative.replace(0, np.nan)
    d['mfi14'] = 100 - 100 / (1 + ratio)
    d.loc[(negative == 0) & (positive > 0), 'mfi14'] = 100
    d.loc[(negative == 0) & (positive == 0), 'mfi14'] = 50
    prev = c.shift(1)
    tr = pd.concat([d['High'] - d['Low'], (d['High'] - prev).abs(), (d['Low'] - prev).abs()], axis=1).max(axis=1)
    d['atr14'] = tr.rolling(14).mean()
    return d


def _status(bull_condition: bool, bear_condition: bool, direction: str) -> str:
    if bull_condition and bear_condition:
        return 'inconclusive'
    if direction == 'bull':
        return 'supportive' if bull_condition else 'contradictory' if bear_condition else 'inconclusive'
    return 'supportive' if bear_condition else 'contradictory' if bull_condition else 'inconclusive'


def score(frame: pd.DataFrame, benchmark: pd.DataFrame | None = None, direction: str = 'bull') -> dict:
    if direction not in ('bull', 'bear'):
        raise ValueError('direction must be bull or bear')
    d = indicators(frame)
    x, old = d.iloc[-1], d.iloc[-11]
    statuses = {}
    notes = {}
    statuses['trend'] = _status(x.Close > x.sma50 > x.sma200, x.Close < x.sma50 < x.sma200, direction)
    notes['trend'] = f'Close {x.Close:.2f}; SMA50 {x.sma50:.2f}; SMA200 {x.sma200:.2f}. Full moving-average alignment required.'
    statuses['momentum'] = _status(x.rsi14 > 50 and x.macd_hist > 0, x.rsi14 < 50 and x.macd_hist < 0, direction)
    notes['momentum'] = f'RSI(14) {x.rsi14:.1f}; MACD histogram {x.macd_hist:.3f}. Both must agree.'
    statuses['money_flow'] = _status(x.obv > old.obv and x.mfi14 > 50, x.obv < old.obv and x.mfi14 < 50, direction)
    notes['money_flow'] = f'OBV 10-session change {x.obv-old.obv:,.0f}; MFI(14) {x.mfi14:.1f}. These are price/volume proxies, not direct institutional flows.'
    prior_high = d['High'].iloc[-21:-1].max()
    prior_low = d['Low'].iloc[-21:-1].min()
    statuses['structure'] = _status(x.Close > prior_high, x.Close < prior_low, direction)
    notes['structure'] = f'Close {x.Close:.2f}; prior 20-session high {prior_high:.2f}; low {prior_low:.2f}. Breakout/breakdown confirmation only.'
    statuses['relative_strength'] = 'unavailable'
    notes['relative_strength'] = 'Benchmark data missing or insufficient overlapping history.'
    if benchmark is not None and 'Close' in benchmark:
        b = pd.to_numeric(benchmark['Close'], errors='coerce')
        joined = pd.concat([d['Close'].rename('stock'), b.rename('benchmark')], axis=1).dropna()
        # Require benchmark data current to the latest stock session.
        if len(joined) >= 64 and joined.index[-1] == d.index[-1]:
            stock_return = joined['stock'].iloc[-1] / joined['stock'].iloc[-64] - 1
            benchmark_return = joined['benchmark'].iloc[-1] / joined['benchmark'].iloc[-64] - 1
            diff = stock_return - benchmark_return
            # Tiny differences are inconclusive, not evidence of directional strength.
            statuses['relative_strength'] = 'supportive' if (diff > 0.001 if direction == 'bull' else diff < -0.001) else ('contradictory' if (diff < -0.001 if direction == 'bull' else diff > 0.001) else 'inconclusive')
            notes['relative_strength'] = f'63-session stock return {stock_return:+.1%}; benchmark {benchmark_return:+.1%}; difference {diff:+.1%}.'
    supported = sum(v == 'supportive' for v in statuses.values())
    available = sum(v != 'unavailable' for v in statuses.values())
    contradictions = sum(v == 'contradictory' for v in statuses.values())
    # Signed distance from SMA20, expressed in ATRs, must match trade direction.
    distance_atr = float((x.Close - x.sma20) / x.atr14) if x.atr14 > 0 else float('nan')
    extended = bool(np.isfinite(distance_atr) and (distance_atr > 2.5 if direction == 'bull' else distance_atr < -2.5))
    if available < 5:
        readiness = 'Incomplete evidence'
    elif extended:
        readiness = 'Extended'
    elif supported >= 4 and contradictions <= 1:
        readiness = 'Confirmed'
    elif supported >= 3 and contradictions <= 2:
        readiness = 'Developing'
    elif supported >= 2:
        readiness = 'Emerging'
    else:
        readiness = 'No setup'
    warnings = []
    if extended:
        warnings.append(f'Direction-specific extension: {distance_atr:+.2f} ATR from SMA20 (threshold 2.5 ATR).')
    if available < 5:
        warnings.append('Incomplete benchmark/evidence: do not treat score as a complete screen.')
    if contradictions:
        warnings.append(f'{contradictions} category/categories contradict the selected direction.')
    warnings.append('Earnings/events, options liquidity, spreads, and execution risks are NOT checked.')
    return {
        'close': round(float(x.Close), 2), 'score': round(100 * supported / 5),
        'aligned': supported, 'total': 5, 'available': available,
        'contradictions': contradictions, 'readiness': readiness,
        'statuses': statuses, 'notes': notes, 'extended': extended,
        'distance_atr': round(distance_atr, 2) if np.isfinite(distance_atr) else None,
        'rsi': round(float(x.rsi14), 1), 'mfi': round(float(x.mfi14), 1),
        'data_date': str(pd.Timestamp(d.index[-1]).date()),
        'warnings': warnings,
    }
