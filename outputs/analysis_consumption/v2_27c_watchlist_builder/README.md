# v2.27C — Watchlist Builder

**Status:** `WATCHLIST_BUILDER_IMPLEMENTED_METADATA_ONLY_SCORING_INDEPENDENT`

A functional metadata-only watchlist CLI is implemented.

## Commands

```bash
python scripts/watchlist_builder_v2_27c.py init my_watchlist.json --name "My watchlist"
python scripts/watchlist_builder_v2_27c.py add my_watchlist.json --catalog universe.csv --ticker SAN --exchange XMAD --tags bank,review --note "Review fundamentals"
python scripts/watchlist_builder_v2_27c.py import my_watchlist.json --catalog universe.csv --input watchlist_import_template.csv
python scripts/watchlist_builder_v2_27c.py list my_watchlist.json
python scripts/watchlist_builder_v2_27c.py validate my_watchlist.json --catalog universe.csv
python scripts/watchlist_builder_v2_27c.py export my_watchlist.json --output my_watchlist.csv
```

The builder rejects ambiguous or unknown assets, prevents duplicate identities, writes atomically with a backup and neutralizes spreadsheet formulas in CSV text.

Watchlists contain no scores, ranks, recommendations, signals or allocations. They remain usable with scoring fail-closed.

**Next:** v2.27D - Score Explorer Prototype.
