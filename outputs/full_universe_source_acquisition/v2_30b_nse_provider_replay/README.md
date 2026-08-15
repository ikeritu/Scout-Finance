# v2.30B — NSE Provider Evidence Recovery and Controlled Replay

Status: **14/14 immutable replay PASS; live freshness not verified; promotion HOLD**.

The archived official NSE equity file was recovered with its URL, acquisition timestamp and hashes. The controlled replay matched all 2,013 held identities against that source using `symbol + ISIN`.

## Result

- Official raw NSE rows: 2,397; unique symbols and ISINs: 2,397.
- Held/replayed rows: 2,013.
- Identity matches: 2,013/2,013; missing: 0; duplicates: 0.
- Three names contain only whitespace-normalization differences.
- Repository replay provider coverage: 14/14.
- Total row disposition: 43,089/43,089.

The validated alias is constrained to `provider=nse_india_v2_17g`, `exchange=NSE`, `country=India`, producing canonical `source_provider=nse_india`. It has not been applied to the operational dataset.

No live request was made, so freshness and promotion remain blocked. Universe and scoring pointers are unchanged.

Next: **v2.30C — reconcile and disposition all 2,013 NSE rows before candidate materialization**.
