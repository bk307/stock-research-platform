# Stock Research MVP V0.8 — Historical Opportunity Tracking

## What's new
- Historical opportunity tracking section below the latest screening/candidate details.
- Comparison table for each ticker's latest and preceding **distinct Confirmed EOD data dates**: score, change, evidence count, readiness, and contradictions.
- Per-ticker historical score chart and observation table.
- Separate strategy and benchmark selection. Intraday Preview snapshots are excluded from historical EOD comparisons.
- Keeps V0.7 navy/charcoal/copper theme, password gate, cloud persistence, CSV backup, and research screen.
- Includes the V0.7 Supabase `sb_secret_` API-header fix.

## Deploy
1. Download and unzip this package.
2. In the existing GitHub `stock-research-platform` repository, replace the Python files and `requirements.txt`, update README, and retain `.streamlit/config.toml` at repository root. Add the **new** `opportunity_history.py` file at repository root next to `app.py`.
3. Commit changes; wait for Streamlit Community Cloud to redeploy. If necessary reboot via Manage app.
4. Keep your existing Streamlit Secrets (`APP_PASSWORD`, `SUPABASE_URL` (base URL only), `SUPABASE_SERVICE_ROLE_KEY`). Never commit secrets to GitHub.
5. Unlock the dashboard and scroll beneath candidate details to **Historical opportunity tracking — Confirmed EOD**. No SQL migration is required.

## Validation
- Verify that existing Supabase rows load without cloud error and history appears in the new section.
- With only one distinct EOD date per ticker, expect `Insufficient history`, **not** a fabricated trend.
- Rerun a screen on the same data date: it must not create a second EOD observation in the historical comparison. It may create another stored run snapshot.
- After a subsequent completed trading session, compare two distinct data dates and verify score delta.
- Verify Intraday Preview observations do not enter Confirmed EOD trends.
- Confirm cloud storage writes and check rows in Supabase. Export a CSV backup.

## Important limitations
The research scores and labels are unvalidated heuristics, not recommendations or forecasts. A change in score is not a return or a predictive performance claim. Yahoo Finance data may be delayed or revised. This version does not implement event/earnings filters, options liquidity/risk checks, fundamentals, or automated trades. Streamlit password protection is a shared application gate, not a multi-user identity system. Supabase secret keys must remain in Streamlit server-side Secrets.
