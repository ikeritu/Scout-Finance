# Streamlit Visual Smoke Test v2.38CF

Decision: `STREAMLIT_VISUAL_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATIONS`.

Validation mode: `STRUCTURAL_SMOKE_TEST`.

Screenshots available: `false`.

This phase checks whether the Streamlit app can be visually smoke-tested. In this execution environment, `streamlit` and `playwright` are not available, so the phase records an honest structural smoke test instead of claiming a browser pass.

## Covered

- App entry point exists and parses.
- Global universe module exists and parses.
- Global ranking module exists and parses.
- Navigation tokens for Inicio, Universo global and Ranking global experimental are present.
- Ranking disclaimer/no-advice language is present.
- Ranking loader data remains at 1,111 rows.
- Expected ranking populations remain 318/373/124/270/26.
- v2.38CE packaging status is present and valid.

## Not Covered Here

- Real browser screenshots.
- Real Streamlit launch on Windows.
- Pixel-level visual review.

These are deferred to an environment with Streamlit and browser tooling installed. The next phase can still proceed with the limitation documented.

## Guardrails

No network, scoring, ranking, methodology, weight, dataset, UI, recommendation, or broker changes were made.

Next recommended phase: `v2.38CG -- Limitations backlog / product risk register`.
