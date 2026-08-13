# Scout Finance — v2.24B Country / MIC / Currency Backfill Plan

**Status:** `COUNTRY_MIC_CURRENCY_BACKFILL_PLAN_COMPLETED_NO_DATASET_MODIFICATION`

## 1. Scope and immutable baseline

This phase defines a deterministic, auditable plan for improving `country`, `mic` and `currency` coverage. It does **not** execute a backfill and does **not** modify the canonical dataset or operational pointer.

Canonical baseline:

- Dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_21h_activated_operational_reference.csv`
- Rows: **43,089**
- SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- `exchange` coverage: **43,089 / 43,089 = 100%**

v2.24A / v2.23B baseline gaps:

| Field | Missing rows | Missing % | Coverage % |
|---|---:|---:|---:|
| country | 21,154 | 49.0937% | 50.9063% |
| mic | 32,367 | 75.1166% | 24.8834% |
| currency | 31,778 | 73.7497% | 26.2503% |

## 2. Complete provider decomposition of the three gaps

The existing evidence partitions the missing rows without unexplained residuals.

| Provider bucket | Rows | Country missing | MIC missing | Currency missing | Planned treatment |
|---|---:|---:|---:|---:|---|
| `cboe_europe_reference_data` | 21,154 | 21,154 | 21,154 | 21,154 | Highest priority; derive only from deterministic venue/listing metadata rules |
| `nasdaq_trader_nasdaqlisted` | 3,244 | 0 | 3,244 | 3,244 | Provider/exchange mapping; preserve existing country |
| `nasdaq_trader_otherlisted` | 2,404 | 0 | 2,404 | 2,404 | Listing-exchange-specific mapping; do not collapse multiple venues |
| `sec_company_tickers_exchange` | 2,359 | 0 | 2,359 | 2,359 | Exchange/provider mapping; preserve existing country |
| `cboe_listed_symbols` | 1,193 | 0 | 1,193 | 1,193 | US Cboe-specific venue mapping |
| `__MISSING_PROVIDER__` | 2,013 | 0 | 2,013 | 0 | MIC-only remediation from existing exchange; do not infer provider |
| `deutsche_boerse_xetra_all_tradable_instruments` | 1,424 | 0 | 0 | 1,424 | Currency-only remediation; preserve existing country and MIC |
| **TOTAL** | — | **21,154** | **32,367** | **31,778** | **100% of audited gaps assigned** |

## 3. Deterministic precedence rules

Backfill execution in a later dry-run must apply the following precedence, field by field:

1. **Preserve an existing non-empty value.** No rule may overwrite populated canonical metadata in the dry run unless a separate conflict audit explicitly authorizes the correction.
2. **Use authoritative provider-native metadata when available.** A directly supplied country/MIC/currency value has precedence over an inferred value.
3. **Use normalized `exchange` as the primary internal anchor.** `exchange` has 100% coverage and can support a mapping only when the relation for the target field is deterministic.
4. **Use MIC as a venue normalization anchor when already present or deterministically derived.** MIC may support venue-country/currency checks, but must not be used to invent issuer domicile.
5. **Use provider-specific mapping rules before generic exchange rules** when the same exchange label has different semantics across source feeds.
6. **Do not fill ambiguous mappings.** Any 1:N, multi-currency, cross-listing, alias or semantic conflict is classified as `UNRESOLVED_REVIEW_REQUIRED`.
7. **Never use ticker/name heuristics as a silent fallback.** Listing suffixes may be used only if explicitly enumerated and validated as deterministic for the relevant provider.

## 4. Field semantics and safety constraints

### country

The backfill must preserve the semantic meaning already used by the project. A venue location must not automatically be written as issuer domicile. For the CBOE Europe block, country may only be filled when the source/listing metadata establishes the intended country deterministically. Otherwise it remains unresolved.

### mic

MIC is a venue identifier. Backfill should use an explicit `provider + exchange/listing venue -> MIC` mapping. Generic mappings are allowed only when one exchange label maps to exactly one MIC in the relevant provider context.

### currency

Currency should represent the listing/trading currency used by the dataset. Backfill may use provider-native currency or a deterministic venue mapping. Multi-currency venues or instruments must not receive a single default currency unless the provider context proves it.

## 5. Mapping registry design

v2.24E dry-run implementation should consume a versioned mapping registry rather than hard-coded ad-hoc conditionals. Minimum fields:

- `rule_id`
- `source_provider`
- `exchange_raw`
- `exchange_normalized`
- `target_field`
- `target_value`
- `rule_basis`
- `rule_confidence` (`deterministic` only for auto-fill)
- `source_evidence`
- `overwrite_allowed` (default `False`)
- `active`
- `notes`

Each row-level backfill result should also record provenance, e.g. `metadata_rule_id` and `metadata_backfill_status`.

## 6. Conflict / unresolved classes

A row must remain unchanged and be surfaced for review when any of these conditions is detected:

- existing populated value conflicts with proposed mapping;
- one provider/exchange combination maps to multiple MICs;
- venue supports multiple trading currencies and row-level currency is unavailable;
- CBOE Europe listing does not deterministically identify the intended `country` semantic;
- cross-listed instrument makes venue-based inference unsafe;
- provider is missing and exchange alone is not sufficient for a deterministic MIC;
- provider alias or exchange alias is not present in the approved registry;
- proposed value is derived only from ticker/name pattern heuristics.

No unresolved row is a critical failure by itself; silently imputing it is.

## 7. Provider execution order for the future dry run

1. `cboe_europe_reference_data` — largest blocker and the entire country gap.
2. `nasdaq_trader_nasdaqlisted`.
3. `nasdaq_trader_otherlisted`.
4. `sec_company_tickers_exchange`.
5. `cboe_listed_symbols`.
6. `__MISSING_PROVIDER__` — MIC only and only where exchange uniquely resolves the venue.
7. `deutsche_boerse_xetra_all_tradable_instruments` — currency only.

This order is prioritization, not permission to impute ambiguous values.

## 8. Acceptance gates for v2.24E dry run

Before any metadata promotion can be considered, the dry run must report at minimum:

- baseline and post-dry-run missing counts for `country`, `mic`, `currency`;
- filled rows by provider, field and `rule_id`;
- unresolved rows by reason;
- conflicts with existing populated values;
- invalid/unknown MIC count;
- invalid/unknown currency code count;
- row count unchanged at 43,089;
- uniqueness/integrity checks unchanged;
- canonical dataset SHA unchanged during dry run;
- operational pointer unchanged;
- zero scoring promotion side effects.

A coverage improvement target is informative, not sufficient for promotion. Correct provenance and zero silent ambiguity take precedence over maximizing fill percentage.

## 9. Decision register

- `V2_24B_001`: approve `exchange` as the primary internal mapping anchor because coverage is 100%.
- `V2_24B_002`: approve provider-specific deterministic mappings as the preferred backfill mechanism.
- `V2_24B_003`: preserve all existing populated metadata by default; conflicts are reported, not overwritten.
- `V2_24B_004`: assign the full audited country/MIC/currency gap to seven explicit provider buckets with zero unexplained residual rows.
- `V2_24B_005`: keep ambiguous CBOE Europe country semantics unresolved unless listing/source evidence deterministically establishes the intended value.
- `V2_24B_006`: prohibit ticker/name guessing, default venue currency guessing and generic 1:N exchange-to-MIC fills.
- `V2_24B_007`: defer all actual writes to **v2.24E — Metadata Improvement Dry Run** and any promotion to **v2.24F — Metadata Promotion / Freeze Decision**.

## 10. Closure

`v2.24B` is closed as a **planning-only** phase. No row has been backfilled and no canonical artifact has been changed.

Guardrails:

- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `metadata_backfill_executed=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24C — Asset Type Normalization Plan`.