# Scout Finance — v2.25C Score Stability Audit

**Status:** `SCORE_STABILITY_AUDIT_COMPLETED_HOLD_FOR_EXPLAINABILITY`

## Decision

The audit is complete, but the score is **not stable enough for promotion**. Ranking continuity is high (Pearson **0.8906**), while only **53.97%** of rows remain in the same score band. The correct decision is **HOLD** pending v2.25D explainability.

## Core results

- Input rows: **33,498**
- Changed rows: **16,116 (48.11%)**
- Same-band rows: **18,078 (53.97%)**
- Band migrations: **15,420 (46.03%)**
- Mean absolute delta: **10.0086**
- Maximum absolute delta: **35.4**
- Positive / negative / unchanged: **16,116 / 0 / 17,382**
- Crossed upward through 70: **9,022**
- Crossed upward through 85: **10,743**
- Largest exact-score cluster: **10,523 rows at 44.5 (31.41%)**

## Structural finding

The change is not random noise. It is strongly provider-driven:

- `nasdaq_trader_nasdaqlisted`: +29.4796 mean points; 100% change bands.
- `nasdaq_trader_otherlisted`: +29.4683; 100% change bands.
- `jpx_listed_securities`: +18.2; 100% change bands.
- `sec_company_tickers_exchange` and `cboe_listed_symbols`: +18.2; 100% change bands.
- `cboe_europe_reference_data`: +0.8992 mean, but a residual maximum of +24.2.

The shift is explainable as deterministic metadata enrichment, but its magnitude means the score now behaves primarily as a metadata/provider-quality measure. It must not be presented as investment attractiveness.

## Guardrails

- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `stability_promotion_ready=False`
- promoted metadata and operational pointer unchanged
- OpenAI and broker not used
- `full59k=DEPRECATED_DEFERRED`
- critical failed checks: **0**

**Recommended next phase:** `v2.25D — Score Explainability Report`.
