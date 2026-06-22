# Scout Finance — Phase 8D Candidate Source Binding

## Status

- Status: OK
- Base release: v0.7.0-candidate
- Default TOP N: 3
- Candidate source: D:\Proyectos\💰 Scout Finance\outputs\scouting\stage3_candidates_for_ranking.csv
- Candidate source rows: 34
- Memos created: 3

## Controls

- OpenAI called: False
- API called: False
- yfinance called: False
- Pipeline recalculated: False
- app.py modified: False
- src/filters.py modified: False
- releases/v0.7 modified: False

## Design rule

Phase 8D does not invent data. It binds deterministic Phase 8C memo modules to existing local candidate/ranking outputs only.
Missing values remain marked as `data_insufficient`.

## Top candidates bound

| Rank | Ticker | Company | Quant score | Memo status |
|---:|---|---|---:|---|
| 1 | AUPH | Aurinia Pharmaceuticals Inc - Common Shares | 70.83 | data_insufficient |
| 2 | BZ | KANZHUN LIMITED - American Depository Shares | 68.50 | data_insufficient |
| 3 | ADBE | Adobe Inc. - Common Stock | 65.97 | data_insufficient |

## Candidate discovery preview

| Discovery score | Rows | Type | File | Reason |
|---:|---:|---|---|---|
| 89 | 34 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\stage3_candidates_for_ranking.csv` | score column: score; valid ticker rows: 34; preferred filename token: ranking |
| 75 | 500 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\stage1_policy_simulation_final_current_base_alignment.csv` | valid ticker rows: 500; preferred filename token: final |
| 75 | 2000 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\stage1_policy_simulation_final_decisions.csv` | valid ticker rows: 2000; preferred filename token: final |
| 75 | 57 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\top_recoverable_candidates.csv` | valid ticker rows: 57; preferred filename token: candidate |
| 75 | 57 | csv | `D:\Proyectos\💰 Scout Finance\data\stages\stage3_rejection_log.csv` | valid ticker rows: 57; preferred filename token: stage3 |
| 60 | 182 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\fundamental_missing_by_company.csv` | valid ticker rows: 182 |
| 60 | 50 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\market_data_enrichment_success_sample.csv` | valid ticker rows: 50 |
| 60 | 50 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\real_universe_pilot_input_sample.csv` | valid ticker rows: 50 |
| 60 | 182 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\stage1_balanced_dry_run\balanced_dry_run_passed.csv` | valid ticker rows: 182 |
| 60 | 234 | csv | `D:\Proyectos\💰 Scout Finance\outputs\scouting\stage1_balanced_dry_run\balanced_dry_run_rejected.csv` | valid ticker rows: 234 |

## Next

8E — Persist equity_research_memos and prepare UI/export integration
