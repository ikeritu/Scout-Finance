# PHASE 8H — Prompt Packaging and Dry-run AI Memo Preview

## Objective

Create AI interpretation prompt packages for the TOP 3 equity research memos without calling OpenAI or any external API.

This phase is intentionally a dry run. It prepares the exact prompt payloads that a future optional AI phase would use, but keeps the AI gate closed unless future settings explicitly allow execution.

## Inputs

Preferred source order:

1. `outputs/scouting/phase8f_research_memo_export.json`
2. `outputs/scouting/phase8e_persisted_equity_research_memos.json`
3. `outputs/scouting/phase8d_candidate_source_bound_memos.json`

The phase reads at most TOP 3 memos.

## Outputs

- `outputs/scouting/phase8h_prompt_packaging_dry_run_summary.json`
- `outputs/scouting/phase8h_prompt_packaging_dry_run_report.md`
- `outputs/scouting/phase8h_ai_prompt_packages.json`
- `outputs/scouting/phase8h_ai_prompt_packages_index.csv`
- `outputs/scouting/phase8h_prompt_packaging_dry_run_audit.json`
- `outputs/scouting/research_memo_ai_prompts/ai_prompt_package_*.json`
- `outputs/scouting/research_memo_ai_prompts/ai_prompt_package_*.md`

## Safety rules

- No OpenAI call.
- No API call.
- No yfinance call.
- No pipeline recalculation.
- No modification to `app.py`.
- No modification to `src/filters.py`.
- No modification to `releases/v0.7`.
- No invented data.
- Missing data must remain `data_insufficient`.
- Objective data and AI interpretation remain separate.

## Next

8I — Optional AI memo execution sandbox.
