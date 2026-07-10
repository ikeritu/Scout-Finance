# v2.15B - Euronext Acquisition Plan

Status: **EURONEXT_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED**

Phase type: **plan-only**

Generated at UTC: `2026-07-10T21:31:53.196313+00:00`

## Selected provider

- Provider ID: `euronext_official_instruments_equities`
- Provider name: **Euronext official instruments / listed equities**
- Route phase: `v2.15A`
- Route commit: `f803505`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Official source candidates

- P1 `euronext_live_all_equities` - Euronext Live - All Equities - https://live.euronext.com/en/products/equities/list
- P2 `euronext_live_market_equity_pages` - Euronext Live market-specific equity pages - https://live.euronext.com/en/products/equities/list
- P3 `euronext_advanced_reference_data` - Euronext Advanced Reference Data - https://www.euronext.com/en/products-services/advanced-reference-data
- P4 `euronext_static_reference_data` - Euronext Static Reference Data - Equities & Bonds - https://www.euronext.com/en/products-services/static-reference-data

## Market scope

Amsterdam, Brussels, Dublin, Lisbon, Milan, Oslo, Paris

## Taxonomy rules

- `include_common_equity_like`: include - Include ordinary/common listed equities where the instrument type or market segment clearly identifies equity shares.
- `exclude_etf_etn_etc_funds_bonds_structured`: exclude - Exclude ETFs, ETNs, ETCs, funds, bonds, warrants, certificates, structured products and derivatives.
- `exclude_ambiguous_without_manual_review`: exclude_or_hold - If instrument classification is ambiguous, do not add during rebuild; route to exclusions/manual review.

## Validation plan for v2.15D

- Confirm source accessibility and official origin.
- Identify whether a public export/API exists for all equities.
- Detect pagination, markets, endpoint parameters and rate limits.
- Verify required fields: ISIN, symbol/ticker, name, market/exchange, instrument type.
- Measure gross rows and market distribution.
- Validate taxonomy filters before any rebuild phase.
- Estimate net-new overlap against expanded_universe_v2_14e only in validation phase, not in this plan phase.

## Risks and mitigations

- Risk: Euronext public list may use dynamic endpoints not visible in static HTML.
  Mitigation: v2.15C should save both HTML and discovered JS/API references for later validation.
- Risk: Reference data products may be gated/commercial.
  Mitigation: Use public Euronext Live pages first; treat reference data product pages as documentation/fallback, not guaranteed input.
- Risk: Overlap with Cboe Europe and Xetra may be significant.
  Mitigation: v2.15D must perform ISIN and exchange+ticker overlap checks before rebuild.
- Risk: Non-equity instruments may be mixed into source lists.
  Mitigation: Strict taxonomy: exclude ETF, ETN, ETC, funds, bonds, structured products and derivatives.

## Expected outputs in v2.15C

- Raw official pages or endpoint payloads.
- Source discovery manifest.
- Download manifest with status codes and checksums.
- Candidate files stored without parsing decisions.

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.15C - Euronext Raw Acquisition`

## Important note

This phase creates the acquisition plan only. It does not download, parse, normalize, rebuild, score, call OpenAI, call brokers or launch full 59k.
