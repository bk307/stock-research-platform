"""Descriptive, non-predictive cross-session research history analysis."""
import pandas as pd

KEYS = ['Ticker', 'Strategy', 'Benchmark', 'Research mode']


def prepare_history(df, strategy=None, benchmark=None, mode='Confirmed EOD'):
    """Use distinct observed data dates; never mix intraday with confirmed EOD."""
    if df is None or df.empty:
        return pd.DataFrame()
    required = {'Ticker', 'Strategy', 'Research mode', 'Screen timestamp UTC', 'Data date', 'Score'}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    h = df.copy()
    h['Screen timestamp UTC'] = pd.to_datetime(h['Screen timestamp UTC'], utc=True, errors='coerce')
    h['Data date'] = pd.to_datetime(h['Data date'], errors='coerce').dt.date
    h['Score'] = pd.to_numeric(h['Score'], errors='coerce')
    h = h.dropna(subset=['Screen timestamp UTC', 'Data date', 'Score', 'Ticker'])
    h = h[h['Research mode'].eq(mode)]
    if strategy:
        h = h[h['Strategy'].eq(strategy)]
    if benchmark and 'Benchmark' in h:
        h = h[h['Benchmark'].eq(benchmark)]
    h = h.sort_values('Screen timestamp UTC')
    grouping = ['Ticker', 'Strategy', 'Research mode', 'Data date']
    if 'Benchmark' in h:
        grouping.append('Benchmark')
    return h.drop_duplicates(grouping, keep='last').sort_values(['Ticker', 'Data date'])


def summarize_history(h):
    """No extrapolation from a single observation; compare distinct EOD dates only."""
    if h.empty:
        return pd.DataFrame()
    result = []
    grouping = ['Ticker', 'Strategy'] + (['Benchmark'] if 'Benchmark' in h else [])
    for key, g in h.groupby(grouping, dropna=False):
        g = g.sort_values('Data date')
        latest = g.iloc[-1]
        previous = g.iloc[-2] if len(g) >= 2 else None
        change = float(latest['Score'] - previous['Score']) if previous is not None else None
        if change is None:
            trend = 'Insufficient history'
        elif change > 0:
            trend = 'Improving'
        elif change < 0:
            trend = 'Deteriorating'
        else:
            trend = 'Unchanged'
        row = {'Ticker': latest['Ticker'], 'Strategy': latest['Strategy'],
               'Latest data date': str(latest['Data date']), 'EOD observations': len(g),
               'Latest score': int(latest['Score']), 'Previous score': int(previous['Score']) if previous is not None else None,
               'Change vs prior EOD': int(change) if change is not None else None,
               'Direction': trend, 'Readiness': latest.get('Readiness', 'Unknown'),
               'Confluence': latest.get('Confluence', ''), 'Contradictions': latest.get('Contradictions', None)}
        if 'Benchmark' in h: row['Benchmark'] = latest.get('Benchmark', '')
        result.append(row)
    return pd.DataFrame(result)
