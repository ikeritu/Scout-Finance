# Scout Finance — Phase 7F.1 release v0.7 integrity validation

Generated at: `2026-06-10T11:39:32+00:00`

## Status

- Integrity status: **OK**
- Release freeze approved: **True**
- Release directory: `C:\Users\ikeri\proyectos\Scout Finance\releases\v0.7`

## Validated funnel

```text
500 → 182 → 63 → 6
```

## Core counts

| Item | Count |
|---|---:|
| Stage 1 passed | 182 |
| Stage 2 passed | 63 |
| Stage 3 passed | 6 |
| Stage 3 candidates for ranking | 34 |

## Required artifacts

- `VERSION`: True
- `CHANGELOG_v0.7.md`: True
- `RELEASE_NOTES_v0.7.md`: True
- `manifest_v0.7.json`: True
- `app.py`: True
- `src`: True
- `scripts`: True
- `docs/phase7`: True
- `outputs/scouting/phase7e_v07_release_checkpoint_summary.json`: True
- `outputs/scouting/phase7f_release_v07_packaging_summary.json`: True
- `outputs/scouting/phase7c4_pipeline_revalidation_summary.json`: True
- `outputs/scouting/active_pipeline_policy_status.json`: True
- `outputs/scouting/stage3_summary.json`: True
- `outputs/scouting/stage3_candidates_for_ranking.csv`: True
- `outputs/scouting/top_100_candidates.csv`: True
- `outputs/scouting/fundamentals_yfinance_enrichment_summary.json`: True
- `data/stages/stage1_passed.csv`: True
- `data/stages/stage2_passed.csv`: True
- `data/stages/stage3_passed.csv`: True
- `data/stages/stage3_rejection_log.csv`: True

## Checks

- release_dir_exists: True
- release_app_compiles: True
- required_artifacts_ok: True
- required_texts_ok: True
- counts_ok: True
- manifest_exists: True
- manifest_release_ok: True
- manifest_funnel_ok: True
- manifest_files_exist_on_disk: True

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release modified: `False`

## Final statement

```text
Scout Finance v0.7.0-candidate is integrity-validated and ready to freeze.
```
