# Phase 9A — DataLayer and External Calls Audit

Read-only audit before v0.9 experimental AI.

## Scope

- Scan `src/` and `scripts/`.
- Detect yfinance, OpenAI, requests, urllib, httpx, pandas.read_csv, sqlite, env/API-key references.
- Inventory expected paths and scouting outputs.
- Produce recommendation for Phase 9B.

## Safety

- No OpenAI calls.
- No API calls.
- No yfinance calls.
- No pipeline recalculation.
- No app/filter/release changes.
- No v0.8 freeze changes.

## Outputs

- `outputs/scouting/phase9a_data_layer_external_calls_audit_summary.json`
- `outputs/scouting/phase9a_data_layer_external_calls_audit_report.md`
- `outputs/scouting/phase9a_data_layer_external_calls_audit.json`
- `outputs/scouting/phase9a_module_responsibility_matrix.csv`
- `outputs/scouting/phase9a_external_calls_and_data_access.csv`
- `outputs/scouting/phase9a_expected_paths_audit.csv`
- `outputs/scouting/phase9a_outputs_inventory.csv`
