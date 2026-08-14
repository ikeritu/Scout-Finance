# Scout Finance — v2.24D Provider Quality Matrix

**Status:** `PROVIDER_QUALITY_MATRIX_COMPLETED_NO_DATASET_MODIFICATION`

## 1. Scope and immutable baseline

This phase converts the verified v2.23B metadata-coverage evidence plus the v2.24B/v2.24C planning rules into a provider-level quality and execution matrix. It is an audit/planning phase only: no metadata is backfilled, no taxonomy is normalized in the canonical dataset, and no scoring is executed.

Canonical baseline:

- Dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_21h_activated_operational_reference.csv`
- Rows: **43,089**
- SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- Provider buckets in current operational evidence: **14**
- Six-field metadata cells audited: `country`, `mic`, `currency`, `asset_type`, `instrument_type`, `instrument_scope`
- Total missing cells across those six fields: **160,009**

The 14 provider buckets sum exactly to 43,089 rows; there is no unexplained row residual in this matrix.

## 2. Transparent completeness metrics

The inherited v2.23B `priority_score` is retained as historical evidence but is not reinterpreted as a universal sum because its construction is not equivalent across every provider/gap pattern.

v2.24D therefore uses separate transparent metrics:

- `geo_completeness_pct = 100 * (3*rows - country_missing - mic_missing - currency_missing) / (3*rows)`
- `taxonomy_completeness_pct = 100 * (3*rows - asset_type_missing - instrument_type_missing - instrument_scope_missing) / (3*rows)`
- `overall_six_field_completeness_pct = 100 * (6*rows - all_six_missing_cells) / (6*rows)`
- `missing_burden_share_pct = provider_missing_cells / 160009 * 100`

Quality tiers are governance labels, not statistical claims:

- `CONTROL`: 100% six-field completeness
- `HIGH`: >=80% and <100%
- `MEDIUM`: >=60% and <80%
- `LOW`: >=40% and <60%
- `CRITICAL`: <40%

A missing `source_provider` is a provenance override: the `__MISSING_PROVIDER__` bucket remains on `PROVENANCE_HOLD` regardless of its numerical completeness.

## 3. Provider quality matrix

| Provider | Rows | Geo complete | Taxonomy complete | Overall complete | Missing cells | Missing burden | Quality tier | v2.24E route |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `cboe_europe_reference_data` | 21,154 | 0.00% | 33.33% | 16.67% | 105,770 | 66.10% | CRITICAL | `PARTIAL_DETERMINISTIC_ONLY` |
| `nasdaq_trader_nasdaqlisted` | 3,244 | 33.33% | 66.67% | 50.00% | 9,732 | 6.08% | LOW | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `hkex_securities_list` | 2,804 | 100.00% | 0.00% | 50.00% | 8,412 | 5.26% | LOW | `REVIEW_REQUIRED` |
| `jpx_listed_securities` | 3,705 | 100.00% | 33.33% | 66.67% | 7,410 | 4.63% | MEDIUM | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `nasdaq_trader_otherlisted` | 2,404 | 33.33% | 66.67% | 50.00% | 7,212 | 4.51% | LOW | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `sec_company_tickers_exchange` | 2,359 | 33.33% | 66.67% | 50.00% | 7,077 | 4.42% | LOW | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `__MISSING_PROVIDER__` | 2,013 | 66.67% | 33.33% | 50.00% | 6,039 | 3.77% | LOW / PROVENANCE_HOLD | `REVIEW_REQUIRED` |
| `cboe_listed_symbols` | 1,193 | 33.33% | 66.67% | 50.00% | 3,579 | 2.24% | LOW | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `deutsche_boerse_xetra_all_tradable_instruments` | 1,424 | 66.67% | 66.67% | 66.67% | 2,848 | 1.78% | MEDIUM | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `HKEX` | 396 | 100.00% | 0.00% | 50.00% | 1,188 | 0.74% | LOW | `REVIEW_REQUIRED` |
| `TWSE` | 696 | 100.00% | 66.67% | 83.33% | 696 | 0.43% | HIGH | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `SFC_SIMEV_RNVE` | 23 | 100.00% | 33.33% | 66.67% | 46 | 0.03% | MEDIUM | `DETERMINISTIC_MAPPING_CANDIDATE` |
| `ASX` | 1,316 | 100.00% | 100.00% | 100.00% | 0 | 0.00% | CONTROL | `CONTROL_POPULATION` |
| `sgx_structured_endpoint` | 358 | 100.00% | 100.00% | 100.00% | 0 | 0.00% | CONTROL | `CONTROL_POPULATION` |

## 4. Execution-policy classes

### CONTROL_POPULATION

`ASX` and `sgx_structured_endpoint` have complete coverage in all six audited fields. v2.24E must not attempt to improve them. They are control populations for asserting that dry-run logic leaves already-complete provider metadata unchanged.

### DETERMINISTIC_MAPPING_CANDIDATE

`nasdaq_trader_nasdaqlisted`, `nasdaq_trader_otherlisted`, `sec_company_tickers_exchange`, `jpx_listed_securities`, `cboe_listed_symbols`, `deutsche_boerse_xetra_all_tradable_instruments`, `TWSE`, and `SFC_SIMEV_RNVE` have populated anchors that can support provider-specific deterministic rules designed in v2.24B/v2.24C.

Candidate status is not blanket authorization. A field may be filled in v2.24E only when an approved mapping registry resolves it deterministically and provenance is recorded.

### PARTIAL_DETERMINISTIC_ONLY

`cboe_europe_reference_data` dominates the remediation burden: **105,770 / 160,009 = 66.10%** of all missing six-field cells. It has zero completeness across country/MIC/currency and only one of three taxonomy fields populated. However, its `instrument_type` can still provide deterministic cases such as explicit ETF classifications.

Broad values such as `EQTY` are not sufficient by themselves to declare `common_equity`, because prior project evidence contains fund-like instruments represented under broad equity-like provider labels. Ambiguous rows remain unresolved.

### REVIEW_REQUIRED

- `hkex_securities_list`: geography is complete but all three taxonomy fields are missing.
- `HKEX`: same taxonomy failure pattern on the smaller legacy/provider bucket.
- `__MISSING_PROVIDER__`: source provenance itself is absent on 2,013 rows, so provider-specific auto-rules are prohibited until provenance is deterministically restored or another authoritative row-level anchor exists.

Names/tickers alone are not sufficient to leave this class.

## 5. Remediation lanes for v2.24E

### Lane A — deterministic dry-run candidates

Apply only approved registry rules, ordered by missing-cell burden:

1. `cboe_europe_reference_data` — partial deterministic rules only; unresolved rows expected.
2. `nasdaq_trader_nasdaqlisted`.
3. `jpx_listed_securities`.
4. `nasdaq_trader_otherlisted`.
5. `sec_company_tickers_exchange`.
6. `cboe_listed_symbols`.
7. `deutsche_boerse_xetra_all_tradable_instruments`.
8. `TWSE`.
9. `SFC_SIMEV_RNVE`.

### Lane B — review/hold

No automatic fill without newly approved deterministic evidence:

- `hkex_securities_list`
- `HKEX`
- `__MISSING_PROVIDER__`

### Lane C — controls

- `ASX`
- `sgx_structured_endpoint`

Expected dry-run changes for Lane C: **zero**.

## 6. Provider-level v2.24E acceptance gates

For every provider bucket, v2.24E must report:

- row count before and after;
- six-field completeness before and after;
- missing cells before and after;
- filled cells by target field and `rule_id`;
- unresolved rows and reasons;
- conflict rows and reasons;
- overwrite attempts, expected **0**;
- provenance coverage for derived values, expected **100%**;
- control-population changed rows, expected **0**;
- provider-bucket row totals summing to **43,089**.

Global gates remain:

- canonical dataset SHA unchanged during the dry run;
- operational pointer unchanged;
- no row deletion/addition;
- no scoring execution or promotion;
- no OpenAI/broker enrichment;
- no `full59k` launch.

Coverage gain is informative but cannot compensate for ambiguous or untraceable values.

## 7. Decisions

- `V2_24D_001`: approve six-field completeness as the transparent cross-provider comparison metric.
- `V2_24D_002`: retain inherited v2.23B priority evidence without redefining its semantics.
- `V2_24D_003`: separate numerical completeness from automation permission; low completeness does not authorize guessing.
- `V2_24D_004`: classify ASX and SGX as dry-run control populations.
- `V2_24D_005`: classify CBOE Europe as the dominant remediation target but allow only partial deterministic normalization/backfill.
- `V2_24D_006`: place both HKEX taxonomy-empty buckets and the missing-provider bucket on review/hold.
- `V2_24D_007`: require 100% row-level provenance for every derived value in v2.24E.
- `V2_24D_008`: defer all actual metadata changes to v2.24E and any canonical promotion/freeze decision to v2.24F.

## 8. Closure

`v2.24D` is closed as a provider-quality audit and routing matrix. No canonical data, operational pointer or scoring artifact has been modified.

Guardrails:

- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `metadata_normalization_executed=False`
- `metadata_backfill_executed=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24E — Metadata Improvement Dry Run`.
