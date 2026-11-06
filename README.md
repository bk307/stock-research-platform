# Stock Research MVP V0.4 — Opportunity Discovery

This is an experimental, browser-deployable Streamlit stock research dashboard. It is **not** a validated trading strategy, real-time feed, investment recommendation, or comprehensive market scanner.

## What changed since V0.3

- Built-in **illustrative 50-ticker starter universe** (not a liquidity-qualified or exhaustive U.S. universe), plus custom ticker entry.
- Up to 50 tickers per manual run; default 15 to reduce provider throttling. Large runs may be slow or fail under free-data rate limits.
- Five-session **confirmed EOD score change** and improving/unchanged/deteriorating status, calculated with historical date-cut benchmark data. This is a simple change metric, not an efficacy claim.
- Basic data-quality flags for stale EOD observations, zero volume, missing data, and unavailable benchmark.
- Intraday freshness warning; stale/unavailable previews fall back to confirmed EOD.
- Downloadable **CSV screening snapshot** including timestamp, mode, benchmark, strategy, and ticker results.
- Two screenshots of V0.3 validation saved under `validation_screenshots/` in the ZIP. They are historical test records, not live results.

## Deploy / upgrade from V0.3

1. Download and extract the ZIP.
2. In your existing GitHub `stock-research-platform` repository, replace `app.py`, `engine.py`, `data_modes.py`, `requirements.txt`, and `README.md` and **add `universe.py`**. Keep these files at repository root.
3. Commit the changes. Streamlit Community Cloud should redeploy; if not, use its app-management menu to reboot.
4. Select **Custom tickers** and screen `AAPL,MSFT,NVDA` first; then test **Starter universe** with 5–10 tickers.
5. Compare confirmed EOD with Intraday Preview. Export CSV and save it locally for history.

No Python installation is needed for this GitHub/Streamlit workflow.

## Important constraints

- Yahoo Finance via `yfinance` is used for prototype research only; data can be delayed, stale, incomplete, revised, or rate-limited. Confirm data rights and licensing before scaling or redistributing.
- Confirmed EOD deliberately excludes the current New York date, even after close. Holidays and special sessions are not verified against an exchange calendar.
- Intraday preview aggregates available 30-minute bars. The latest bar may be incomplete. A 90-minute freshness threshold is heuristic and is not a real-time guarantee.
- Screening results are held only in Streamlit session state. **CSV exports are manual; they do not automatically persist across app restarts.** Use a durable database in a future release for history and automated monitoring.
- No automatic earnings calendar, fundamentals, valuation, options, event risk, sector mapping, or position sizing.
- Starter universe membership is curated, static, and **not validated for current liquidity**. It is not the whole U.S. stock market.
- Five-session change is calculated on completed EOD sessions. Intraday and EOD rankings should not be treated as interchangeable.
- Do not enter private holdings, brokerage credentials, or secrets into a public prototype.

## Package files

- `app.py` — Streamlit dashboard
- `engine.py` — experimental technical scoring
- `data_modes.py` — confirmed EOD and intraday preview construction
- `universe.py` — starter universe
- `requirements.txt` — dependencies
- `README.md` — this file
- `validation_screenshots/` — archived V0.3 EOD and intraday screenshots
