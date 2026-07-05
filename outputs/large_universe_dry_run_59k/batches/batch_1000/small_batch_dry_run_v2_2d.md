# Scout Finance ? v2.2D Small Batch Dry Run

- Phase: v2.2D
- Method: small_batch_dry_run_v1
- Created at: 2026-07-05T00:58:39+00:00
- Dry-run status: **SMALL_BATCH_DRY_RUN_COMPLETED_WITH_WARNINGS**
- Readiness score: **85/100**
- Elapsed seconds: 0.3527

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false

## Source

- path: data/raw/universe_source_real_clean.csv
- rows: 5617
- columns: 14
- validation_status: SOURCE_VALID_FOR_SMALL_BATCH_WITH_WARNINGS
- validation_scope: PARTIAL_REAL_SOURCE_FOR_SMALL_BATCH

## Batch

- requested_limit: 1000
- written_rows: 1000
- output_dir: outputs/large_universe_dry_run_59k/batches/batch_1000
- batch_csv: outputs/large_universe_dry_run_59k/batches/batch_1000/small_batch_universe_v2_2d.csv
- output_size_bytes: 194860

## Dry-run actions

- source_validation_used: True
- batch_csv_written: True
- batch_execution_performed: True
- scoring_performed: False
- openai_called: False
- broker_called: False
- active_outputs_overwritten: False
- full_59000_universe_launched: False

## Positives

- Output directory is isolated: outputs/large_universe_dry_run_59k/batches/batch_1000
- v2.2C source validation allows small batch with warnings.
- Source CSV readable: data/raw/universe_source_real_clean.csv
- Required mapped ticker column exists: Symbol -> ticker
- Small batch CSV written with 1000 rows.

## Blockers

- No blockers detected.

## Warnings

- Source is partial real source, not full 59k.

## Recommendation

Proceed to v2.2E full dry-run gate. Do not execute full 59k.

Important: v2.2D writes only an isolated source-normalized batch CSV. It does not run scoring, OpenAI, broker calls, or full 59k.