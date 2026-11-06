# Stock Research MVP V0.3

Experimental Streamlit screening app. **Not validated trading advice.**

## What's new

- **Confirmed EOD (default):** excludes the current New York calendar day's daily candle, even after 4 p.m. This deliberately delays same-evening confirmation to avoid uncertain provider finalization.
- **Intraday Preview:** fetches available 30-minute regular-session bars for the current NY date, aggregates a provisional OHLCV candle, and recomputes technical evidence against the confirmed EOD baseline. Shows score delta, data status, and last bar timestamp. Does not replace the baseline.
- If intraday bars are unavailable (weekend, holiday, outside data availability, provider failure), the app displays an explicit **EOD-only fallback**. If the benchmark intraday data is unavailable, relative strength is marked unavailable rather than compared against mismatched dates.
- Results persist while switching tickers.

## GitHub / Streamlit update

Replace `app.py`, `engine.py`, `requirements.txt`, and `README.md` at the **root** of your existing GitHub repository; **add** `data_modes.py` at the root. Commit. Streamlit should redeploy; if it remains on an old version, use the Streamlit **My apps** management menu to reboot. Entry file remains `app.py`.

## Limitations

- This is **not a live-quote feed**. Yahoo/yfinance intraday data can be delayed, missing, revised, or restricted. Check provider usage rights before broader or commercial use.
- Preview is for current New York date only; on weekends/holidays it falls back to confirmed EOD.
- **Time-of-day volume normalization, complete 30-minute-bar verification, exchange-calendar holiday handling, and data-provider finalization checks are not yet implemented.** Intraday MFI/OBV can be skewed by partial-session volume. Preview is *not* a confirmed breakout or entry signal.
- Adjusted historical OHLCV may differ from TradingView's data source and adjustment settings. Validate indicator values on the same completed candle.
- Heuristic score weights and readiness thresholds are experimental, and there are no automated earnings, event, options, valuation, or portfolio checks.
- Do not store brokerage credentials, API keys, or sensitive holdings in a public test deployment.

## Local optional run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Smoke test

1. Select **Confirmed EOD**, enter `AAPL,MSFT,NVDA`, benchmark `SPY`, run Bullish Swing. Confirm the date is strictly before today's New York date.
2. Change candidate dropdown; table remains visible.
3. Switch to **Intraday Preview** and rerun. During a trading session with available intraday data, verify the provisional label, last bar time, EOD baseline and delta. Otherwise verify the explicit fallback.
4. Run Bearish Swing. Compare RSI/MFI and other indicator values on the same confirmed daily candle in TradingView.
