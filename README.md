# Stock Research MVP V0.7

## What's changed
- Navy/charcoal Streamlit theme with copper accent in `.streamlit/config.toml`.
- Supabase REST adapter matches the **existing** `public.research_snapshots` table created with the earlier V0.7 SQL. No additional SQL migration required.
- Keeps V0.6 screens, CSV exports, evidence explanations and password gate.
- Adds cloud-connection health handling; CSV export remains the fallback if Supabase is unavailable.

## Deployment
1. Keep your working V0.6 deployment available until V0.7 is verified.
2. Upload/replace all `.py` files, `requirements.txt`, and `README.md` in the existing GitHub repository.
3. Create a **`.streamlit` folder** at the repository root and upload `config.toml` inside it. GitHub web upload can create the folder by naming the new file `.streamlit/config.toml`.
4. In Streamlit Community Cloud > My apps > your app > Settings > Secrets, preserve your existing `APP_PASSWORD` and add the following **with your actual values entered there only**:

```toml
APP_PASSWORD = "your-existing-password"
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-server-side-secret-key"
```

A newer Supabase `sb_secret_...` key may be used if it has the appropriate database privileges. The legacy `service_role` key is also supported. Never commit credentials or a local `secrets.toml` file to GitHub. The secret key bypasses Row Level Security; keep it exclusively server-side. This simple app password is not full multi-user authentication.

5. Save Secrets and let Streamlit restart; if necessary reboot from My apps.
6. Unlock the app, run a small **Confirmed EOD** screen (e.g. AAPL, MSFT, NVDA), and verify that the history caption says `Saved latest screen to cloud.`
7. In Supabase > Table Editor > `research_snapshots`, verify three rows with ticker, score, strategy, timestamp and `snapshot_id`.
8. Reboot the Streamlit app and unlock it again. The same history should load automatically. Check the cumulative CSV.

## Troubleshooting
- `HTTP 401` or `HTTP 403`: check the project URL and secret key; do not post keys or full logs containing secrets.
- `HTTP 400`: table schema mismatch or invalid field. Verify the table uses the SQL from the earlier V0.7 instructions and the deployed `cloud_history.py` is the new version.
- `HTTP 404`: project URL or table path incorrect.
- If cloud sync fails, download cumulative CSV before closing the session. Don't assume data was saved remotely.
- Public GitHub repository and a password form are **not** sufficient security for real brokerage credentials or sensitive holdings. Use this prototype only with non-sensitive research data.

## Limitations
- Historical research scores are experimental, not validated forecasts.
- Supabase connection has not been exercised against your live project by the author; test the first write and restart explicitly.
- The dark theme uses native Streamlit styling; not every third-party table/chart element will exactly match the palette.
