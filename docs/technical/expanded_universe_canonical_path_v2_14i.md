# Expanded Universe Canonical Path - v2.14I

Generated at UTC: `2026-07-10T08:50:18.111883+00:00`

## Canonical current dataset

`outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`

## Why this matters

The expanded-universe path changed during the v2.x provider expansion work. Older files in `data/raw/expanded_universe/` are historical and should not be treated as the current source of truth unless a specific phase explicitly references them.

## Current source of truth

| Concept | Path |
|---|---|
| Current expanded universe | `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv` |
| Xetra expanded validation | `outputs/full_universe_source_acquisition/deutsche_boerse_xetra_expanded_validation_v2_14f.json` |
| Xetra closure report | `outputs/full_universe_source_acquisition/deutsche_boerse_xetra_closure_report_v2_14g.json` |
| Audit triage report | `outputs/audit/scout_finance_audit_triage_v2_14h.md` |
| Technical audit evidence | `outputs/audit/auditoria_tecnica_scout_finance_v1.md` |

## Current state

- Rows: `38,287`
- Threshold: `50,000`
- Completed: `76.6%`
- Pending: `23.4%`
- Rows needed: `11,713`

## Rules

- Do not use older expanded-universe CSVs as the current dataset without an explicit phase decision.
- Do not launch full 59k before source completion and explicit gate approval.
- Do not run scoring/OpenAI/broker actions from documentation phases.
