# Scout Finance ? v2.1B Generate Controlled Scale Outputs

- Phase: v2.1B
- Method: generate_controlled_scale_outputs_from_size_100_v1
- Created at: 2026-07-03T12:13:57+00:00
- Generation status: **CONTROLLED_SCALE_GENERATED_WITH_WARNINGS**
- Readiness score: **90/100**
- Source size: 100
- Target sizes: 250, 500, 1000

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false

## Blockers

- No blockers detected.

## Warnings

- Generated files are controlled structural scale outputs from size_100, not fresh real-universe data.

## Generated files

- size_250/`active_real_universe_top_candidates.csv` ? OK ? rows: 250 ? bytes: 335177
- size_250/`local_score_v0_breakdown.csv` ? OK ? rows: 250 ? bytes: 85434
- size_250/`local_score_v0_candidates.csv` ? OK ? rows: 250 ? bytes: 252044
- size_250/`ranking_explainability_candidates.csv` ? OK ? rows: 250 ? bytes: 335177
- size_250/`ranking_explainability_factors.csv` ? OK ? rows: 250 ? bytes: 107323
- size_500/`active_real_universe_top_candidates.csv` ? OK ? rows: 500 ? bytes: 669763
- size_500/`local_score_v0_breakdown.csv` ? OK ? rows: 500 ? bytes: 170868
- size_500/`local_score_v0_candidates.csv` ? OK ? rows: 500 ? bytes: 503630
- size_500/`ranking_explainability_candidates.csv` ? OK ? rows: 500 ? bytes: 669763
- size_500/`ranking_explainability_factors.csv` ? OK ? rows: 500 ? bytes: 214757
- size_1000/`active_real_universe_top_candidates.csv` ? OK ? rows: 1000 ? bytes: 1338523
- size_1000/`local_score_v0_breakdown.csv` ? OK ? rows: 1000 ? bytes: 341478
- size_1000/`local_score_v0_candidates.csv` ? OK ? rows: 1000 ? bytes: 1006390
- size_1000/`ranking_explainability_candidates.csv` ? OK ? rows: 1000 ? bytes: 1338523
- size_1000/`ranking_explainability_factors.csv` ? OK ? rows: 1000 ? bytes: 429367

## Recommendation

Re-run v2.1A readiness gate to verify the generated 250 / 500 / 1000 outputs.
Treat this as a structural/performance scale test, not as fresh real-universe research.