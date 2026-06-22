# Phase 9D — Deterministic Red Flags Detector

## Objective

Add a deterministic red flags detector before adding any AI profile layer.

This phase reuses local outputs. It does not run OpenAI, APIs or yfinance.

## Adds

- `src/red_flags.py`
- `src/phase9d_red_flags_detector.py`
- `scripts/check_phase9d_red_flags_detector.py`

## Detects

- Debt warnings
- Operating margin warnings
- Free cash flow warnings
- Dilution warnings
- Data quality warnings
- Risk score warnings
- Valuation score warnings
- Growth score warnings
- Reason-token warnings from existing stage outputs

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

- `outputs/scouting/phase9d_red_flags_detector_summary.json`
- `outputs/scouting/phase9d_red_flags_detector_report.md`
- `outputs/scouting/phase9d_red_flags_detector_audit.json`
- `outputs/scouting/phase9d_red_flags_detector_export.json`
- `outputs/scouting/phase9d_red_flags_detector_index.csv`
- `outputs/scouting/red_flags/*.json`
- `outputs/scouting/red_flags/*.md`

## Next

Phase 9E — Integrate Red Flags into Research Memo v2.
