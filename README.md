# Stock Research MVP V0.6 — Research History and Clarity

## Deploy
Replace `app.py`, `engine.py`, `data_modes.py`, `universe.py`, `research_quality.py`, `history.py`, `requirements.txt`, and `README.md` in the existing GitHub repo. **Add `cloud_history.py`.** Commit; Streamlit will redeploy.

## Required security configuration
Your Streamlit Community Cloud app URL may be publicly reachable. Before using V0.6, go to **Streamlit Community Cloud → My apps → your app → Settings → Secrets** and add:

```toml
APP_PASSWORD = "CHOOSE_A_LONG_UNIQUE_PASSWORD"
```

Do not commit this password or any cloud key to GitHub. The app will refuse to run without a password. This is a basic shared password gate, **not full per-user authentication**. Anyone who knows the password shares access to the same cloud history. Do not enter brokerage credentials or sensitive personal financial information.

## Optional persistent history (Supabase)
Create a Supabase project (free-tier eligibility and limits may change). Open its SQL editor and run:

```sql
create table if not exists public.research_snapshots (
  record_id text primary key,
  run_at timestamptz not null,
  ticker text not null,
  payload jsonb not null
);
create index if not exists research_snapshots_run_at_idx
  on public.research_snapshots (run_at);
alter table public.research_snapshots enable row level security;
-- Do not create anonymous access policies.
```

Then add to **Streamlit app Settings → Secrets** (not GitHub):

```toml
APP_PASSWORD = "CHOOSE_A_LONG_UNIQUE_PASSWORD"
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SECRET_SERVER_SIDE_KEY"
```

**Security:** The service-role key bypasses row-level security. Keep it exclusively in server-side Streamlit Secrets. This prototype's shared password is not a substitute for proper authentication, access controls, auditing, and production security. A public Streamlit app with a shared password is appropriate only for non-sensitive prototype research.

When cloud configuration is present, the app loads history on first unlock and writes each completed screen to Supabase. If a write fails, the app shows a failure message; export CSV as a backup. Without Supabase, session-only CSV workflows remain available.

## V0.6 improvements
- Compact discovery table and expandable detailed metrics.
- Short supporting-versus-contradictory evidence summary.
- Duplicate-resistant history snapshots (same run timestamp, mode, strategy, ticker).
- Excel-safe CSV export splits `2/5` into numeric Supporting Categories and Total Categories.
- Optional Supabase persistence; required shared-password gate.

## Validation
1. Set APP_PASSWORD in Streamlit Secrets and unlock.
2. Run AAPL,MSFT,NVDA in EOD and inspect details.
3. Download Excel-safe CSV and check numeric confluence fields.
4. If using Supabase, run a screen, reboot app, unlock, and verify history restored.
5. Rerun same screen widget interactions and confirm no extra history rows are added.

**Limitations:** Scores remain unvalidated. Data may be delayed; intraday previews are provisional and fall back to EOD when stale. No automated fundamental, earnings, options, or execution risk checks.
