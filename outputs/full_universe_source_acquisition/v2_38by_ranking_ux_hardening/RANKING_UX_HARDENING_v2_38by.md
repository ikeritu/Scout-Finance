# Ranking UX Hardening v2.38BY

Decision: `COMPLETED_RANKING_UX_HARDENING_READ_ONLY`.

This phase hardens the `Ranking global (experimental)` screen created in v2.38BW over the real v2.38BV output and closed by v2.38BX.

UX changes verified:

- Search by company, ticker, asset id, or country.
- Country and confidence filters retained.
- Score and coverage range filters added.
- Top N control added.
- Filtered CSV export added without private watchlist data.
- Blocked population is visible as its own review surface.
- Copy states the screen is experimental research, not financial advice, not a price target, not a return promise, and not a broker workflow.

Guardrails: no scoring recomputation, no methodology change, no weight change, no network calls, no broker actions, and no recommendations.

Next recommended phase: `v2.38BZ -- Product readiness gate`.
