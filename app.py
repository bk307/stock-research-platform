"""Stock Research MVP V0.2. Launch: streamlit run app.py"""
import pandas as pd
import streamlit as st
from engine import score

st.set_page_config(page_title='Stock Research MVP V0.2', layout='wide')
st.title('Stock Research MVP — Technical Confluence')
st.caption('V0.2 • Experimental end-of-day research • Not a trading recommendation')
st.warning('No automated earnings/event checks, options pricing, fundamental valuation, or live quotes. Scores are not validated.')

@st.cache_data(ttl=3600, show_spinner=False)
def download(ticker: str, period: str = '2y'):
    import yfinance as yf
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise ValueError('No data returned')
    return df

if 'screen' not in st.session_state:
    st.session_state.screen = None

with st.sidebar:
    st.header('Screen configuration')
    with st.form('screen_form'):
        tickers = st.text_area('Ticker universe (comma-separated)', 'AAPL,MSFT,NVDA,AMZN,META,GOOGL,AMD,AVGO,TSLA,PLTR')
        benchmark_symbol = st.text_input('Benchmark', 'SPY').strip().upper()
        direction_label = st.radio('Strategy', ['Bullish Swing', 'Bearish Swing'])
        run = st.form_submit_button('Run research screen', type='primary')
    if st.session_state.screen is not None:
        st.caption('Results remain visible until you run a new screen. Changing configuration does not recalculate existing results.')

if run:
    symbols = list(dict.fromkeys(s.strip().upper() for s in tickers.split(',') if s.strip()))[:30]
    if not symbols or not benchmark_symbol:
        st.error('Enter at least one ticker and a benchmark.')
    else:
        direction = 'bull' if direction_label == 'Bullish Swing' else 'bear'
        rows, details, errors = [], {}, []
        try:
            benchmark = download(benchmark_symbol)
        except Exception as exc:
            benchmark = None
            errors.append(f'Benchmark {benchmark_symbol}: {exc}')
        with st.spinner('Downloading daily data and calculating evidence...'):
            bar = st.progress(0)
            for i, symbol in enumerate(symbols):
                try:
                    result = score(download(symbol), benchmark, direction)
                    details[symbol] = result
                    rows.append({
                        'Ticker': symbol, 'Price': result['close'],
                        'Heuristic Score': result['score'],
                        'Confluence': f"{result['aligned']}/{result['total']}",
                        'Contradictions': result['contradictions'],
                        'Readiness': result['readiness'], 'Data Date': result['data_date'],
                        'RSI': result['rsi'], 'MFI': result['mfi'],
                    })
                except Exception as exc:
                    errors.append(f'{symbol}: {exc}')
                bar.progress((i + 1) / len(symbols))
            bar.empty()
        # Store a complete snapshot so dropdown changes don't trigger downloads.
        st.session_state.screen = {
            'rows': rows, 'details': details, 'errors': errors,
            'direction': direction_label, 'benchmark': benchmark_symbol,
        }
        st.session_state.pop('candidate_choice', None)

screen = st.session_state.screen
if screen is None:
    st.info('Choose a direction and click **Run research screen**. Data downloads require internet access.')
else:
    st.subheader(f"Latest completed screen — {screen['direction']}")
    st.caption(f"Benchmark: {screen['benchmark']} • Data source: Yahoo Finance via yfinance (adjusted daily OHLCV) • Data may be delayed, revised, or incomplete")
    if screen['rows']:
        table = pd.DataFrame(screen['rows']).sort_values(['Heuristic Score', 'Ticker'], ascending=[False, True])
        st.dataframe(table, use_container_width=True, hide_index=True)
        chosen = st.selectbox('Inspect candidate', table['Ticker'].tolist(), key='candidate_choice')
        result = screen['details'][chosen]
        st.subheader(f"{chosen} — {result['readiness']}")
        st.caption(f"Last daily bar: {result['data_date']} • Score {result['score']}/100 • Support {result['aligned']}/5 • Contradictions {result['contradictions']}")
        for name, status in result['statuses'].items():
            symbol = {'supportive': '✅', 'contradictory': '❌', 'inconclusive': '➖', 'unavailable': '❔'}[status]
            with st.expander(f"{symbol} {name.replace('_', ' ').title()} — {status.title()}"):
                st.write(result['notes'][name])
        st.markdown('**Risk / limitations**')
        for warning in result['warnings']:
            st.write('• ' + warning)
        st.info('Readiness is not a buy/sell instruction. Inconclusive evidence is not automatically bearish; unavailable evidence is not scored as confirmation. Review price chart, events, liquidity, and position risk manually.')
    else:
        st.error('No securities could be screened. Review the errors below.')
    if screen['errors']:
        with st.expander(f"{len(screen['errors'])} data warnings / exclusions"):
            for error in screen['errors']:
                st.write('• ' + error)
