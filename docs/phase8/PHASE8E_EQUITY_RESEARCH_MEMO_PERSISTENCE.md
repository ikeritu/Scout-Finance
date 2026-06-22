# PHASE 8E — Equity Research Memo Persistence

## Objective

Persist the Phase 8D TOP 3 deterministic research memos into the official `equity_research_memos` SQLite table without recalculating the pipeline and without using paid or external data calls.

## Inputs

- `outputs/scouting/phase8d_candidate_source_bound_memos.json`
- `outputs/scouting/phase8d_bound_top_candidates.csv`

## Outputs

- `outputs/scouting/phase8e_equity_research_memo_persistence_summary.json`
- `outputs/scouting/phase8e_equity_research_memo_persistence_report.md`
- `outputs/scouting/phase8e_persisted_equity_research_memos.json`
- `outputs/scouting/phase8e_persisted_equity_research_memos.csv`
- `outputs/scouting/phase8e_equity_research_memo_db_audit.json`

## Database

Default database:

```text
 data/demo/demo_signals.db
```

Table:

```text
 equity_research_memos
```

## Rules

- No inventar datos.
- Missing values remain null or are represented through `data_gaps` / `data_insufficient`.
- Objective data is stored separately from AI interpretation JSON.
- AI interpretation remains disabled.
- `estimated_cost = 0.0`.
- `model_used = null`.
- TOP 3 by default.
- Do not call OpenAI.
- Do not call yfinance.
- Do not call external APIs.
- Do not modify `app.py`.
- Do not modify `src/filters.py`.
- Do not modify `releases/v0.7`.
- Do not recalculate the pipeline.

## Next

8F should decide between:

1. A readable export/report layer for the memo outputs.
2. An optional AI interpretation gate guarded by `ENABLE_OPENAI=True`.

The safer order is export/report first, then AI.
