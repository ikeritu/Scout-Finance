# v2.16B - TMX Acquisition Plan

Status: **TMX_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED_FULL_SOURCE_BLOCKED**

Phase type: **acquisition-plan-only**

Generated at UTC: `2026-08-04T19:42:40.833463+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Provider

- Provider ID: `tmx_tsx_tsxv_official_equities`
- Provider name: `TMX / TSX / TSXV official equities`
- Country: `Canada`
- Scope: `TSX and TSXV listed equities`
- Route confirmation artifact: `outputs\full_universe_source_acquisition\tmx_provider_route_confirmation_v2_16a.json`

## Acquisition plan summary

- Source candidates: `7`
- Primary source: `tmx_listed_company_directory`
- Supporting sources: `tmx_equity_symbol_lookup`, `tmx_tsxv_lcdb_search`, `tmx_money_stocklists`, `tmx_money_recent_listings`, `tmx_newsroom_equity_financing_statistics`
- Paid/controlled fallback: `tmx_datalinx_reference_data`
- Taxonomy policy rows: `8`
- Risk rows: `8`
- Critical failed checks: `0`

## Source candidates

- `tmx_listed_company_directory` priority=1 — TSX/TSXV Listed Company Directory — decision=`primary_candidate_source` — https://www.tsx.com/en/listings/listing-with-us/listed-company-directory
- `tmx_equity_symbol_lookup` priority=2 — TMX apps equity search quick view — decision=`primary_probe_seed` — https://apps.tmx.com/HttpController?GetPage=SearchEquitiesQuickViewPage&language=en
- `tmx_tsxv_lcdb_search` priority=3 — TSX Venture Listed Company Database Search — decision=`tsxv_supplement_probe_seed` — https://apps.tmx.com/TSXVenture/TSXVentureHttpController?GetPage=LcdbSearch
- `tmx_money_stocklists` priority=4 — TMX Money Stocklists — decision=`supporting_probe_seed` — https://money.tmx.com/stock-lists
- `tmx_money_recent_listings` priority=5 — TMX Money Recent Listings — decision=`supporting_recent_changes_source` — https://money.tmx.com/stock-list/RECENT_LISTINGS_SYMBOLS
- `tmx_newsroom_equity_financing_statistics` priority=6 — TMX Equity Financing Statistics — decision=`supporting_sanity_check_source` — https://www.tmx.com/en/newsroom/press-releases
- `tmx_datalinx_reference_data` priority=7 — TMX Datalinx / TMX Info Services reference data — decision=`documented_fallback_not_executed_by_default` — https://www.tmxinfoservices.com/

## Taxonomy policy

- `include` — common_shares_or_ordinary_shares — policy=`include_if_company_equity_and_listed_on_tsx_or_tsxv`
- `include_review` — preferred_shares — policy=`include_only_if_existing_project_policy_allows_preferred_equity`
- `include_review` — capital_pool_companies — policy=`review_in_v2_16d_before_inclusion`
- `exclude_by_default` — etf_etp_fund — policy=`exclude`
- `exclude_by_default` — cdr — policy=`exclude`
- `exclude_by_default` — warrants_rights_units_receipts — policy=`exclude`
- `exclude_by_default` — debt_and_fixed_income — policy=`exclude`
- `exclude_or_review` — nex_inactive_issuers — policy=`exclude_unless_explicitly_approved`

## Risk matrix

- `dynamic_html` severity=`high` — Directory pages may be rendered dynamically. Mitigation: v2.16C raw acquisition captures landing HTML only; v2.16D validates whether endpoint discovery is needed.
- `no_isin_in_public_directory` severity=`high` — TMX public pages may expose symbol/name/exchange but not ISIN. Mitigation: Use ISIN where available; otherwise validate canonical matching policy in later dry-run before rebuild.
- `instrument_type_ambiguity` severity=`high` — Public lists may mix common equity, ETFs, CDRs, warrants, rights, receipts or funds. Mitigation: Keep taxonomy exclusions explicit and validate type markers before candidate extraction.
- `symbol_suffixes` severity=`medium` — Canadian symbols can include suffixes/classes such as .A, .B, .H, preferred series, or special forms. Mitigation: Do not normalize symbols in v2.16B/C; defer symbol normalization to a specific dry-run validation phase.
- `tsx_vs_tsxv_vs_nex` severity=`medium` — TSX, TSXV and NEX may require different treatment. Mitigation: Record exchange/market as raw field and keep NEX excluded or review-only unless approved.
- `paid_reference_data` severity=`medium` — Best official reference data may be behind TMX Datalinx licensing. Mitigation: Document paid/controlled route but do not access it without authorization.
- `recent_lists_not_comprehensive` severity=`medium` — TMX Money stocklists and recent listings are partial lists. Mitigation: Use them only for discovery/sanity checks, not as primary universe source.
- `duplicate_share_classes` severity=`medium` — Multiple classes or preferred lines may create duplicates at issuer level. Mitigation: Later canonical dry-run must define duplicate key policy: ISIN first, then exchange+symbol, then issuer review.

## v2.16C checklist

- [ ] v2.16C — create_raw_directory — `raw_dir_must_not_exist_before_run`
- [ ] v2.16C — download_tmx_listed_company_directory_landing_html — `download_only_no_parse`
- [ ] v2.16C — download_tmx_equity_symbol_lookup_landing_response — `download_only_no_query_sweep`
- [ ] v2.16C — download_tsxv_lcdb_search_landing_response — `download_only_no_query_sweep`
- [ ] v2.16C — download_tmx_money_stocklists_landing_html — `supporting_source_only`
- [ ] v2.16C — download_recent_listings_html — `supporting_source_only`
- [ ] v2.16C — write_manifest_hashes_status_codes — `manifest_only_no_parsing`
- [x] v2.16C — do_not_read_canonical_dataset — `canonical_dataset_read=False`
- [x] v2.16C — do_not_rebuild_expanded_universe — `expanded_universe_rebuilt=False`

## Checks

- v2_16a_route_confirmation_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_provider_route_confirmation_v2_16a.json
- v2_16a_status_confirmed: PASS (critical) — TMX_PROVIDER_ROUTE_CONFIRMED_PLAN_ONLY_FULL_SOURCE_BLOCKED
- v2_16a_recommended_v2_16b: PASS (critical) — v2.16B - TMX Acquisition Plan
- provider_id_matches_v2_16a: PASS (critical) — tmx_tsx_tsxv_official_equities
- source_candidates_defined: PASS (critical) — sources=7
- primary_directory_defined: PASS (critical) — tmx_listed_company_directory
- taxonomy_policy_defined: PASS (critical) — taxonomy_rows=8
- risk_matrix_defined: PASS (critical) — risk_rows=8
- next_phase_checklist_defined: PASS (critical) — checklist_rows=9
- current_rows_unchanged: PASS (critical) — current_rows=38287
- rows_needed_unchanged: PASS (critical) — rows_needed=11713
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_network: PASS (critical) — network_download_performed=False
- no_raw_downloads: PASS (critical) — raw_files_downloaded=False
- no_parsing: PASS (critical) — parsing_performed=False
- no_normalization: PASS (critical) — normalization_performed=False
- no_net_new_filtering: PASS (critical) — net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) — expanded_universe_rebuilt=False

## Guards

- Network download performed in v2.16B: false
- Endpoint probe executed in v2.16B: false
- Raw files downloaded in v2.16B: false
- Raw files modified after write: false
- Parsing performed: false
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

TMX acquisition planning is complete.

The primary route is the official TSX/TSXV Listed Company Directory. Supporting routes include the TMX equity search controller, TSXV listed company database search, TMX Money stocklists, recent listings and monthly TMX equity financing statistics. TMX Datalinx is documented only as a paid or controlled official fallback and must not be accessed without authorization.

This phase is plan-only. It performs no network calls, no downloads, no parsing, no canonical reads, no canonical writes, no normalization, no net-new filtering and no rebuild.

## Recommended next phase

`v2.16C - TMX Raw Acquisition`
