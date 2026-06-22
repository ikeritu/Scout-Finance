# PHASE 8J — AI Memo Integration Readiness and v0.8 Candidate Audit

## Objective

Audit the complete Phase 8 chain from 8A to 8I and decide whether Scout Finance can move to a v0.8 release candidate.

## Scope

This phase consolidates:

- 8A Dashboard final design
- 8B AI Equity Research Memo Blueprint
- 8C Deterministic research modules
- 8D Candidate source binding
- 8E Memo persistence
- 8F Memo export/report layer
- 8G Optional AI gate and cost guardrails
- 8H Prompt packaging dry-run
- 8I Optional AI execution sandbox

## Hard rules

- Do not call OpenAI.
- Do not call APIs.
- Do not call yfinance.
- Do not recalculate the pipeline.
- Do not touch `app.py`.
- Do not touch `src/filters.py`.
- Do not touch `releases/v0.7`.
- Keep TOP N capped at 3.
- Keep real AI calls disabled by default.
- No inventar datos.
- Use `data_insufficient` when data is missing.

## Outputs

- `outputs/scouting/phase8j_v08_candidate_audit_summary.json`
- `outputs/scouting/phase8j_v08_candidate_audit_report.md`
- `outputs/scouting/phase8j_v08_candidate_audit.json`
- `outputs/scouting/phase8j_v08_candidate_readiness_decision.json`
- `outputs/scouting/phase8j_phase_status_matrix.csv`
- `outputs/scouting/phase8j_key_outputs_manifest.csv`

## Recommended next step

If valid, create the v0.8 release candidate freeze package.
