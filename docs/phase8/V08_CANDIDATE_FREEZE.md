# Scout Finance v0.8.0-candidate Freeze

## Objective

Create the v0.8.0-candidate release freeze package after Phase 8J validates readiness.

## Scope

v0.8.0-candidate is:

- Quantitative ranking
- Deterministic equity research memo layer
- Memo persistence
- Markdown/JSON/CSV export
- AI gate and cost guardrails
- Prompt packaging dry-run
- Optional AI execution sandbox
- Real AI calls disabled by default

## Safety position

- No OpenAI calls
- No API calls
- No yfinance calls
- No pipeline recalculation
- No `app.py` changes
- No `src/filters.py` changes
- No `releases/v0.7` modification
- TOP 3 by default
- No inventar datos
- Use `data_insufficient` when needed
- Not financial advice

## Files

- `src/freeze_v08_candidate.py`
- `scripts/check_v08_candidate_freeze.py`

## Outputs

- `releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip`
- `releases/RELEASE_LOCK_v0.8.json`
- `releases/FREEZE_REPORT_v0.8.md`
- `releases/MANIFEST_v0.8.0_candidate.json`
