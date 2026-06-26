# Scout Finance — v1.4D Real Universe Scoring Bridge Report

Status: **OK**

## Summary

- Input rows: 3
- Candidates scored: 3
- Top tickers: AAPL, MSFT, ASML
- Score method: `metadata_score_local_no_market_data`

## Important warning

This is **metadata-only scoring**. It does not use price, market cap, fundamentals, OpenAI, APIs or yfinance.

## Controls

- OpenAI called: False
- API called: False
- yfinance called: False
- Market data called: False
- Pipeline recalculated: False
- Financial scoring recalculated: False

## Score components

- Metadata completeness
- Exchange presence / known major exchange
- Country presence / developed market proxy
- Sector presence / high-signal sector proxy
- Industry presence
- Stable order tie-breaker

## Candidates

- `AAPL` — Apple Inc. — score `96.75` — `METADATA_SCORE`
- `MSFT` — Microsoft Corporation — score `96.65` — `METADATA_SCORE`
- `ASML` — ASML Holding N.V. — score `96.55` — `METADATA_SCORE`