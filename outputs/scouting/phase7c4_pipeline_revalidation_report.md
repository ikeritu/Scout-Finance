# Scout Finance — Phase 7C.4 Pipeline revalidation closure

Generated at: `2026-06-09T09:11:41+00:00`

## Closure status

- Status: **OK**
- Ready for next phase: **True**
- Recommended next phase: **7D — Integrate real revalidated funnel into dashboard/app**

## Active policies

| Layer | Active policy |
|---|---|
| Stage 1 | Balanced official policy |
| Stage 2 | yfinance-aligned provider-limitation policy |
| Stage 3 | Existing Stage 3 opportunity scoring policy |

## Funnel

```text
500 initial clean pilot universe
→ 182 Stage 1 PASSED
→ 63 Stage 2 PASSED
→ 6 Stage 3 PASSED
```

## Stage counts

| Stage | Passed | Watchlist | Rejected |
|---|---:|---:|---:|
| Stage 1 | 182 | 84 | 234 |
| Stage 2 | 63 | 81 | 38 |
| Stage 3 | 6 | 28 | 29 |

## Stage 3 category distribution

```json
{
  "🟡 Interesante con condiciones": 33,
  "🔴 Descartada por scoring": 29,
  "🟢 Candidata fuerte para scouting": 1
}
```

## Top company

```json
{
  "ticker": "AUPH",
  "name": "Aurinia Pharmaceuticals Inc - Common Shares",
  "final_stage3_score": 70.83,
  "stage3_category": "🟢 Candidata fuerte para scouting"
}
```

## Top candidates

- AUPH | Aurinia Pharmaceuticals Inc - Common Shares | score=70.83 | 🟢 Candidata fuerte para scouting
- BZ | KANZHUN LIMITED - American Depository Shares | score=68.5 | 🟡 Interesante con condiciones
- ADBE | Adobe Inc. - Common Stock | score=65.97 | 🟡 Interesante con condiciones
- ADEA | Adeia Inc.  - Common Stock | score=64.8 | 🟡 Interesante con condiciones
- AUGO | Aura Minerals Inc. - Common Shares | score=60.12 | 🟡 Interesante con condiciones
- ATAT | Atour Lifestyle Holdings Limited - American Depositary Shares | score=60.12 | 🟡 Interesante con condiciones
- APP | Applovin Corporation - Class A Common Stock | score=59.34 | 🟡 Interesante con condiciones
- BKNG | Booking Holdings Inc. - Common Stock | score=59.04 | 🟡 Interesante con condiciones
- AVGO | Broadcom Inc. - Common Stock | score=58.52 | 🟡 Interesante con condiciones
- ADSK | Autodesk, Inc. - Common Stock | score=58.48 | 🟡 Interesante con condiciones

## Evidence files

- stage1_summary: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage1_balanced_official_closure_summary.json`
- stage2_summary: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage2_summary.json`
- stage3_summary: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage3_summary.json`
- stage2_implementation_summary: exists=True rows=None path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage2_yfinance_policy_implementation_summary.json`
- stage1_passed: exists=True rows=182 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage1_passed.csv`
- stage1_watchlist: exists=True rows=84 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage1_watchlist.csv`
- stage1_rejected: exists=True rows=234 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage1_rejected.csv`
- stage2_passed: exists=True rows=63 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage2_passed.csv`
- stage2_watchlist: exists=True rows=81 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage2_watchlist.csv`
- stage2_rejected: exists=True rows=38 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage2_rejected.csv`
- stage3_passed: exists=True rows=6 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage3_passed.csv`
- stage3_watchlist: exists=True rows=28 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage3_watchlist.csv`
- stage3_rejected: exists=True rows=29 path=`C:\Users\ikeri\proyectos\Scout Finance\data\stages\stage3_rejected.csv`
- exports_stage3_candidates_for_ranking: exists=True rows=34 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\stage3_candidates_for_ranking.csv`
- exports_top_20_deep_research: exists=True rows=20 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\top_20_deep_research.csv`
- exports_top_50_watchlist: exists=True rows=34 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\top_50_watchlist.csv`
- exports_top_100_candidates: exists=True rows=34 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\top_100_candidates.csv`
- exports_top_recoverable_candidates: exists=True rows=57 path=`C:\Users\ikeri\proyectos\Scout Finance\outputs\scouting\top_recoverable_candidates.csv`

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- release modified: `False`

## Notes

This phase only closes the revalidation evidence. It does not modify production code, dashboard code, release files, or external-data providers.
