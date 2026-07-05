# Scout Finance ? v2.5A Expanded Source Revalidation Gate

- Phase: v2.5A
- Method: expanded_source_revalidation_gate_v1
- Created at: 2026-07-05T22:07:43+00:00
- Gate decision: **EXPANDED_SOURCE_REVALIDATED_PARTIAL_BELOW_TARGET**
- Readiness score: **75/100**
- Expanded source: `data/raw/expanded_universe/expanded_universe_v2_4b.csv`
- Included rows: 5648
- Issues: 0
- Duplicate exchange+ticker keys: 0
- Target first expansion rows: 15000
- Minimum full source rows: 50000

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false

## Positives

- v2.4D closure artifact found: outputs/full_universe_source_acquisition/expanded_source_partial_closure_v2_4d.json
- v2.4C validation artifact found: outputs/full_universe_source_acquisition/expanded_source_validation_real_v2_4c.json
- Expanded source CSV exists: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- v2.4D closure status accepted: EXPANDED_SOURCE_PARTIAL_CLOSED_WITH_CONDITIONS
- v2.4C validation status accepted: EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_BELOW_TARGET_WITH_WARNINGS
- Expanded source has included rows: 5648
- No structural issues detected.
- No duplicate exchange+ticker keys detected.
- No missing required canonical columns.
- Full 59k remains correctly blocked below first expansion target.

## Blockers

- No blockers detected.

## Warnings

- Expanded source below first expansion target: 5648 < 15000
- Expanded source below full-source threshold: 5648 < 50000

## Recommendation

Keep full 59k blocked. Next useful step is either add more providers or return to MVP/product work.

Important: v2.5A is a revalidation gate only. It does not execute scoring, call OpenAI, call a broker, download data, overwrite active outputs, or launch full 59k.