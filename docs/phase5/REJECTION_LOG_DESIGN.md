# Diseño del log de rechazo

## Objetivo

Evitar que el embudo sea una caja negra.

Cada empresa que no pasa debe tener un motivo claro, recuperable y auditable.

## Columnas recomendadas

```text
ticker
name
stage
status
reason_code
reason_text
metric_name
metric_value
threshold
severity
recoverable
special_case
sector
industry
country
market_cap
data_date
created_at
```

## Estados

```text
PASSED
WATCHLIST
REJECTED
```

## Severity

```text
low
medium
high
critical
```

## Recoverable

```text
true
false
```

Ejemplo:

```text
MISSING_FCF → recoverable=true
LOW_LIQUIDITY_EXTREME → recoverable=false
HIGH_VALUATION → recoverable=true
DELISTED → recoverable=false
```

## Reason codes iniciales

Stage 1:

```text
INACTIVE_SECURITY
NOT_COMMON_STOCK
MISSING_MARKET_CAP
MARKET_CAP_BELOW_MINIMUM
MISSING_PRICE
PRICE_BELOW_MINIMUM
MISSING_VOLUME
LOW_DOLLAR_VOLUME
DUPLICATE_NON_PRIMARY_LISTING
EXCHANGE_NOT_ALLOWED
```

Stage 2:

```text
MISSING_REVENUE
REVENUE_NOT_POSITIVE
LOW_DATA_COMPLETENESS
OPERATING_MARGIN_TOO_NEGATIVE
FCF_MARGIN_TOO_NEGATIVE
DEBT_TOO_HIGH
HIGH_DILUTION
STALE_FINANCIAL_DATA
SECTOR_RULE_REQUIRED
```

Stage 3:

```text
LOW_FINAL_SCORE
HIGH_RISK_SCORE
LOW_DATA_QUALITY
VALUATION_NOT_ATTRACTIVE
LOW_BUSINESS_QUALITY
LOW_FINANCIAL_HEALTH
LOW_MOAT_PROXY
```
