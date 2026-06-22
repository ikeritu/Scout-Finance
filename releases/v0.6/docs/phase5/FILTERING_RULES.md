# Reglas de filtrado — Fase 5A

## Principio general

Cada empresa debe terminar cada stage con uno de estos estados:

```text
PASSED
WATCHLIST
REJECTED
```

## Stage 1 — Investable universe

### Reglas duras

REJECTED si:

```text
is_active = false
asset_type no es common_stock
price <= 0
market_cap missing
avg_volume_90d missing
ticker duplicado no principal
exchange no permitido
```

### Market cap

```text
PASSED:    market_cap >= 300M
WATCHLIST: 100M <= market_cap < 300M
REJECTED:  market_cap < 100M
```

### Precio

```text
PASSED:    price >= 3
WATCHLIST: 1 <= price < 3
REJECTED:  price < 1
```

### Dollar volume

```text
dollar_volume = price * avg_volume_90d
```

```text
PASSED:    dollar_volume >= 2M/día
WATCHLIST: 500k <= dollar_volume < 2M/día
REJECTED:  dollar_volume < 500k/día
```

## Stage 2 — Financial sanity check

### Data completeness

```text
PASSED:    data_completeness_score >= 70
WATCHLIST: 50 <= data_completeness_score < 70
REJECTED:  data_completeness_score < 50
```

### Revenue

```text
PASSED: revenue_ttm > 0
WATCHLIST: revenue_ttm missing pero special_case = true
REJECTED: revenue_ttm <= 0 y no special_case
```

### Operating margin

```text
PASSED:    operating_margin >= 0
WATCHLIST: -20% <= operating_margin < 0
REJECTED:  operating_margin < -20%
```

Excepción growth:

```text
si revenue_growth_3y > 25%
y gross_margin > 40%
y balance fuerte
→ WATCHLIST aunque operating_margin sea negativo
```

### Free cash flow margin

```text
PASSED:    fcf_margin >= 0
WATCHLIST: -10% <= fcf_margin < 0
REJECTED:  fcf_margin < -10%
```

### Deuda

Regla general:

```text
PASSED:    net_debt_to_ebitda <= 3
WATCHLIST: 3 < net_debt_to_ebitda <= 5
REJECTED:  net_debt_to_ebitda > 5
```

No aplicar igual a:

```text
banks
insurance
REITs
utilities
financials
```

### Dilución

```text
PASSED:    shares_dilution_3y <= 10%
WATCHLIST: 10% < shares_dilution_3y <= 30%
REJECTED:  shares_dilution_3y > 30%
```

## Stage 3 — Opportunity scoring

### Fórmula inicial

```text
final_stage3_score =
  20% business_quality_score
+ 15% financial_health_score
+ 15% growth_score
+ 15% valuation_score
+ 15% moat_proxy_score
+ 10% momentum_score
+ 10% data_quality_score
- risk_penalty
```

```text
risk_penalty = risk_score * 0.5
```

### Categorías Stage 3

```text
🟢 Candidata fuerte para scouting
🔵 Alta calidad pero valoración exigente
🟡 Interesante con condiciones
🟠 Riesgo elevado / revisar con cuidado
⚫ Datos insuficientes pero potencial
🔴 Descartada por scoring
```

## Reglas para no perder oportunidades

No descartar directamente por:

```text
PER alto
FCF negativo temporal
margen operativo negativo en empresa growth
falta de un dato no crítico
sector especial
empresa pequeña pero líquida y creciente
valoración exigente si la calidad es alta
```

Usar WATCHLIST o RECOVERABLE.
