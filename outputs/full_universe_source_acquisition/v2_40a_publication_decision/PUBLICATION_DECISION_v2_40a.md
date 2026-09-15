# Publication Decision v2.40A

Decision: `PUBLIC_DEMO_SAFE_MODE_REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT`.

The full real Scout Finance app and ranking should not be deployed publicly yet. The selected path requires a safe public demo mode before any controlled external deployment.

## Policy Gates

- `v2.40B`: allowed only as technical hosting preparation.
- `v2.40C`: required before any public demo.
- `v2.40D`: blocked until both `v2.40B` and `v2.40C` pass.

## Rationale

Scout Finance remains a local research tool with an experimental ranking, known coverage gaps, security warnings, manual Streamlit/browser validation and strict no-advice/no-broker guardrails.

No deployment, release, asset upload, tag, credential preparation, network call, scoring, ranking rebuild, dataset mutation or functional UI change was performed.

Next recommended phase: `v2.40B-streamlit-cloud-hosting-prep`.
