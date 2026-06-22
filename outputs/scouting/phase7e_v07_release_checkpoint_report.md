# Scout Finance — Phase 7E.1 v0.7 release checkpoint marker fix

Generated at: `2026-06-10T09:38:57+00:00`

## Status

- Checkpoint status: **OK**
- Ready for v0.7 release packaging: **True**
- Recommended next phase: **7F — Package release v0.7 candidate**

## Why 7E.1 exists

The first 7E checkpoint incorrectly required the obsolete original 7D marker:

```text
# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED
```

That marker was removed on purpose by 7D.1 because the original block was inserted before its helper function. The correct safe dashboard marker is:

```text
# PHASE 7D.1 DASHBOARD HOTFIX APPLIED
```

## Current validated funnel

```text
500 → 182 → 63 → 6
```

## Counts

| Item | Count |
|---|---:|
| Stage 1 passed | 182 |
| Stage 2 passed | 63 |
| Stage 3 passed | 6 |
| Top 100 candidates rows | 34 |
| Candidates for ranking rows | 34 |

## Required dashboard checks

- `# PHASE 7D.1 DASHBOARD HOTFIX APPLIED`: True
- `# PHASE 7D.2 INSTITUTIONAL COUNT HOTFIX APPLIED`: True
- `# PHASE 7D.3B FUNDAMENTAL COVERAGE EXACT FIX APPLIED`: True
- `Funnel real revalidado`: True
- `500 → 182 → 63 → 6`: True
- `fundamentals_yfinance_enrichment_summary.json`: True
- `summary["runner_phase"] = "7C.1"`: True

## Optional legacy checks

- `# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED`: False

## Evidence files

- stage1_balanced_closure: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage1_balanced_official_closure_summary.json`
- stage2_yfinance_policy: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage2_yfinance_policy_implementation_summary.json`
- phase7c4_pipeline_closure: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7c4_pipeline_revalidation_summary.json`
- phase7d_dashboard: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7d_dashboard_revalidated_funnel_summary.json`
- phase7d1_hotfix: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7d1_dashboard_hotfix_summary.json`
- phase7d2_count_hotfix: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7d2_institutional_count_hotfix_summary.json`
- phase7d3b_fundamental_exact_fix: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7d3b_fundamental_coverage_exact_fix_summary.json`
- active_pipeline_policy_status: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\active_pipeline_policy_status.json`
- stage3_summary: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage3_summary.json`
- stage1_passed: exists=True rows=182 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage1_passed.csv`
- stage2_passed: exists=True rows=63 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage2_passed.csv`
- stage3_passed: exists=True rows=6 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage3_passed.csv`
- top_100_candidates: exists=True rows=34 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\top_100_candidates.csv`
- stage3_candidates_for_ranking: exists=True rows=34 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage3_candidates_for_ranking.csv`
- phase7c4_top_candidates: exists=True rows=20 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\phase7c4_pipeline_revalidation_top_candidates.csv`

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release modified: `False`

## Release note draft

```text
v0.7 candidate: real pilot funnel validated and dashboard-integrated.
Pipeline: institutional universe → Stage 1 Balanced → Stage 2 yfinance-aligned → Stage 3 scoring.
Validated funnel: 500 → 182 → 63 → 6.
Top candidate: AUPH — Aurinia Pharmaceuticals Inc - Common Shares — score 70.83.
```
