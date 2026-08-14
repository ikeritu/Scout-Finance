# Scout Finance — v2.25D Score Explainability Report

**Status:** `SCORE_EXPLAINABILITY_COMPLETED_NOT_INVESTMENT_READY`

## Conclusion

The formula is **100% mathematically explainable**, but it is **not an investment-attractiveness score**. Every one of the **33,498** scores is reconstructed exactly, with maximum error **0**.

The current formula should be frozen in v2.25E as a **data-readiness / metadata-quality score**, not promoted as production investment scoring.

## What creates the average score of 70.6094

- Data quality: **47.5801 points (67.3848%)**
- Instrument-scope confidence: **16.8305 points**
- Provider quality: **6.1989 points**
- Investment attractiveness: **0 points**

No fundamentals, valuation, momentum, risk, liquidity or manually validated attractiveness labels participate.

## Explainability coverage

- Formula reconstruction: **33,498 / 33,498**
- Explanation archetypes: **19**
- Rows complete across seven audited metadata fields: **13086 (39.065%)**
- Largest identical archetype: **10523 rows (31.4138%)**

The large clusters show that many instruments receive the same score because they share a provider/template, not because their financial attractiveness is equivalent.

## Decision input for v2.25E

- Mathematically explainable: **yes**
- Financially meaningful as an attractiveness ranking: **no**
- Stable enough for investment-score promotion: **no**
- Recommended treatment: **freeze current formula as a data-readiness diagnostic**
- Build a separate future investment score only when authorized financial inputs and validation labels exist.

## Guardrails

- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `explainability_promotion_ready=False`
- metadata artifact and operational pointer unchanged
- OpenAI and broker not used
- `full59k=DEPRECATED_DEFERRED`
- critical failed checks: **0**

**Recommended next phase:** `v2.25E — Scoring Promotion / Freeze Decision`.
