# Stock Research MVP — Phase 1

A **local, manually run**, end-of-day technical confluence prototype. It does **not** execute trades, produce AI-generated research, or provide real-time alerts.

## Run

1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Create an environment: `python -m venv .venv`
4. Activate it: Windows `.venv\Scripts\activate`; macOS/Linux `source .venv/bin/activate`.
5. Install dependencies: `pip install -r requirements.txt`
6. Start: `streamlit run app.py`
7. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## What works

- Manually screen up to 30 tickers against SPY (or another benchmark).
- Calculate SMA20/50/200, RSI14, MACD histogram, OBV, MFI14, ATR14, and relative strength.
- Rank bullish and bearish candidates using five broad evidence categories.
- Show readiness as Emerging / Developing / Confirmed / Extended / No setup.
- Inspect category-level evidence and warnings; errors are shown, not hidden.

## Critical limitations

- Uses `yfinance` as a **prototype-only** data source; availability, adjustments, licensing and reliability must be evaluated before production use. No assumption of commercial redistribution rights.
- Scores and thresholds are **heuristics, not validated**. The five categories are not statistically independent, and no predictive edge is claimed.
- Price data are auto-adjusted; OHLC and volume can differ from your chart provider.
- Does **not** check earnings dates, SEC filings, fundamentals, sector regime, option spreads, position sizing, stop placement, taxes, or corporate actions beyond provider adjustments.
- Data are downloaded on demand and cached for one hour; this is **not** scheduled monitoring.
- No point-in-time constituent universe, survivorship-safe backtesting, or transaction-cost model.
- No automated orders, alerts, AI-generated claims, or personalized recommendations.

## Planned build order

1. Verify indicator parity against TradingView and add tests, data freshness and quality gates.
2. Formalize strategy-specific scoring, risk/reward and event exclusions; backtest without look-ahead.
3. Add fundamentals and two distinct long-term screens: Quality at a Discount; Deep Value / Turnaround.
4. Add source-grounded AI research briefs and a skeptical second-opinion checklist.
5. Add holdings, transactions, thesis history, closed positions and re-entry watchlist.
6. Add options research, with chain liquidity and payoff/risk analysis.

## Design principle

The software gathers and calculates evidence. The investor makes decisions. Missing or contradictory evidence must remain visible.
