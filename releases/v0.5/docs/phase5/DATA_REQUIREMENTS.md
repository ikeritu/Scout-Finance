# Requisitos de datos — Fase 5A

## Stage 0 — Universo global

Campos mínimos:

```text
ticker
name
exchange
country
region
currency
sector
industry
asset_type
is_active
market_cap
price
avg_volume_30d
avg_volume_90d
data_source
last_updated
```

Campos recomendados:

```text
isin
figi
cusip
ipo_date
shares_outstanding
free_float
primary_listing
adr_flag
otc_flag
etf_flag
fund_flag
preferred_flag
warrant_flag
spac_flag
duplicate_group
```

## Stage 1 — Datos de mercado

Necesarios:

```text
market_cap
price
avg_volume_30d
avg_volume_90d
dollar_volume
exchange
asset_type
is_active
```

## Stage 2 — Datos fundamentales

Necesarios:

```text
revenue_ttm
revenue_growth_1y
revenue_growth_3y
gross_margin
operating_margin
net_margin
ebitda
free_cash_flow
fcf_margin
total_debt
cash
net_debt
net_debt_to_ebitda
debt_to_equity
current_ratio
interest_coverage
shares_dilution_3y
financial_data_date
data_completeness_score
```

## Stage 3 — Datos de scoring

Necesarios:

```text
business_quality_score
financial_health_score
growth_score
valuation_score
risk_score
moat_proxy_score
momentum_score
liquidity_score
data_quality_score
```

## Datos de valoración

Recomendados:

```text
pe_ratio
forward_pe
ev_ebitda
ev_sales
price_sales
price_book
fcf_yield
earnings_yield
sector_median_pe
sector_median_ev_ebitda
sector_median_price_sales
```

## Dividendos

Si aplica:

```text
dividend_yield
payout_ratio_earnings
payout_ratio_fcf
dividend_growth_5y
dividend_years_growth
dividend_cut_5y
yield_trap_warning
```
