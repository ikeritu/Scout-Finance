# v2.27B — Export Pack Design

**Status:** `EXPORT_PACK_CONTRACT_APPROVED_CATALOG_EXPORTS_AUTHORIZED_RANKING_EXPORTS_BLOCKED`

The export contract is ready for implementation.

## Authorized now

- Full 43,089-row universe catalog
- Filtered catalog
- Segment summaries
- Watchlist import template
- Analyst catalog ZIP bundle
- Metadata-only asset comparisons

## Gated or blocked

- Diagnostic quality pack: explicit internal mode only
- Production ranking CSV/XLSX: **blocked**
- Score, rank, recommendation and signal columns: **absent** until the scoring pointer authorizes them

Every bundle contains `README.md`, `manifest.json`, `data_dictionary.csv`, data files and member hashes. CSV output uses deterministic columns, RFC 4180 quoting, explicit null semantics and formula-injection protection. ZIP paths are traversal-safe.

No pointer or source dataset was modified.

**Next:** v2.27C - Watchlist Builder.
