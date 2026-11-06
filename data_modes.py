"""Conservative EOD selection and clearly labeled intraday preview construction."""
from __future__ import annotations
from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd

NY = ZoneInfo('America/New_York')
OHLCV = ['Open', 'High', 'Low', 'Close', 'Volume']


def ny_now(now=None):
    if now is None:
        return datetime.now(NY)
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    return now.astimezone(NY)


def normalize_daily(frame):
    """Convert daily date labels to New York session dates, retaining OHLCV."""
    if frame is None or frame.empty:
        raise ValueError('No daily OHLCV returned')
    d = frame.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    if not set(OHLCV).issubset(d.columns):
        raise ValueError('Missing daily OHLCV fields')
    idx = pd.DatetimeIndex(d.index)
    if idx.tz is not None:
        idx = idx.tz_convert(NY).tz_localize(None)
    d.index = idx.normalize()
    d = d[OHLCV].sort_index()
    return d[~d.index.duplicated(keep='last')]


def confirmed_daily(frame, now=None):
    """Fail closed: today's daily bar is never used in confirmed EOD scoring.

    This deliberately sacrifices same-evening freshness; the provider's daily
    bar can be revised or incomplete after the exchange close.
    """
    today = pd.Timestamp(ny_now(now).date())
    d = normalize_daily(frame)
    closed = d.loc[d.index < today].copy()
    if closed.empty:
        raise ValueError('No prior-session daily candles available')
    return closed


def aggregate_today_intraday(frame, now=None):
    """Aggregate only today's available regular-session bars, excluding future bars.

    Timestamped intraday bars must be timezone-aware. Intraday bars are treated
    as provisional, including at/after market close; data may be delayed.
    """
    current = ny_now(now)
    if frame is None or frame.empty:
        return None
    d = frame.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    if not set(OHLCV).issubset(d.columns):
        return None
    idx = pd.DatetimeIndex(d.index)
    if idx.tz is None:
        return None  # Never guess a timestamp timezone.
    d.index = idx.tz_convert(NY)
    d = d.sort_index()
    # yfinance 30m bar timestamps mark interval start. Keep only regular hours.
    d = d[(d.index.date == current.date()) & (d.index.time >= time(9,30)) &
          (d.index.time < time(16,0)) & (d.index <= pd.Timestamp(current))]
    d = d.dropna(subset=OHLCV)
    if d.empty:
        return None
    if (d['High'] < d['Low']).any() or (d['Volume'] < 0).any():
        return None
    return {'Open': float(d['Open'].iloc[0]), 'High': float(d['High'].max()),
            'Low': float(d['Low'].min()), 'Close': float(d['Close'].iloc[-1]),
            'Volume': float(d['Volume'].sum()),
            'last_bar_at': str(d.index[-1]), 'bars': len(d)}


def preview_frame(confirmed, aggregate, now=None):
    """Append exactly one provisional NY-session candle to confirmed daily data."""
    if aggregate is None:
        return None
    d = confirmed_daily(confirmed, now)
    today = pd.Timestamp(ny_now(now).date())
    row = pd.DataFrame([{key: aggregate[key] for key in OHLCV}], index=[today])
    return pd.concat([d, row])
