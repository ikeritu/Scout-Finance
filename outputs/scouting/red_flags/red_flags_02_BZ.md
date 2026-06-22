# Red Flags — BZ

- Company: **KANZHUN LIMITED - American Depository Shares**
- Red flag count: `3`
- Max severity: **HIGH**
- Has high or critical: `True`
- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- Pipeline recalculated: `False`

## Flags

### HIGH — Debt-related warning detected

- Category: `debt`
- Code: `DEBT_REASON_PRESENT`
- Detail: Reason token `DEBT` found in source row.
- Source: `reason_text`

```json
{
  "token": "DEBT"
}
```

### HIGH — Operating margin warning detected

- Category: `margins`
- Code: `OPERATING_MARGIN_REASON_PRESENT`
- Detail: Reason token `OPERATING_MARGIN` found in source row.
- Source: `reason_text`

```json
{
  "token": "OPERATING_MARGIN"
}
```

### MEDIUM — Market cap warning detected

- Category: `source_quality`
- Code: `MARKET_CAP_REASON_PRESENT`
- Detail: Reason token `MARKET_CAP` found in source row.
- Source: `reason_text`

```json
{
  "token": "MARKET_CAP"
}
```
