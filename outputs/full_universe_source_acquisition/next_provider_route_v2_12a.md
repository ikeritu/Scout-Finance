# v2.12A — Next Provider Route For Full Source 50k

Status: **NEXT_PROVIDER_ROUTE_READY**

Phase type: **route-selection-only**

Route decision: **HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE**

Selected provider: **hkex_securities_list**

Readiness score: **96/100**

Recommended next phase: **v2.12B — HKEX Acquisition Plan**

Generated at UTC: `2026-07-08T09:57:15.032225+00:00`

## Current state

- Current expanded rows: 30354
- Full source threshold: 50000
- Rows needed for full source: 19646
- First expansion unlocked: true
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and gate explicitly approved
- Previous closure commit: `4aa1928`

## Hard guards

- Network download performed: false
- Raw files downloaded: false
- Expanded universe rebuilt: false
- Normalization performed: false
- Net-new filtering performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Route candidates

1. **hkex_securities_list** — SELECTED_AS_NEXT_PROVIDER_ROUTE — readiness 96/100 — Best next route because it is official, direct-file, schema-rich and low brittleness.
2. **asx_listed_companies** — BACKUP_ROUTE_READY — readiness 92/100 — Excellent low-risk backup and possible add-on provider.
3. **tsx_tmx_listed_company_directory** — BACKUP_ROUTE_READY — readiness 86/100 — Useful later route but not the cleanest immediate direct-file target.
4. **euronext_equities_live_directory** — DEFERRED_ROUTE_CANDIDATE — readiness 82/100 — Promising but less direct than HKEX/ASX.
5. **deutsche_boerse_xetra_tradable_instruments** — DEFERRED_ROUTE_CANDIDATE — readiness 78/100 — High potential, but direct-file path needs more careful route discovery.
6. **jpx_listed_company_search** — DEFERRED_ROUTE_CANDIDATE — readiness 74/100 — Good candidate but not selected first because HKEX has a clearer direct file.

## Selected route rationale

HKEX is selected because it exposes a clear official securities list route with a direct XLSX file candidate, expected security names and ISIN coverage, and low acquisition brittleness.

ASX is the best backup route because it exposes a direct official CSV, but its expected row contribution is probably too small to materially close the 19,646-row gap by itself.

Euronext, Xetra, JPX and TMX remain valid follow-up route candidates, but require more careful discovery or are less likely to close the full gap alone.

## v2.12B contract preview

v2.12B must be **plan-only**.

Allowed:

- Define a controlled HKEX acquisition plan.
- Define raw preservation rules for v2.12C.
- Define expected outputs for XLSX acquisition.
- Define validation questions for v2.12D.

Forbidden:

- No download.
- No rebuild.
- No scoring.
- No OpenAI.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.

## v2.12 validation questions

- Does HKEX ListOfSecurities.xlsx remain directly downloadable?
- Does it contain securities name, stock code, category and ISIN?
- How many rows exist before filtering?
- How many rows are ordinary equities versus ETFs, REITs, warrants, derivatives or other instruments?
- How many candidate symbols are net-new against expanded_universe_v2_11e?
- Can HKEX rows be normalized conservatively without brittle scraping?
- Does HKEX materially reduce the 19,646-row gap to 50k?
- Should HKEX be source provider, candidate provider, enrichment, reference-only or deferred?

## Planned v2.12B outputs

- `scripts/hkex_acquisition_plan_v2_12b.py`
- `outputs/full_universe_source_acquisition/hkex_acquisition_plan_v2_12b.json`
- `outputs/full_universe_source_acquisition/hkex_acquisition_plan_v2_12b.md`
- `outputs/full_universe_source_acquisition/hkex_acquisition_contract_v2_12b.csv`
- `outputs/full_universe_source_acquisition/hkex_planned_outputs_v2_12b.csv`

## Project percentages

- v2.12A route: 100% completed / 0% pending after commit
- Fuente real expandida: 88% completed / 12% pending
- Fuente real completa 50k–59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 94% completed / 6% pending
