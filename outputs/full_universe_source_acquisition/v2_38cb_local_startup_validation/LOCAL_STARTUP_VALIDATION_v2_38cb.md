# Local Startup Validation v2.38CB

Decision: `LOCAL_STARTUP_VALIDATED_WITH_ENVIRONMENT_WARNINGS`.

This phase validates the local startup path for Scout Finance without opening a browser or calling network APIs.

Validated:

- `app_v2_37.py` exists and parses.
- `src/ui_v2_37/global_ranking.py` exists and parses.
- `run_local_ui_v2_37.bat` points to `app_v2_37.py`, uses `streamlit run`, uses `localhost`, and checks dependencies.
- The ranking loader reads the real v2.38BV JSON and returns 1,111 rows.
- v2.38BZ and v2.38CA summaries are present and in the expected states.
- Guardrails remain closed: no scoring recomputation, no methodology/weight changes, no network, no recommendations, no broker actions.

Counts:

- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- Not yet scored: 26
- Total: 1,111

Environment warnings are allowed because this diagnostic may run outside the user's Windows setup. The next phase is `v2.38CC -- User guide / dummy-friendly guide`.
