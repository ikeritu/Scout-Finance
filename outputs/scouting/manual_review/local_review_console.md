# Scout Finance — Local Review Console

Status: **OK**

This console is generated from v0.9 experimental outputs.

## Safety

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- Pipeline recalculated: `False`
- Not financial advice.
- Manual review required.

## Candidates

| Ticker | Company | Auto verdict | Red flags | Max severity | Manual status |
|---|---|---:|---:|---:|---|
| AUPH | Aurinia Pharmaceuticals Inc - Common Shares | NEEDS_MORE_DATA | 3 | HIGH | pending_review |
| BZ | KANZHUN LIMITED - American Depository Shares | NEEDS_MORE_DATA | 3 | HIGH | pending_review |
| ADBE | Adobe Inc. - Common Stock | NEEDS_MORE_DATA | 3 | HIGH | pending_review |

## How to review manually

Edit `outputs/scouting/manual_review/manual_review_state.json`.

Allowed manual statuses:

- `pending_review`
- `reviewed_watchlist`
- `reviewed_reject`
- `needs_more_data`
