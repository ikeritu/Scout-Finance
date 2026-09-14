# Final Operational Publication v2.38CJ

Decision: `FINAL_OPERATIONAL_PUBLICATION_READY_WITH_DOCUMENTED_LIMITATIONS`.

Cycle status: `V2_38_LOCAL_CYCLE_CLOSED`.

Publication scope: herramienta local de investigacion (`local_research_tool_only`).

This closes the local v2.38 cycle. The final publication is operational only inside the local/repository package. It is not financial advice, does not create recommendations, does not include a broker workflow, and does not create automated trading signals.

## Frozen Operational State

- Source phase: `v2.38CI-freeze-candidate-version`
- Source status: `FREEZE_CANDIDATE_VERSION_LOCKED_WITH_DOCUMENTED_LIMITATIONS`
- Handoff checks: 34
- Checklist steps: 12
- Failures: 0
- Warnings: 0
- Blocking issues: 0
- Documented limitations preserved: 14

## Frozen Ranking Counts

- Total: 1111
- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- No adapter: 26

## Final Operator Checklist

- 01. Enter the local repository: `cd "D:\Proyectos\Scout Finance"` (Required).
- 02. Confirm the branch: `git status on phase9b-global-enrichment-v2-38b` (Required).
- 03. Install dependencies: `pip install -r requirements.txt` (Required when environment is new).
- 04. Optionally run freeze QA: `python tests/qa_freeze_candidate_version_full_suite_v2_38ci.py` (Optional verification).
- 05. Optionally run final handoff QA: `python tests/qa_final_operational_publication_v2_38cj.py` (Optional verification).
- 06. Start the local app: `run_local_ui_v2_37.bat` (Required).
- 07. Open Streamlit: `http://localhost:8501` (Required).
- 08. Open Global experimental ranking: `Use the Ranking global experimental screen` (Required).
- 09. Review limitations: `Read v2.38CG and v2.38CJ reports before interpretation` (Required).
- 10. Export CSV when needed: `Use the filtered export as a research artifact only` (Optional).
- 11. Keep scope clear: `Treat outputs as local research, not financial advice` (Required).
- 12. Do not use broker workflows: `No automated trading or broker action is part of this release` (Required).

## Guardrails

No network, no scoring recomputation, no weight changes, no ranking changes, no methodology changes, no dataset mutation, no UI changes, no broker actions and no investment recommendations are introduced by this phase.

Next decision: `POST_V2_38_DECISION`.
