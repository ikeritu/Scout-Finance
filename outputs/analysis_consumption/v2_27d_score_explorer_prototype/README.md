# v2.27D — Score Explorer Prototype

**Status:** `SCORE_EXPLORER_PROTOTYPE_IMPLEMENTED_FAIL_CLOSED_DIAGNOSTIC_ONLY`

A responsive static-HTML explorer is implemented with no external dependencies.

## Default behavior

With the current scoring pointer, the explorer renders a locked page:

- scoring unavailable
- no scores
- no ranking
- no signals
- catalog/watchlist fallback remains available

## Explicit diagnostic mode

The v2.25B artifact can be opened only with an acknowledgement flag and only after its SHA-256, row count and DATA_READINESS_ONLY role pass. The view shows aggregate coverage, buckets, component means, providers and countries.

It deliberately ignores `dry_run_rank` and never displays top/bottom assets. The score is a data-quality diagnostic with no attractiveness component.

```bash
python scripts/score_explorer_v2_27d.py \
  --pointer outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json \
  --output score_explorer.html

python scripts/score_explorer_v2_27d.py \
  --pointer outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json \
  --mode diagnostic \
  --scores outputs/full_universe_source_acquisition/production_scoring_dry_run_v2_scores_v2_25b.csv \
  --acknowledge-data-readiness-only \
  --output diagnostic_explorer.html
```

**Next:** v2.27E - Report Generator.
