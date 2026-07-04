# Scout Finance ? v2.2A 59k Dry Run Plan

- Phase: v2.2A
- Method: dry_run_59k_plan_v1
- Created at: 2026-07-04T23:48:17+00:00
- Plan status: **DRY_RUN_59K_PLAN_READY**
- Readiness score: **90/100**
- Dry-run folder: `outputs/large_universe_dry_run_59k`

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false

## Positives

- v2.1 closure exists and allows conditional planning.
- v2.1D allows planning a conditional 59k dry-run.

## Blockers

- No blockers detected.

## Warnings

- 59k dry-run must remain conditional until source validation and safeguards are implemented.

## Source requirements

- A real source file or dataset containing approximately 59k companies must be identified.
- The source must include at least a ticker column.
- Optional but recommended columns: company_name, exchange, sector, industry, country, market_cap.
- The source must be read-only during dry-run generation.
- The source must be validated before any batch execution.

## Safety rules

- Do not call OpenAI during v2.2 dry-run planning or first execution.
- Do not call any broker or trading API.
- Do not overwrite active MVP outputs.
- Write all 59k dry-run outputs to a separate folder.
- Keep scoring deterministic.
- Do not recalculate production scoring unless explicitly approved.
- Require a clean git checkpoint before any execution.
- Record runtime, row counts, file sizes, and errors.
- Stop immediately if memory/runtime/file-size limits are exceeded.

## Execution limits

- first_batch_limit_rows: 1000
- second_batch_limit_rows: 5000
- full_dry_run_rows: 59000
- max_single_output_file_mb_warning: 100
- max_total_output_mb_warning: 1000
- max_runtime_minutes_warning: 60

## Planned phases

- **v2.2B ? 59k Dry Run Script Skeleton**: Create a safeguarded dry-run script with no execution by default.
- **v2.2C ? 59k Source Validation**: Validate source rows, required columns and duplicate tickers.
- **v2.2D ? Small Batch Dry Run**: Run a controlled batch, initially 1k rows.
- **v2.2E ? Full Dry Run Gate**: Decide whether full 59k dry-run is allowed.
- **v2.2F ? Full 59k Dry Run**: Execute full dry-run only after explicit approval.

## Rollback plan

- Keep current tag v2.1_large_universe_mode_closed as rollback anchor.
- Create a new checkpoint tag before any full 59k dry-run.
- Never overwrite outputs/scouting or outputs/mvp during dry-run.
- If the dry-run fails, delete only outputs/large_universe_dry_run_59k.
- Return to the last clean commit if code changes are introduced.

## Recommendation

Proceed to v2.2B script skeleton. Do not execute the 59k universe yet.

Important: this plan does not execute the 59k universe.