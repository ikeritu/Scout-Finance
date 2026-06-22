# PHASE 8I — Optional AI Execution Sandbox

## Objective

Create a controlled AI execution sandbox envelope for the TOP 3 equity research memo prompt packages.

This phase intentionally does **not** call OpenAI.

## Safety policy

- No inventar datos.
- Mark `data_insufficient` when information is missing.
- Separate objective data from AI interpretation.
- Keep `estimated_cost = 0.0`.
- Keep `model_used = null`.
- Keep TOP N capped at 3.
- Do not touch `app.py`.
- Do not touch `src/filters.py`.
- Do not touch `releases/v0.7`.
- Do not recalculate the pipeline.
- Do not call OpenAI, APIs or yfinance.

## Files

- `src/phase8i_optional_ai_execution_sandbox.py`
- `scripts/check_phase8i_optional_ai_execution_sandbox.py`

## Outputs

- `outputs/scouting/phase8i_optional_ai_execution_sandbox_summary.json`
- `outputs/scouting/phase8i_optional_ai_execution_sandbox_report.md`
- `outputs/scouting/phase8i_ai_execution_sandbox_decision.json`
- `outputs/scouting/phase8i_ai_execution_sandbox_results.json`
- `outputs/scouting/phase8i_ai_execution_sandbox_index.csv`
- `outputs/scouting/phase8i_ai_execution_sandbox_audit.json`
- `outputs/scouting/research_memo_ai_execution_sandbox/`

## Next

8J — AI memo integration readiness and final v0.8 candidate audit.
