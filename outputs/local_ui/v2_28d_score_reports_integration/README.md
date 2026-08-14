# v2.28D — Score Explorer & Reports Integration

Status: **COMPLETE**

- Score Explorer remains fail-closed when production scoring is unavailable.
- Diagnostic data-readiness view requires explicit acknowledgement.
- Diagnostic artifact hash and row count are verified before display.
- `dry_run_rank` is ignored and assets are never ordered by diagnostic score.
- Universe, watchlist and acknowledged diagnostic reports are downloadable as Markdown or HTML.
- Every report has a downloadable provenance manifest.

Validation: `python tests/qa_score_reports_ui_v2_28d.py`

Expected: `PASS: diagnostic-ack/hash/rows/no-ranking/components/reports/manifest/fail-closed`
