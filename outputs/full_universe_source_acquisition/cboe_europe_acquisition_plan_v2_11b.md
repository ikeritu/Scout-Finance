# v2.11B — Cboe Europe Acquisition Plan

Status: **CBOE_EUROPE_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Readiness score: **94/100**

Decision: **PROCEED_TO_V2_11C_ACQUISITION_ONLY_AFTER_V2_11B_VALIDATION_AND_COMMIT**

Generated at UTC: `2026-07-07T22:40:12.626588+00:00`

## Confirmed previous phase

- v2.11A commit: `581fff8`
- v2.11A status: `CBOE_EUROPE_ROUTE_READY`
- v2.11A pushed to origin/main: yes

## Hard guards

- Network download performed: false
- Raw files downloaded: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false
- Rebuild allowed: false

## Current source context

- Current expanded rows: 9,200
- Rows needed for first expansion: 5,800
- Rows needed for full source: 40,800
- First expansion threshold: 15,000
- Full source threshold: 50,000
- Full 59k status: blocked until source complete and gate approved

## v2.11C controlled acquisition contract

v2.11C must be **acquisition-only**.

Allowed:

- Download Cboe Europe Reference Data page as raw HTML.
- Discover official Live Symbols CSV links from the Reference Data page.
- Discover official Live Symbols Enhanced CSV links from the Reference Data page.
- Download discovered official CSV files as raw files.
- Download CXE/BXE/DXE/TRF symbols_traded pages as fallback raw HTML.
- Record URL, status code, content type, byte size, SHA256 and fetch timestamp.
- Preserve raw files exactly as received.

Forbidden:

- No rebuild.
- No scoring.
- No OpenAI calls.
- No broker/API trading calls.
- No full 59k launch.
- No normalization.
- No net-new filtering.
- No brittle scraping.
- No issuer inference.
- No primary-exchange assumptions.
- No overwrite of active outputs.

## Cboe Europe route families

1. `cboe_europe_reference_data_page`
2. `live_symbols_csv`
3. `live_symbols_enhanced_csv`
4. `symbols_traded_cxe`
5. `symbols_traded_bxe`
6. `symbols_traded_dxe`
7. `symbols_traded_trf`
8. `BXE/CXE/DXE/TRF/SIS MIC and venue semantics caution`

## MIC / venue caution

BXE, CXE, DXE, TRF and SIS must be treated cautiously.

v2.11C may preserve the source fields, but must not decide whether those values represent:

- primary exchange,
- execution venue,
- reporting venue,
- book,
- MIC,
- market segment,
- listing market.

That decision belongs to v2.11D validation.

## Handoff questions for v2.11D

- Does Cboe Europe expose stable official Live Symbols CSV files?
- Are CSV files available for BXE, CXE, DXE, TRF EU, TRF UK and/or SIS?
- Does enhanced CSV contain richer symbol/name/MIC/country/currency fields?
- How many rows exist before net-new filtering?
- How many MIC+ticker, venue+ticker, ISIN and exchange+ticker candidates are net-new against expanded_universe_v2_8e?
- Are rows ordinary shares, ETFs, funds, ETCs or mixed instruments?
- Can Cboe Europe rows be normalized conservatively without brittle scraping?
- Does Cboe Europe unlock the 15000-row first expansion threshold?
- Should Cboe Europe be source provider, candidate provider, enrichment, reference-only or deferred?

## Planned v2.11C outputs

- `scripts/cboe_europe_acquisition_v2_11c.py`
- `outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/`
- `outputs/full_universe_source_acquisition/cboe_europe_download_manifest_v2_11c.json`
- `outputs/full_universe_source_acquisition/cboe_europe_download_manifest_v2_11c.csv`
- `outputs/full_universe_source_acquisition/cboe_europe_discovered_links_v2_11c.csv`
- `outputs/full_universe_source_acquisition/cboe_europe_acquisition_report_v2_11c.md`

## v2.11B conclusion

Cboe Europe acquisition is ready to move to v2.11C only after this plan is validated and committed.

No source acquisition has been performed in v2.11B.
