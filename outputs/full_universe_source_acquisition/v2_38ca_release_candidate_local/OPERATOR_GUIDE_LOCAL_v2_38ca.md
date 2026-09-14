# Operator Guide Local v2.38CA

Scout Finance is ready as a local release candidate with limitations: `RELEASE_CANDIDATE_LOCAL_READY_WITH_LIMITATIONS`.

## Start On Windows

1. Open PowerShell.
2. Go to the project folder:

```powershell
cd "D:\Proyectos\💰 Scout Finance"
```

3. Install dependencies if needed:

```powershell
python -m pip install -r requirements.txt
```

4. Start the local app:

```powershell
.\run_local_ui_v2_37.bat
```

5. Open `http://localhost:8501` if the browser does not open automatically.

## First Screens To Review

- `Inicio`: confirms local product status and general data mode.
- `Universo global (43.089)`: shows global coverage and missing data explicitly.
- `Ranking global (experimental)`: shows the real v2.38BV ranking surface hardened in v2.38BY.

## Required Outputs

- v2.38BV ranking results.
- v2.38BX closure audit summary and manifest.
- v2.38BY UX hardening summary, manifest, and checks.
- v2.38BZ product readiness summary, manifest, and checks.
- v2.38CA release candidate checklist, summary, guide, and manifest.

If a required output is missing, run the corresponding phase builder or stop and inspect the missing artifact. Do not replace a missing real output with a fabricated placeholder.

## State Meanings

- `ELIGIBLE_PARTIAL`: main experimental ranking population.
- `PARTIAL_COMPARABILITY`: scored, but separated because comparability is lower.
- `REVIEW_REQUIRED`: never scored automatically; needs human or separate contract review.
- `BLOCKED`: coverage below the contractual floor.
- `NOT_YET_SCORED_NO_ADAPTER`: eligible in principle, but missing a real adapter.

## Limits That Still Matter

The ranking is for local research triage only. It is not financial advice, not a predictive product, not a price target workflow, not a buy/sell/hold signal, and not connected to any broker. Some countries, prices, adapters, financial institutions, and low-coverage assets remain explicitly limited.
