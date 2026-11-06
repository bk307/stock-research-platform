"""Conservative research data-quality and transparent opportunity ordering."""
from __future__ import annotations
import math
import pandas as pd

CATEGORIES = ('trend', 'momentum', 'money_flow', 'structure', 'relative_strength')


def category_changes(baseline: dict, current: dict) -> list[str]:
    out = []
    for name in CATEGORIES:
        before = baseline['statuses'].get(name, 'unavailable')
        after = current['statuses'].get(name, 'unavailable')
        if before != after:
            out.append(f"{name.replace('_', ' ').title()}: {before} → {after}")
    return out


def intraday_assessment(quality: dict, benchmark_quality: dict | None, max_age_minutes=45) -> dict:
    """Do not use incomplete/unverified 30-minute bars for actionable ranking.

    A last-bar start time alone does not prove bar completeness. Therefore all
    intraday signals are provisional and confidence is capped at Caution.
    """
    flags = []
    if quality['status'] == 'unavailable':
        flags.append('No current-session intraday data')
        return {'label': 'Unavailable', 'flags': flags, 'usable': False}
    age = quality.get('age_minutes')
    if quality['status'] == 'stale' or age is None or age > max_age_minutes:
        flags.append(f'Intraday observation too old for preview (bar start age {age} min; limit {max_age_minutes} min)')
        return {'label': 'Stale', 'flags': flags, 'usable': False}
    if benchmark_quality is None or benchmark_quality['status'] != 'provisional':
        flags.append('Benchmark intraday evidence unavailable or stale')
        return {'label': 'Incomplete', 'flags': flags, 'usable': False}
    b_age = benchmark_quality.get('age_minutes')
    if b_age is None or b_age > max_age_minutes:
        flags.append(f'Benchmark intraday observation too old ({b_age} min)')
        return {'label': 'Stale', 'flags': flags, 'usable': False}
    flags.append('Intraday bar completion unverified; time-of-day volume not normalized')
    return {'label': 'Provisional', 'flags': flags, 'usable': True}


def eod_assessment(issues: list[str], result: dict) -> dict:
    flags = list(issues)
    if result['available'] < 5:
        flags.append('One or more evidence categories unavailable')
    return {'label': 'Review' if flags else 'Baseline', 'flags': flags, 'usable': True}


def priority_label(result: dict, quality: dict, eod_delta: int | None) -> str:
    """Ordering aid, NOT a recommendation or forward-return prediction."""
    if not quality['usable'] or quality['label'] in ('Stale', 'Unavailable', 'Incomplete'):
        return 'Data review'
    if result['readiness'] == 'Extended':
        return 'Extended / avoid chasing'
    if result['available'] < 5:
        return 'Evidence review'
    if result['contradictions'] >= 3:
        return 'Conflicting evidence'
    if result['readiness'] in ('Confirmed', 'Developing') and result['contradictions'] <= 1:
        return 'Research priority'
    if result['readiness'] == 'Emerging' and (eod_delta is not None and eod_delta > 0):
        return 'Improving watch'
    if result['readiness'] == 'Emerging':
        return 'Early watch'
    return 'No setup'


PRIORITY_ORDER = {'Research priority': 0, 'Improving watch': 1, 'Early watch': 2,
                  'Extended / avoid chasing': 3, 'Conflicting evidence': 4,
                  'Evidence review': 5, 'Data review': 6, 'No setup': 7}


def historical_key(row: dict) -> tuple:
    return (str(row.get('Screen timestamp UTC', '')), str(row.get('Strategy', '')),
            str(row.get('Research mode', '')), str(row.get('Ticker', '')))
