# Scout Finance — Phase 8D Candidate Source Binding

## Objective

Bind the deterministic Phase 8C research memo modules to existing local Scout Finance candidate/ranking outputs.

This phase exists because Phase 8C validated the architecture but produced `Memos created: 0`, meaning the deterministic memo layer was not yet connected to the real TOP candidate source.

## Rules

- Do not call OpenAI.
- Do not call external APIs.
- Do not call yfinance.
- Do not recalculate the pipeline.
- Do not touch `app.py`.
- Do not touch `src/filters.py`.
- Do not touch `releases/v0.7`.
- Analyze TOP 3 by default.
- Do not invent data.
- If data is missing, keep `data_insufficient`.

## Outputs

- `outputs/scouting/phase8d_candidate_source_binding_summary.json`
- `outputs/scouting/phase8d_candidate_source_binding_report.md`
- `outputs/scouting/phase8d_candidate_source_bound_memos.json`
- `outputs/scouting/phase8d_candidate_source_bound_memos.csv`
- `outputs/scouting/phase8d_bound_top_candidates.csv`
- `outputs/scouting/phase8d_candidate_source_discovery.json`

## Next phase

8E — Persist `equity_research_memos` and prepare UI/export integration.
