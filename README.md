# Stock Research MVP — V0.5

Experimental research prototype. **Not a trading signal, real-time quote service, or validated investment model.**

## What's new

- **Research priority:** an explicit, deterministic sorting aid based on readiness, contradictions, and recent *confirmed* EOD score trajectory. A higher rank is not evidence of future returns.
- **Evidence changes:** displays exactly which of five category statuses changed from the confirmed EOD baseline to a usable intraday preview.
- **Data confidence:** separate Baseline/Review/Provisional/Stale/Incomplete/Unavailable labels. Intraday preview is refused when the most recent 30-minute bar *start* is more than 45 minutes old, or benchmark data is similarly old. Bar completion remains unverified even when fresh.
- **Portable history:** downloads a cumulative CSV and can re-import it. History resides in Streamlit session memory until exported; it is **not** permanent server-side storage. Save your history CSV after each session and import it on your next visit. An earlier V0.4 snapshot may be imported if it includes the required timestamp/strategy/mode/ticker/score fields.

## Update existing Streamlit app

1. Download ZIP and extract it.
2. Upload/replace **app.py, engine.py, data_modes.py, universe.py, requirements.txt, README.md** in the root of your existing GitHub repository.
3. **Add new files `research_quality.py` and `history.py`** to the same root. Do not upload only the ZIP.
4. Commit changes. Streamlit should redeploy; if needed reboot from Streamlit Community Cloud's **My apps** management menu.
5. Run custom `AAPL,MSFT,NVDA` Confirmed EOD, then Intraday Preview. Check `Data confidence`, `Priority`, `Evidence changes`, and CSV exports. Try reimporting the cumulative CSV in the sidebar.

## Limitations and safeguards

- Intraday market data from Yahoo Finance/yfinance can be delayed, incomplete, revised, or unavailable. A 30-minute bar's timestamp is its *start*, not proof it closed. No real-time claims. No time-of-day volume normalization.
- EOD deliberately excludes the current New York calendar day, including after the close. Weekend/holiday handling is approximate.
- Research priority is a transparent **heuristic**, not a trained predictive model or calibrated probability.
- A 5-session EOD score delta compares two historic indicator snapshots; it is not actual multi-day stored history and does not predict returns.
- Manual CSV history is not durable cloud storage, and importing/exporting does not automate scheduling. It is also not a point-in-time fundamentals or survivorship-safe backtest dataset.
- No earnings/event calendar, liquidity qualification, financial valuation, options chains, execution risk, or automated trade execution.
- Public GitHub code and public Streamlit hosting: **do not enter private holdings, account numbers, credentials, or API keys**.

## Run locally (optional)

```bash
pip install -r requirements.txt
streamlit run app.py
```
