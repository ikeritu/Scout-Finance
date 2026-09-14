# Release Candidate Local v2.38CA

Decision: `RELEASE_CANDIDATE_LOCAL_READY_WITH_LIMITATIONS`.

Scout Finance is prepared as a local release candidate for research use with limitations. This phase adds an operator guide and a reproducible local readiness checklist. It does not recompute scores, alter methodology, change weights, call network APIs, create advice, create recommendations, or connect broker workflows.

Verified populations:

- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- Not yet scored: 26
- Total: 1,111

Startup path:

- Install dependencies with `python -m pip install -r requirements.txt`.
- Launch with `run_local_ui_v2_37.bat`.
- Review `Ranking global (experimental)` as a research-only surface.

Readiness result: local candidate ready with explicit limitations. Next recommended phase: `v2.38CB -- Local startup/dependency validation`.
