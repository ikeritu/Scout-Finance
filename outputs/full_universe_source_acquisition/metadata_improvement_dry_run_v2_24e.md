# Scout Finance — v2.24E Metadata Improvement Dry Run

**Status:** `METADATA_IMPROVEMENT_DRY_RUN_COMPLETED_NO_PROMOTION`

## Execution result

The deterministic overlay was executed over all **43,089** canonical rows. It is a non-promoted artifact: the canonical CSV and operational pointer were not modified.

- Canonical contract SHA (CRLF) before/after: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707` / `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- Materialized checkout SHA (LF) before/after: `72a02a82851c6b6e14a43944e817700010516286defd8f9984991fb4d1ea50d4` / `72a02a82851c6b6e14a43944e817700010516286defd8f9984991fb4d1ea50d4`
- Derived cells: **56,002**
- Derived-value provenance: **56,002/56,002 = 100.0000%**
- Overwrite attempts: **0**
- Rule conflicts: **0**
- ASX/SGX changed rows: **0**
- Critical failed checks: **0**

## Coverage before / after

| Field | Missing before | Missing after | Deterministic fills | Coverage after |
|---|---:|---:|---:|---:|
| `country` | 21,154 | 21,154 | 0 | 50.9063% |
| `mic` | 32,367 | 23,167 | 9,200 | 46.2345% |
| `currency` | 31,778 | 21,154 | 10,624 | 50.9063% |
| `asset_type` | 37,978 | 17,429 | 20,549 | 59.5512% |
| `instrument_type` | 5,213 | 5,213 | 0 | 87.9018% |
| `instrument_scope` | 31,519 | 15,890 | 15,629 | 63.1228% |

## Provider results

| Provider | Rows | Missing before | Missing after | Filled cells | Changed rows |
|---|---:|---:|---:|---:|---:|
| `cboe_europe_reference_data` | 21,154 | 105,770 | 84,776 | 20,994 | 10,497 |
| `nasdaq_trader_nasdaqlisted` | 3,244 | 9,732 | 0 | 9,732 | 3,244 |
| `jpx_listed_securities` | 3,705 | 7,410 | 0 | 7,410 | 3,705 |
| `nasdaq_trader_otherlisted` | 2,404 | 7,212 | 0 | 7,212 | 2,404 |
| `sec_company_tickers_exchange` | 2,359 | 7,077 | 2,359 | 4,718 | 2,359 |
| `deutsche_boerse_xetra_all_tradable_instruments` | 1,424 | 2,848 | 0 | 2,848 | 1,424 |
| `cboe_listed_symbols` | 1,193 | 3,579 | 1,193 | 2,386 | 1,193 |
| `TWSE` | 696 | 696 | 0 | 696 | 696 |
| `SFC_SIMEV_RNVE` | 23 | 46 | 40 | 6 | 3 |
| `ASX` | 1,316 | 0 | 0 | 0 | 0 |
| `HKEX` | 396 | 1,188 | 1,188 | 0 | 0 |
| `__MISSING_PROVIDER__` | 2,013 | 6,039 | 6,039 | 0 | 0 |
| `hkex_securities_list` | 2,804 | 8,412 | 8,412 | 0 | 0 |
| `sgx_structured_endpoint` | 358 | 0 | 0 | 0 | 0 |

## Holds and unresolved cases

HKEX (`hkex_securities_list` and `HKEX`) and `__MISSING_PROVIDER__` remain on review hold. CBOE Europe geography remains unresolved because the canonical rows do not contain venue/listing detail sufficient for deterministic country, MIC or currency; broad `EQTY` taxonomy rows also remain unresolved. Unresolved cells are reported, never guessed.

## Acceptance and guardrails

All critical gates passed: 43,089 rows, unchanged canonical SHA, unchanged pointer, zero overwrites, zero rule conflicts, 100% provenance, provider reconciliation and zero control-population changes.

- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24F — Metadata Promotion / Freeze Decision`.
