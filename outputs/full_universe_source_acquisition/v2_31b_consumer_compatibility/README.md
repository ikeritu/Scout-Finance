# v2.31B — Consumer Compatibility Regression

Status: **PASS · no breaking changes · no migration required**.

The previous operational CSV and the promoted XZ catalog expose the same 43,089 stable identities. No identity was added, removed or changed, so existing watchlists continue to resolve without migration.

## Consumers covered

Pointer adapter, catalog loader, stable identities, search, filters, pagination, asset detail, watchlists, CSV export, universe reports, maintenance state, scoring fail-closed and rollback reference.

All 13 consumer contracts pass. No pointer or user watchlist was modified.

Next: **v2.31C — maintenance state and alert rebaseline**.
