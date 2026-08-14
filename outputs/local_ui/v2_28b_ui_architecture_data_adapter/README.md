# v2.28B — UI Architecture & Data Adapter

**Status:** `UI_FOUNDATION_IMPLEMENTED_POINTER_SAFE_FAIL_CLOSED_LEGACY_APP_UNTOUCHED`

A new safe UI entrypoint, `app_v2_28.py`, is implemented alongside the untouched legacy `app.py`.

## Foundation

- Typed application state
- Safe repository path resolution
- Operational universe pointer and SHA-256 validation
- Fail-closed scoring pointer state machine
- Read-only maintenance summary
- Eight-screen navigation registry
- Streamlit status shell with no external calls or pipeline execution

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_v2_28.py
```

The current expected score state is `SCORING_UNAVAILABLE`; the catalog/watchlist/report workflow remains available. Legacy ranking helpers are not imported or called.

**Next:** v2.28C - Catalog & Watchlist UI.
