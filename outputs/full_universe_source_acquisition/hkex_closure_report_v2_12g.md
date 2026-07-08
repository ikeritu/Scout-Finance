# v2.12G - HKEX Closure Report

Status: **HKEX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED**

Phase type: **closure-only**

Source decision: **HKEX_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**

Generated at UTC: `2026-07-08T12:28:47.628499+00:00`

## Phase chain

- v2.12A - Next Provider Route - commit `9856571`
- v2.12B - HKEX Acquisition Plan - commit `abbbc0f`
- v2.12C - HKEX Acquisition Real - commit `cd277d4`
- v2.12D - HKEX Validation - commit `5bf9ada`
- v2.12E - Rebuild Expanded Source With HKEX - commit `dc58678`
- v2.12F - Validate Expanded Source With HKEX - commit `3f8872e`

## Final HKEX decision

HKEX is accepted as a conservative expanded-source provider.

Only allowed HKEX equity categories were added.

Non-equity, derivative, debt, ETF, REIT, warrant, CBBC and review-required rows were excluded.

## Counts

- Baseline rows before HKEX: 30354
- HKEX candidate rows reviewed: 17589
- HKEX rows added: 2804
- HKEX exclusions: 14785
- Current expanded rows: 33158
- Duplicate exchange+ticker keys: 0
- First expansion threshold: 15000
- First expansion unlocked: True
- Full source threshold: 50000
- Full source unlocked: False
- Rows needed full source: 16842
- Critical failed checks: 0
- Warning failed checks: 0
- Full 59k universe launched: false

## Accepted HKEX breakdown

- Equity / Equity Securities (Main Board): 2467
- Equity / Equity Securities (GEM): 309
- Equity / Investment Companies: 22
- Equity / Trading Only Securities: 6

## Exclusion breakdown

- NON_EQUITY_CATEGORY_EXCLUDED: 14783
- EQUITY_SUBCATEGORY_NOT_IN_ALLOWLIST: 2

## Provider breakdown after HKEX

- cboe_europe_reference_data: 21154
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## Hard guards

- phase_type: closure-only
- network_download_performed_in_closure: False
- raw_files_modified: False
- normalization_performed_in_closure: False
- net_new_filtering_performed_in_closure: False
- expanded_universe_rebuilt_in_closure: False
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Roadmap status

- [done] v2.12A - Next Provider Route For Full Source 50k - 100% completed / 0% pending
- [done] v2.12B - HKEX Acquisition Plan - 100% completed / 0% pending
- [done] v2.12C - HKEX Acquisition Real - 100% completed / 0% pending
- [done] v2.12D - HKEX Validation - 100% completed / 0% pending
- [done] v2.12E - Rebuild Expanded Source With HKEX - 100% completed / 0% pending
- [done] v2.12F - Validate Expanded Source With HKEX - 100% completed / 0% pending
- [in_progress_until_commit] v2.12G - HKEX Closure Report - 90% completed / 10% pending
- [next] v2.13A - Next Provider Route For Full Source 50k - 0% completed / 100% pending
- [blocked] Full 59k dry-run real - Blocked until source >=50k and explicit gate approval - 0% completed / 100% pending

## Project percentages

- v2.12 HKEX: 100% completed / 0% pending after commit
- Fuente real expandida: 91% completed / 9% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 95% completed / 5% pending

## Recommended next phase

**v2.13A_NEXT_PROVIDER_ROUTE_FOR_FULL_SOURCE_50K**

Reason: expanded source is now 33158 rows, but the 50k source-complete gate is still blocked. Remaining gap: 16842 rows.

## Scope note

v2.12G is closure-only.

It does not download, modify raw files, normalize, filter net-new rows, rebuild, score, call OpenAI, call broker APIs, or launch full 59k.
