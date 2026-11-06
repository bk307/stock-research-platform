"""Stock Research MVP V0.4 — discovery, trend-in-evidence, and data quality."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from engine import score, MIN_BARS
from data_modes import confirmed_daily, aggregate_today_intraday, preview_frame, preview_quality, ny_now
from universe import STARTER

st.set_page_config(page_title='Stock Research MVP V0.4', layout='wide')
st.title('Stock Research MVP — Opportunity Discovery')
st.caption('V0.4 · Experimental technical research · Not a recommendation or trading signal')
st.warning('No automated earnings/event checks, fundamentals, options pricing, liquidity qualification, or execution-risk assessment. Scores are unvalidated.')

@st.cache_data(ttl=1800, show_spinner=False)
def download(ticker: str, period='2y', interval='1d'):
    import yfinance as yf
    d = yf.download(ticker, period=period, interval=interval,
                    auto_adjust=True, progress=False, threads=False, prepost=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    if d.empty:
        raise ValueError('No data returned')
    return d


def evidence_trajectory(eod, benchmark, direction):
    """Compare today's confirmed assessment with that from five sessions ago.

    Both security and benchmark are cut at the historical date to avoid peeking.
    This is a retrospective score comparison, not a backtest or return forecast.
    """
    if len(eod) < MIN_BARS + 5:
        return None
    old = eod.iloc[:-5]
    old_benchmark = None
    if benchmark is not None:
        old_benchmark = benchmark.loc[benchmark.index <= old.index[-1]]
    try:
        return score(old, old_benchmark, direction)
    except (ValueError, KeyError, IndexError):
        return None


def quality_checks(eod, now):
    """Detect missing/old daily observations and poor price/volume coverage."""
    issues = []
    last = pd.Timestamp(eod.index[-1]).date()
    days = (now.date() - last).days
    if days > 4:
        issues.append(f'Latest confirmed daily observation is {days} calendar days old.')
    if len(eod) < MIN_BARS:
        issues.append(f'Only {len(eod)} daily sessions (minimum {MIN_BARS}).')
    recent = eod.tail(20)
    if recent['Volume'].le(0).any():
        issues.append('At least one of the last 20 sessions has zero volume.')
    if recent[['Open','High','Low','Close','Volume']].isna().any().any():
        issues.append('Missing values in the last 20 daily sessions.')
    return issues


if 'screen_v04' not in st.session_state:
    st.session_state.screen_v04 = None

with st.sidebar:
    st.header('Screen configuration')
    with st.form('screen_form'):
        universe_mode = st.radio('Ticker source', ['Custom tickers', 'Starter universe (50)'])
        tickers = st.text_area('Custom tickers (comma-separated)', 'AAPL,MSFT,NVDA,AMZN,META,GOOGL,AMD,AVGO,TSLA,PLTR')
        limit = st.slider('Maximum securities to screen', 3, 50, 15, step=1)
        benchmark_symbol = st.text_input('Benchmark', 'SPY').strip().upper()
        direction_label = st.radio('Strategy', ['Bullish Swing', 'Bearish Swing'])
        research_mode = st.radio('Research mode', ['Confirmed EOD', 'Intraday Preview'])
        run = st.form_submit_button('Run research screen', type='primary')
    st.caption('Starter universe is illustrative, not a full market scan or liquidity-screened list. Yahoo data may be delayed, revised, or rate-limited.')
    if st.session_state.screen_v04:
        st.caption('Results remain available while you change the candidate dropdown. Run again to refresh.')

if run:
    if universe_mode.startswith('Starter'):
        symbols = STARTER[:limit]
    else:
        symbols = list(dict.fromkeys(s.strip().upper() for s in tickers.split(',') if s.strip()))[:limit]
    if not symbols or not benchmark_symbol:
        st.error('Enter at least one ticker and a benchmark.')
    else:
        direction = 'bull' if direction_label == 'Bullish Swing' else 'bear'
        now = ny_now()
        rows, details, errors = [], {}, []
        try:
            b_eod = confirmed_daily(download(benchmark_symbol), now)
        except Exception as exc:
            b_eod = None
            errors.append(f'Benchmark {benchmark_symbol}: {exc}')
        b_preview = None
        if research_mode == 'Intraday Preview' and b_eod is not None:
            try:
                b_agg = aggregate_today_intraday(download(benchmark_symbol, period='5d', interval='30m'), now)
                b_preview = preview_frame(b_eod, b_agg, now)
                b_quality = preview_quality(b_agg, now)
                if b_quality['status'] != 'provisional':
                    errors.append(f'Benchmark {benchmark_symbol}: {b_quality["message"]} Relative strength may be unavailable or stale.')
                    b_preview = None
            except Exception as exc:
                errors.append(f'Benchmark {benchmark_symbol} intraday: {exc}')
        with st.spinner('Downloading market data and screening...'):
            progress = st.progress(0)
            for i, symbol in enumerate(symbols):
                try:
                    eod = confirmed_daily(download(symbol), now)
                    issues = quality_checks(eod, now)
                    baseline = score(eod, b_eod, direction)
                    prior = evidence_trajectory(eod, b_eod, direction)
                    result = baseline
                    preview_status = 'Not requested'
                    last_intraday = None
                    if research_mode == 'Intraday Preview':
                        try:
                            agg = aggregate_today_intraday(download(symbol, period='5d', interval='30m'), now)
                            q = preview_quality(agg, now)
                            preview_status = q['message']
                            if q['status'] == 'provisional' and b_preview is not None:
                                pframe = preview_frame(eod, agg, now)
                                if pframe is not None:
                                    result = score(pframe, b_preview, direction)
                                    last_intraday = agg['last_bar_at']
                            elif q['status'] == 'stale':
                                issues.append('Intraday data stale: confirmed EOD result shown instead.')
                            else:
                                issues.append('Intraday preview unavailable: confirmed EOD result shown instead.')
                        except Exception as exc:
                            preview_status = 'Intraday unavailable; confirmed EOD shown.'
                            errors.append(f'{symbol} intraday: {exc}')
                    if b_eod is None:
                        issues.append('Benchmark unavailable; relative strength cannot be evaluated.')
                    # Quality warning does not silently alter scores; disclose explicitly.
                    delta = baseline['score'] - prior['score'] if prior else None
                    trajectory = ('Improving' if delta is not None and delta > 0 else
                                  'Deteriorating' if delta is not None and delta < 0 else
                                  'Unchanged' if delta == 0 else 'Unavailable')
                    details[symbol] = dict(result=result, baseline=baseline, prior=prior,
                                           quality=issues, preview_status=preview_status,
                                           last_intraday=last_intraday)
                    rows.append({'Ticker': symbol, 'Price': result['close'],
                                 'Score': result['score'], 'Confluence': f"{result['aligned']}/5",
                                 'Contradictions': result['contradictions'],
                                 'Readiness': result['readiness'],
                                 '5-Session EOD Δ': delta,
                                 'EOD trajectory': trajectory,
                                 'Data date': result['data_date'],
                                 'RSI': result['rsi'], 'MFI': result['mfi'],
                                 'Data status': preview_status if research_mode == 'Intraday Preview' else 'Prior completed session',
                                 'Quality flags': len(issues), 'EOD score': baseline['score']})
                except Exception as exc:
                    errors.append(f'{symbol}: {exc}')
                progress.progress((i+1)/len(symbols))
            progress.empty()
        st.session_state.screen_v04 = {
            'rows': rows, 'details': details, 'errors': errors,
            'direction': direction_label, 'benchmark': benchmark_symbol,
            'mode': research_mode, 'universe': universe_mode,
            'run_at': now.strftime('%Y-%m-%d %H:%M %Z'),
            'export_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
        st.session_state.pop('candidate_v04', None)

screen = st.session_state.screen_v04
if screen is None:
    st.info('Choose a universe and research mode, then click **Run research screen**.')
else:
    st.subheader(f"Latest screen — {screen['direction']} — {screen['mode']}")
    st.caption(f"Run: {screen['run_at']} · Benchmark: {screen['benchmark']} · Yahoo Finance via yfinance · adjusted OHLCV")
    if screen['mode'] == 'Intraday Preview':
        st.warning('INTRADAY PREVIEW: data is provisional, delayed and may include an unfinished bar. Stale or unavailable data falls back to confirmed EOD. No real-time claim.')
    else:
        st.info('CONFIRMED EOD: excludes the current New York calendar day even after the close; same-evening updates may be delayed.')
    if screen['rows']:
        table = pd.DataFrame(screen['rows'])
        # Candidate ranking uses confirmed/provisional score and recent EOD trajectory;
        # no assertion of forecasting power or optimized weights.
        table['_change'] = pd.to_numeric(table['5-Session EOD Δ'], errors='coerce').fillna(-999)
        table = table.sort_values(['Score', '_change', 'Ticker'], ascending=[False, False, True]).drop(columns=['_change'])
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption('5-session Δ compares confirmed EOD scores, not prices or future returns. Scores and thresholds are experimental.')
        export = table.copy()
        export.insert(0, 'Screen timestamp UTC', screen['export_at_utc'])
        export.insert(1, 'Research mode', screen['mode'])
        export.insert(2, 'Strategy', screen['direction'])
        export.insert(3, 'Benchmark', screen['benchmark'])
        st.download_button('Download screening snapshot (CSV)',
                           export.to_csv(index=False).encode('utf-8'),
                           file_name=f"stock_research_{screen['export_at_utc'][:10]}_{screen['mode'].replace(' ','_')}.csv",
                           mime='text/csv')
        chosen = st.selectbox('Inspect candidate', table['Ticker'].tolist(), key='candidate_v04')
        item = screen['details'][chosen]
        result, baseline, prior = item['result'], item['baseline'], item['prior']
        st.subheader(f"{chosen} — {result['readiness']}")
        st.caption(f"Data {result['data_date']} · Score {result['score']}/100 · Support {result['aligned']}/5 · Contradictions {result['contradictions']}")
        if prior:
            st.write(f"**Five-session confirmed EOD change:** {baseline['score']-prior['score']:+d} points ({prior['score']} → {baseline['score']}).")
        else:
            st.write('**Five-session confirmed EOD change:** unavailable.')
        if screen['mode'] == 'Intraday Preview':
            st.write(f"**Intraday data:** {item['preview_status']}")
            st.write(f"**Confirmed EOD baseline:** {baseline['score']}/100, {baseline['readiness']} ({baseline['data_date']})")
            if item['last_intraday']:
                st.write(f"**Provisional change:** {result['score']-baseline['score']:+d} points; {baseline['readiness']} → {result['readiness']}")
        for name, status in result['statuses'].items():
            symbol = {'supportive': '✅', 'contradictory': '❌', 'inconclusive': '➖', 'unavailable': '❔'}[status]
            with st.expander(f"{symbol} {name.replace('_',' ').title()} — {status.title()}"):
                st.write(result['notes'][name])
        st.markdown('**Data quality / risk limitations**')
        for warning in item['quality'] + result['warnings']:
            st.write('• ' + warning)
        st.info('These are research heuristics, not trading instructions. Check charts, earnings, events, spreads, liquidity, and position risk independently.')
    else:
        st.error('No securities could be screened. Review the errors below.')
    if screen['errors']:
        with st.expander(f"{len(screen['errors'])} data warnings / exclusions"):
            for error in screen['errors']:
                st.write('• ' + error)
