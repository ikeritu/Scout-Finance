# Changelog — Scout Finance v0.7 candidate

## Added

- Real pilot funnel release candidate.
- Validated institutional universe pipeline.
- Stage 1 Balanced official policy integrated.
- Stage 2 yfinance-aligned provider-limitation policy integrated.
- Stage 3 scoring outputs integrated.
- Dashboard now displays the validated funnel: `500 → 182 → 63 → 6`.
- Dashboard hotfixes included:
  - 7D.1 dashboard helper/render order fix.
  - 7D.2 institutional universe Count/Nº fix.
  - 7D.3b fundamental coverage exact fix.

## Changed

- Fundamental coverage dashboard now reflects 7C.1 yfinance enrichment:
  - Stage 1 passed: 182
  - Fundamentals matched: 182
  - Coverage: 83.17%
  - Runner phase: 7C.1
- Stage 2 no longer blocks clean pass solely on missing `shares_dilution_3y` when absent due to provider limitation.

## Validated funnel

```text
500 → 182 → 63 → 6
```

## Top candidate

```text
AUPH — Aurinia Pharmaceuticals Inc - Common Shares — score 70.83
```

## Notes

This is a candidate release. It packages validated code and evidence; it does not call OpenAI, yfinance, or external APIs during packaging.
