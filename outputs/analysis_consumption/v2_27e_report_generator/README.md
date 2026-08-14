# v2.27E — Report Generator

**Status:** `REPORT_GENERATOR_IMPLEMENTED_CATALOG_AND_WATCHLIST_READY_DIAGNOSTIC_GATED`

A functional local report generator now produces Markdown or responsive HTML.

## Available

- Operational universe status report
- Metadata-only watchlist report
- Explicitly gated data-readiness diagnostic

Every report receives a JSON sidecar manifest with source paths, SHA-256 hashes, timestamp, consumer state, output hash and safety flags.

## Blocked

Production ranking reports remain unavailable while the scoring pointer is fail-closed. Reports never contain investment recommendations, buy/sell signals, allocations or broker actions.

```bash
python scripts/report_generator_v2_27e.py --type universe --universe-pointer POINTER.json --scoring-pointer SCORING.json --output universe.md
python scripts/report_generator_v2_27e.py --type watchlist --watchlist watchlist.json --scoring-pointer SCORING.json --format html --output watchlist.html
```

**Next:** v2.27F - Analyst Workflow Review.
