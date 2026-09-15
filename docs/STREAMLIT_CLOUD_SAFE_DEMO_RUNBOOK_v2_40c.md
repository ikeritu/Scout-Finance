# Streamlit Cloud Safe Demo Runbook v2.40C

This runbook is preparation only. Do not create or share a public URL until `v2.40D-controlled-external-publication-qa` passes.

## Required Setting

Set this only in Streamlit Cloud secrets or environment settings when preparing the controlled demo:

```toml
SCOUT_FINANCE_SAFE_DEMO_MODE = "1"
```

Do not add real provider credentials. The demo requires no secrets and no external network providers.

## Manual Checks Before Any URL Is Shared

1. The sidebar shows `Modo demo seguro`.
2. The global universe refresh button is disabled.
3. Watchlists are blocked.
4. Ranking copy says experimental research and no financial advice.
5. No broker or trading action is available.
6. `v2.40D` QA has passed.
