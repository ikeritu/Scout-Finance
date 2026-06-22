# Phase 9B — Minimal DataHub and Local Source Manifest

## Objective

Create a very small DataHub layer for Scout Finance v0.9 without copying FinceptTerminal architecture.

This phase adds a local-only data access module and a manifest of local sources. It does not download data.

## Scope

- Add `src/data_hub.py`.
- Add `src/phase9b_minimal_datahub_cache.py`.
- Generate a local source manifest from:
  - `outputs/scouting/`
  - `data/stages/`
- Keep all external access disabled.

## Safety

- No OpenAI calls.
- No API calls.
- No yfinance calls.
- No pipeline recalculation.
- No app changes.
- No filter changes.
- No release changes.
- v0.8 remains untouched.

## Outputs

- `outputs/scouting/phase9b_minimal_datahub_cache_summary.json`
- `outputs/scouting/phase9b_minimal_datahub_cache_report.md`
- `outputs/scouting/phase9b_minimal_datahub_cache_audit.json`
- `outputs/scouting/phase9b_datahub_local_source_manifest.json`
- `outputs/scouting/phase9b_datahub_local_source_manifest.csv`

## Next

Phase 9C — Research Memo v2 Contract Hardening, or Phase 9D — Red Flags Detector.
