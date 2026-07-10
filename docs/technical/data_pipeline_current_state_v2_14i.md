# v2.14I - Documentation and Canonical Dataset Path

Generated at UTC: `2026-07-10T08:50:18.111883+00:00`

Phase type: **documentation-only**

## Purpose

This document records the current data-pipeline state after the Deutsche Boerse Xetra closure and the audit triage gate.

It intentionally separates two project tracks:

1. **Streamlit app / MVP track**
   - Documented historical app state: `v1.1C — MVP Final Freeze`

2. **Data pipeline / expanded universe track**
   - Current data-pipeline state: `v2.14H — Audit Triage / Stability Gate`
   - Last provider closure: `v2.14G — Deutsche Boerse Xetra Closure Report`

## Current canonical dataset

- Canonical expanded universe CSV: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Validation artifact: `outputs/full_universe_source_acquisition/deutsche_boerse_xetra_expanded_validation_v2_14f.json`
- Closure artifact: `outputs/full_universe_source_acquisition/deutsche_boerse_xetra_closure_report_v2_14g.json`

## Current counts

- Expanded universe rows: `38,287`
- Minimum full-source threshold: `50,000`
- Source-to-50k completed: `76.6%`
- Source-to-50k pending: `23.4%`
- Rows still needed: `11,713`

## Gates

- Full source gate: **blocked**
- Full 59k dry-run: **blocked**
- Scoring recalculation: **not performed**
- OpenAI calls: **not performed**
- Broker calls: **not performed**

## Provider breakdown at v2.14F/v2.14G

- cboe_europe_reference_data: 21,154
- jpx_listed_securities: 3,705
- nasdaq_trader_nasdaqlisted: 3,244
- hkex_securities_list: 2,804
- nasdaq_trader_otherlisted: 2,404
- sec_company_tickers_exchange: 2,359
- deutsche_boerse_xetra_all_tradable_instruments: 1,424
- cboe_listed_symbols: 1,193

## Important note

`data/raw/expanded_universe/` contains earlier historical expanded-universe artifacts. The current canonical dataset after v2.14G is in `outputs/full_universe_source_acquisition/`.
