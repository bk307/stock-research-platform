"""Run: streamlit run app.py"""
import streamlit as st
import pandas as pd
from engine import score

st.set_page_config(page_title='Stock Research MVP', layout='wide')
st.title('Stock Research MVP — Technical Confluence')
st.caption('Research prototype • End-of-day data • Not a trading signal or investment advice')
st.warning('Scores are experimental. No earnings/calendar risk checks, options pricing, fundamental valuation, or live quotes are included yet.')

@st.cache_data(ttl=3600, show_spinner=False)
def download(ticker, period='2y'):
    import yfinance as yf
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise ValueError('No data returned')
    return df

with st.sidebar:
    st.header('Screen configuration')
    tickers = st.text_area('Ticker universe (comma-separated)', 'AAPL,MSFT,NVDA,AMZN,META,GOOGL,AMD,AVGO,TSLA,PLTR')
    benchmark_symbol = st.text_input('Benchmark', 'SPY').strip().upper()
    direction = st.radio('Strategy', ['Bullish Swing', 'Bearish Swing'])
    run = st.button('Run research screen', type='primary')

if run:
    symbols = list(dict.fromkeys(s.strip().upper() for s in tickers.split(',') if s.strip()))[:30]
    if not symbols:
        st.error('Enter at least one ticker.')
        st.stop()
    try:
        benchmark = download(benchmark_symbol)
    except Exception as e:
        benchmark = None
        st.warning(f'Benchmark unavailable: {e}')
    rows, details, errors = [], {}, []
    progress = st.progress(0)
    for i, symbol in enumerate(symbols):
        try:
            d = download(symbol)
            result = score(d, benchmark, 'bull' if direction=='Bullish Swing' else 'bear')
            details[symbol] = result
            rows.append({'Ticker':symbol,'Price':result['close'],'Heuristic Score':result['score'],
                         'Confluence':f"{result['aligned']}/{result['total']}",'Readiness':result['readiness'],
                         'RSI':result['rsi'],'MFI':result['mfi']})
        except Exception as e:
            errors.append(f'{symbol}: {e}')
        progress.progress((i+1)/len(symbols))
    if rows:
        table = pd.DataFrame(rows).sort_values('Heuristic Score', ascending=False)
        st.dataframe(table, use_container_width=True, hide_index=True)
        chosen = st.selectbox('Inspect candidate', table['Ticker'].tolist())
        result = details[chosen]
        st.subheader(f'{chosen} — {result["readiness"]}')
        st.write('**Evidence categories**')
        for name, passed in result['signals'].items():
            st.write(('✅' if passed else '⚠️') + ' ' + name.replace('_',' ').title())
        st.write('**Limitations / warnings:** ' + ('; '.join(result['warnings']) if result['warnings'] else 'No automated warning from available checks'))
        st.info('A category marked ⚠️ is not necessarily bearish; it may be unconfirmed. Review the chart, event calendar, liquidity and position risk manually.')
    if errors:
        with st.expander(f'{len(errors)} data errors / exclusions'):
            st.write('\n'.join(errors))
else:
    st.info('Select a direction and click **Run research screen**. Data downloads require internet access.')
