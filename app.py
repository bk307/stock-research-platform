"""Stock Research MVP V0.3 — confirmed daily research and provisional preview."""
import pandas as pd
import streamlit as st
from engine import score
from data_modes import confirmed_daily, aggregate_today_intraday, preview_frame, ny_now

st.set_page_config(page_title='Stock Research MVP V0.3', layout='wide')
st.title('Stock Research MVP — Technical Confluence')
st.caption('V0.3 • Research prototype • Not investment advice or a trading signal')
st.warning('Experimental scores. Earnings/events, options pricing, fundamentals, and execution risks are NOT automatically checked.')

@st.cache_data(ttl=1800, show_spinner=False)
def download(ticker: str, period='2y', interval='1d'):
    import yfinance as yf
    d = yf.download(ticker, period=period, interval=interval,
                    auto_adjust=True, progress=False, threads=False,
                    prepost=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    if d.empty:
        raise ValueError('No data returned')
    return d

if 'screen' not in st.session_state:
    st.session_state.screen = None

with st.sidebar:
    st.header('Screen configuration')
    with st.form('screen_form'):
        tickers = st.text_area('Ticker universe (comma-separated)', 'AAPL,MSFT,NVDA,AMZN,META,GOOGL,AMD,AVGO,TSLA,PLTR')
        benchmark_symbol = st.text_input('Benchmark', 'SPY').strip().upper()
        direction_label = st.radio('Strategy', ['Bullish Swing', 'Bearish Swing'])
        research_mode = st.radio('Research mode', ['Confirmed EOD', 'Intraday Preview'],
                                 help='EOD excludes today until the next NY calendar day. Preview uses available 30-minute regular-session bars; it is not live.')
        run = st.form_submit_button('Run research screen', type='primary')
    if st.session_state.screen is not None:
        st.caption('Results persist until you run a new screen. Changing settings does not recalculate existing results.')

if run:
    symbols = list(dict.fromkeys(s.strip().upper() for s in tickers.split(',') if s.strip()))[:30]
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
                if b_preview is None:
                    errors.append(f'Benchmark {benchmark_symbol}: no current-session intraday bars; relative strength unavailable in preview.')
            except Exception as exc:
                errors.append(f'Benchmark {benchmark_symbol} intraday: {exc}')
        with st.spinner('Downloading data and calculating evidence...'):
            bar = st.progress(0)
            for i, symbol in enumerate(symbols):
                try:
                    eod = confirmed_daily(download(symbol), now)
                    baseline = score(eod, b_eod, direction)
                    result = baseline
                    preview_status = 'Not requested'
                    last_intraday = None
                    if research_mode == 'Intraday Preview':
                        try:
                            agg = aggregate_today_intraday(download(symbol, period='5d', interval='30m'), now)
                            pframe = preview_frame(eod, agg, now)
                            if pframe is not None:
                                result = score(pframe, b_preview, direction)
                                preview_status = 'Provisional — current-session 30m bars'
                                last_intraday = agg['last_bar_at']
                            else:
                                preview_status = 'Unavailable — showing confirmed EOD only'
                        except Exception as exc:
                            preview_status = 'Unavailable — showing confirmed EOD only'
                            errors.append(f'{symbol} preview: {exc}')
                    details[symbol] = {'result': result, 'baseline': baseline,
                                       'preview_status': preview_status, 'last_intraday': last_intraday}
                    rows.append({'Ticker': symbol, 'Price': result['close'],
                                 'Heuristic Score': result['score'],
                                 'Confluence': f"{result['aligned']}/{result['total']}",
                                 'Contradictions': result['contradictions'],
                                 'Readiness': result['readiness'], 'Data Date': result['data_date'],
                                 'RSI': result['rsi'], 'MFI': result['mfi'],
                                 'Data Status': preview_status if research_mode == 'Intraday Preview' else 'Confirmed prior session',
                                 'EOD Score': baseline['score']})
                except Exception as exc:
                    errors.append(f'{symbol}: {exc}')
                bar.progress((i+1)/len(symbols))
            bar.empty()
        st.session_state.screen = {'rows': rows, 'details': details, 'errors': errors,
            'direction': direction_label, 'benchmark': benchmark_symbol,
            'mode': research_mode, 'run_at': now.strftime('%Y-%m-%d %H:%M %Z')}
        st.session_state.pop('candidate_choice', None)

screen = st.session_state.screen
if screen is None:
    st.info('Choose a research mode and click **Run research screen**. Data downloads require internet access.')
else:
    st.subheader(f"Latest screen — {screen['direction']} — {screen['mode']}")
    st.caption(f"Run at {screen['run_at']} • Benchmark: {screen['benchmark']} • Yahoo Finance via yfinance (adjusted OHLCV; may be delayed/revised)")
    if screen['mode'] == 'Intraday Preview':
        st.warning('PROVISIONAL: intraday data is not real-time or guaranteed complete. Preview never replaces the confirmed EOD baseline. No current-session data means EOD-only fallback.')
    else:
        st.info('Confirmed EOD mode conservatively excludes the current New York calendar day, even after market close. This may delay same-evening updates.')
    if screen['rows']:
        table = pd.DataFrame(screen['rows']).sort_values(['Heuristic Score', 'Ticker'], ascending=[False, True])
        st.dataframe(table, use_container_width=True, hide_index=True)
        chosen = st.selectbox('Inspect candidate', table['Ticker'].tolist(), key='candidate_choice')
        item = screen['details'][chosen]
        result, baseline = item['result'], item['baseline']
        st.subheader(f"{chosen} — {result['readiness']}")
        st.caption(f"Data: {result['data_date']} • Score {result['score']}/100 • Support {result['aligned']}/5 • Contradictions {result['contradictions']}")
        if screen['mode'] == 'Intraday Preview':
            st.write(f"**Preview status:** {item['preview_status']}")
            if item['last_intraday']:
                st.caption(f"Last available intraday bar started at {item['last_intraday']}. This is not a quote timestamp or guaranteed complete bar.")
            st.write(f"**Confirmed EOD baseline:** {baseline['score']}/100, {baseline['readiness']} (as of {baseline['data_date']})")
            if item['last_intraday']:
                st.write(f"**Provisional change:** {result['score']-baseline['score']:+d} score points; readiness {baseline['readiness']} → {result['readiness']}")
        for name, status in result['statuses'].items():
            symbol = {'supportive': '✅', 'contradictory': '❌', 'inconclusive': '➖', 'unavailable': '❔'}[status]
            with st.expander(f"{symbol} {name.replace('_',' ').title()} — {status.title()}"):
                st.write(result['notes'][name])
        st.markdown('**Risk / limitations**')
        for warning in result['warnings']:
            st.write('• ' + warning)
        st.info('Readiness is not a buy/sell instruction. Intraday volume and MFI can be incomplete and are not normalized by time of day. Check charts, market events, liquidity and risk manually.')
    else:
        st.error('No securities could be screened. Review the errors below.')
    if screen['errors']:
        with st.expander(f"{len(screen['errors'])} data warnings / exclusions"):
            for error in screen['errors']:
                st.write('• ' + error)
