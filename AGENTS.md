# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
A portal of independent **Streamlit** data apps (Python). Each app is a standalone script that is run directly with `streamlit run <path>.py`. There is no single entrypoint, no build step, no test suite, and no lint config. Most apps under `app_*`, `APP_*`, and `apps_tat_enaex/*` either scrape Chilean public data sources (SII, INE, MOP — see `readme.md`) or process user-uploaded/pasted spreadsheets.

### Dependencies
Python deps come from two files: `requirements.txt` (root) and `apps_tat_enaex/requirements.txt`. The startup update script installs both with `pip install --user --break-system-packages`. The `streamlit` console script lands in `~/.local/bin`, which is **not on PATH by default** — prefix commands with `export PATH="$HOME/.local/bin:$PATH"` or invoke via `python3 -m streamlit ...`.

### Running an app
```
export PATH="$HOME/.local/bin:$PATH"
streamlit run app_sii_dolar/app_sii_dolar.py --server.port 8501 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
```
Swap the script path to run any other app (e.g. `app_ine_ipc/app_ine_ipc.py`, `apps_tat_enaex/app_tat_match/app_tat_match.py`). Health check: `curl http://localhost:8501/_stcore/health` returns `ok`. The `.devcontainer/devcontainer.json` uses `app_sii_dolar/app_sii_dolar.py` as the default app.

### Notes / gotchas
- The data-scraping apps (`app_sii_*`, `app_ine_*`, `app_indice_polinomico_mop`) require outbound internet access to the source sites; they fetch live data when you click the "Generar resumen"-style button. Network to `sii.cl`/`ine.gob.cl` works from this environment.
- The TAT / contracts apps (`apps_tat_enaex/*`, `APP_TAT/*`, `APP_CONTRATOS_DASHBOARD/*`, `app_sievo`) expect the user to upload Excel/CSV files in the UI and do not need internet.
- There are **no lint or automated tests** in this repo. The best available programmatic check is `python3 -m py_compile <files>`.
