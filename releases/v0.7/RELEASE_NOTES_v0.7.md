# Release Notes — Scout Finance v0.7 candidate

## Summary

Scout Finance v0.7 candidate freezes the first real pilot institutional funnel.

The release includes:

```text
Institutional universe → Stage 1 Balanced → Stage 2 yfinance-aligned → Stage 3 scoring
```

Validated funnel:

```text
500 → 182 → 63 → 6
```

## Included evidence

- Stage 1 closure evidence.
- Stage 2 yfinance policy implementation evidence.
- Stage 3 scoring evidence.
- Dashboard integration evidence.
- 7E.1 v0.7 release checkpoint evidence.

## Important policy note

Missing `shares_dilution_3y` from yfinance is treated as a provider limitation warning, not as an automatic clean-pass blocker.

Dilution is not ignored. It remains pending for stronger sources such as SEC/companyfacts or direct filings.

## Candidate status

```text
Ready for v0.7 release packaging: True
```
