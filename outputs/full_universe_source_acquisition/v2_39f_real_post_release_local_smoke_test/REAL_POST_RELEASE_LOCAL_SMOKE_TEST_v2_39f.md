# Real Post-Release Local Smoke Test v2.39F

Decision: `REAL_POST_RELEASE_LOCAL_SMOKE_TEST_READY`.

This phase runs the reproducible offline portion of the post-release local smoke test and leaves real Windows/Streamlit/browser checks as explicit manual validation.

## Results

- Checks total: 28
- PASS: 17
- WARN: 11
- BLOCKER: 0
- Compile failures: 0
- Ranking loader: `PASS`
- Ranking total: 1111
- Ranking populations: 318/373/124/270/26
- Launcher: `PASS`
- Streamlit environment: `STREAMLIT_NOT_AVAILABLE_IN_BUILDER_ENV`
- Browser validation: `MANUAL_REQUIRED`

Warnings are documented for Streamlit/browser checks that require a real local runtime. No network, dependency installation, scoring, ranking rebuild, dataset mutation, UI change, broker action, tag creation, asset upload or GitHub Release was performed.

Next recommended phase: `v2.40A-publication-decision`.
