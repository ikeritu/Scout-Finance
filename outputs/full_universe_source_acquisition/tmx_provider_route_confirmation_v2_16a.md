# v2.16A - TMX Provider Route Confirmation

Status: **TMX_PROVIDER_ROUTE_CONFIRMED_PLAN_ONLY_FULL_SOURCE_BLOCKED**

Phase type: **provider-route-confirmation-only**

Generated at UTC: `2026-08-04T19:30:52.859409+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Previous provider closure

- Previous provider: `Euronext`
- Closure artifact: `outputs\full_universe_source_acquisition\euronext_closure_report_v2_15g.json`
- Closure status: `EURONEXT_CLOSED_PUBLIC_AND_ENDPOINT_ROUTE_ZERO_VALID_CANDIDATES_FULL_SOURCE_BLOCKED`
- Rows added by Euronext: `0`
- Closure recommended next phase: `v2.16A - TMX Provider Route Confirmation`

## Confirmed next provider

- Provider ID: `tmx_tsx_tsxv_official_equities`
- Provider name: `TMX / TSX / TSXV official equities`
- Country: `Canada`
- Scope: `TSX and TSXV listed equities`
- Route status: `CONFIRMED`
- Recommended next phase: `v2.16B - TMX Acquisition Plan`

## Decision matrix

- `provider_after_euronext`: **confirm_tmx_tsx_tsxv_as_next_route** — Open TMX route as v2.16 without touching canonical dataset. Basis: `v2.15G recommended_next_phase=v2.16A - TMX Provider Route Confirmation; euronext_rows_added=0; euronext_unique_candidates=0`
- `phase_scope`: **route_confirmation_only** — No network, no download, no parsing, no rebuild. Basis: `v2.16A confirms provider and scope only.`
- `tmx_initial_scope`: **tsx_and_tsxv_listed_equities** — Focus next acquisition plan on official TMX / TSX / TSXV equity sources. Basis: `TMX route is intended to cover Canadian listed equities after Euronext produced zero valid candidates.`
- `instrument_scope`: **equities_first_exclude_funds_by_default** — v2.16B must define exclusion logic before acquisition or parsing. Basis: `Existing source-acquisition policy excludes ETFs, ETNs, ETCs, funds, bonds and non-equity instruments unless explicitly approved.`
- `full_source_gate`: **remain_blocked** — Full source, full59k, scoring, OpenAI and broker layers remain blocked. Basis: `current_rows=38287; threshold=50000; rows_needed=11713`

## Checklist

- [x] v2.16A — confirm_tmx_provider_route — `plan_only`
- [x] v2.16A — confirm_current_rows_unchanged — `current_rows=38287`
- [x] v2.16A — keep_full_source_blocked — `full_source_gate=BLOCKED`
- [ ] v2.16B — identify_official_tmx_sources — `plan_only_until_approved`
- [ ] v2.16B — define_tmx_source_taxonomy — `no_download_yet`
- [ ] v2.16B — define_equity_vs_etf_fund_exclusion_policy — `no_parsing_yet`
- [ ] v2.16C — tmx_raw_acquisition — `only_after_v2_16b`
- [ ] v2.16D — tmx_validation — `no_rebuild`
- [ ] v2.16E — tmx_candidate_extraction_dry_run — `no_canonical_read`
- [ ] v2.16F — tmx_candidate_validation_against_canonical_dry_run — `read_only_canonical`

## Checks

- euronext_closure_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\euronext_closure_report_v2_15g.json
- euronext_closed_with_zero_valid_candidates: PASS (critical) — EURONEXT_CLOSED_PUBLIC_AND_ENDPOINT_ROUTE_ZERO_VALID_CANDIDATES_FULL_SOURCE_BLOCKED
- euronext_recommended_tmx_route: PASS (critical) — v2.16A - TMX Provider Route Confirmation
- euronext_rows_added_zero: PASS (critical) — rows_added=0
- tmx_provider_id_confirmed: PASS (critical) — tmx_tsx_tsxv_official_equities
- current_rows_unchanged: PASS (critical) — current_rows=38287
- rows_needed_unchanged: PASS (critical) — rows_needed=11713
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_network: PASS (critical) — network_download_performed=False
- no_raw_downloads: PASS (critical) — raw_files_downloaded=False
- no_normalization: PASS (critical) — normalization_performed=False
- no_net_new_filtering: PASS (critical) — net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) — expanded_universe_rebuilt=False

## Guards

- Network download performed in v2.16A: false
- Endpoint probe executed in v2.16A: false
- Raw files downloaded in v2.16A: false
- Raw files modified after write: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX / TSX / TSXV is confirmed as the next provider route after Euronext closure.

This phase is confirmation-only. It does not perform network access, downloads, parsing, canonical reads, canonical modifications, normalization, net-new filtering or rebuild.

## Recommended next phase

`v2.16B - TMX Acquisition Plan`
