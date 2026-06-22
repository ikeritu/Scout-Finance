# Scout Finance — Phase 8C Deterministic Research Modules

Status: **OK**

## Scope

Phase 8C creates the offline deterministic module layer required before AI Equity Research Memos.

It does **not** call OpenAI, APIs, yfinance or the pipeline. It reads existing Scout Finance outputs only.

## Controls

| Control | Value |
|---|---:|
| OpenAI called | False |
| API called | False |
| yfinance called | False |
| app.py modified | False |
| src/filters.py modified | False |
| v0.7 release modified | False |
| Pipeline recalculated | False |

## Candidate source

- Source file: `None`
- Rows available: `0`
- Default TOP N: `3`
- Memos created: `0`

## Deterministic memo summary

| Rank | Ticker | Company | Quant score | Deterministic score | Status | Verdict | Confidence | Data gaps |
|---:|---|---|---:|---:|---|---|---|---:|
| - | - | - | - | - | data_insufficient | no_candidates_found | low | - |

## Modules

- `src/research_memo.py`
- `src/fundamentals.py`
- `src/valuation.py`
- `src/risk_analysis.py`
- `src/moat_analysis.py`
- `src/growth_analysis.py`
- `src/institutional_view.py`
- `src/earnings_analysis.py`

## Design rules enforced

- No inventar datos.
- Missing fields are marked as `data_insufficient`.
- Objective data, deterministic interpretation and future AI interpretation are separated.
- `estimated_cost = 0.0`.
- `model_used = null`.
- TOP 3 default to control later AI costs.
- 8C remains compatible with the 8B memo schema.

## Next

8D — Memo persistence and integration adapter.

Recommended next scope:
- create/upgrade `equity_research_memos` table without touching v0.7 release
- persist deterministic memos
- keep Streamlit/app integration for later
