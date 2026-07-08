# v2.13A - Next Provider Route For Full Source 50k

Status: **NEXT_PROVIDER_ROUTE_READY**

Phase type: **route-selection-only**

Route decision: **JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE**

Selected provider: **jpx_listed_securities_csv**

Readiness score: **94/100**

Recommended next phase: **v2.13B - JPX Acquisition Plan**

Generated at UTC: `2026-07-08T13:29:08.709004+00:00`

## Current state

- Current expanded rows: 33158
- Full source threshold: 50000
- Rows needed for full source: 16842
- First expansion unlocked: true
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and gate explicitly approved
- Previous HKEX closure commit: `c904c10`

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

1. **jpx_listed_securities_csv** — SELECTED_AS_NEXT_PROVIDER_ROUTE — readiness 94/100 — expected rows 3500-5000 — overlap risk low_geographic_overlap_after_hkex_and_cboe_europe — Best next route because it is official, geographically complementary and likely lower-overlap than Xetra/Euronext after Cboe Europe.
2. **deutsche_boerse_xetra_all_tradable_instruments** — BACKUP_ROUTE_READY_HIGH_ROW_POTENTIAL — readiness 90/100 — expected rows 5000-15000 — overlap risk medium_high_due_to_existing_cboe_europe_reference_data — Strong backup if JPX acquisition is blocked or insufficient.
3. **asx_listed_companies** — BACKUP_ROUTE_READY_LOW_COMPLEXITY — readiness 88/100 — expected rows 1500-2500 — overlap risk low — Excellent backup/add-on route but smaller than JPX.
4. **tsx_tmx_listed_company_directory** — BACKUP_ROUTE_READY — readiness 84/100 — expected rows 3000-5000 — overlap risk low_medium — Good candidate but less direct than JPX/ASX.
5. **euronext_equities_live_directory** — DEFERRED_ROUTE_CANDIDATE — readiness 80/100 — expected rows 1500-8000 — overlap risk high_due_to_existing_cboe_europe_reference_data — Deferred because Cboe Europe already covers much of Europe.

## Selected route rationale

JPX is selected because it is an official exchange route, geographically complementary to the current source mix, and likely lower-overlap than Xetra or Euronext after the Cboe Europe expansion.

Xetra remains the strongest high-row backup route, but it carries higher overlap risk with Cboe Europe and includes many non-share instruments that require strict filtering.

ASX is the best low-complexity backup/add-on route, but likely too small alone to close the remaining 16,842-row gap.

## v2.13B contract preview

v2.13B must be **plan-only**.

Allowed:

- Define a controlled JPX acquisition plan.
- Define raw preservation rules for v2.13C.
- Define expected outputs for JPX CSV / data portal acquisition.
- Define validation questions for v2.13D.

Forbidden:

- No download.
- No rebuild.
- No scoring.
- No OpenAI.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.

## v2.13 validation questions

- Does JPX expose a directly downloadable listed securities CSV through the official data portal?
- Does the file contain code, company name, market segment and security/instrument classification?
- How many rows exist before filtering?
- How many rows are ordinary listed companies versus ETFs, REITs, preferred shares, funds or other instruments?
- How many candidate identifiers are net-new against expanded_universe_v2_12e?
- Can JPX rows be normalized conservatively without brittle scraping?
- Does JPX materially reduce the 16,842-row gap to 50k?
- Should JPX be source provider, candidate provider, enrichment, reference-only or deferred?

## Planned v2.13B outputs

- `scripts/jpx_acquisition_plan_v2_13b.py`
- `outputs/full_universe_source_acquisition/jpx_acquisition_plan_v2_13b.json`
- `outputs/full_universe_source_acquisition/jpx_acquisition_plan_v2_13b.md`
- `outputs/full_universe_source_acquisition/jpx_acquisition_contract_v2_13b.csv`
- `outputs/full_universe_source_acquisition/jpx_planned_outputs_v2_13b.csv`

## Project percentages

- v2.13A route: 100% completed / 0% pending after commit
- Fuente real expandida: 91% completed / 9% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 95% completed / 5% pending
