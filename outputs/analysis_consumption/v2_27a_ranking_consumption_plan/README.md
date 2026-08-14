# v2.27A — Ranking Consumption Plan

**Status:** `RANKING_CONSUMPTION_CONTRACT_APPROVED_IMPLEMENTATION_GATED_BY_SCORING_POINTER`

The consumption contract is approved, but a production leaderboard is not authorized.

## Honest operating state

- Operational universe: **43,089 instruments**
- Active production scoring: **none**
- Ranking allowed by pointer: **false**
- Diagnostic score coverage: **33,498 (77.74%)**
- Unscored instruments: **9,591**
- Attractiveness component: **0%**

The v2.25B score is a data-readiness diagnostic dominated by metadata quality. It must not be shown as “best investments”, “top opportunities”, or equivalent.

## Consumer states

| State | Purpose | Ranking |
|---|---|---|
| Catalog available | Search, filter, group and inspect the universe | No |
| Diagnostic locked | Internal data-quality inspection | No |
| Production ranking | Future promoted score artifact | Only after every pointer check passes |
| Scoring unavailable | Safe fallback | No |

## Planned views

- **V01 — Universe explorer:** available now; state `CATALOG_AVAILABLE`.
- **V02 — Segment overview:** available now; state `CATALOG_AVAILABLE`.
- **V03 — Diagnostic coverage:** gated; state `DIAGNOSTIC_LOCKED`.
- **V04 — Production leaderboard:** blocked; state `PRODUCTION_RANKING`.
- **V05 — Asset comparison:** planned; state `CATALOG_AVAILABLE or PRODUCTION_RANKING`.
- **V06 — Saved ranking view:** blocked; state `PRODUCTION_RANKING`.

## Decision

Catalog exploration is authorized. Diagnostic and production rankings remain blocked. All downstream exports, watchlists and UI components must inherit this state machine.

**Next:** v2.27B - Export Pack Design.
