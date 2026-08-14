# v2.28C — Catalog & Watchlist UI

Status: **COMPLETE**

- Metadata-only operational catalog with search, five filters and pagination.
- Stable-identity asset selection and descriptive asset detail.
- Local JSON watchlists with notes, tags, deduplication and atomic backups.
- Safe CSV download and explicit preservation of `Unknown` metadata.
- Fail-closed exclusion of scores, ranks, signals and recommendations.

Validation: `python tests/qa_catalog_watchlist_ui_v2_28c.py`

Expected: `PASS: catalog/search/filters/unknown/pagination/identity/watchlist/dedupe/export/fail-closed`
