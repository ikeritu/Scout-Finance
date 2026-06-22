# Diseño maestro — Embudo global de filtros

## Objetivo principal

Scout Finance debe convertirse en un sistema de scouting financiero global capaz de:

1. Partir de un universo amplio de empresas cotizadas.
2. Aplicar filtros automáticos por capas.
3. Reducir drásticamente el universo.
4. Mantener trazabilidad de descartes.
5. Reservar IA para las mejores candidatas.

## Embudo objetivo

```text
Stage 0 — Universo global
~59.000 empresas

Stage 1 — Investable universe
~11.000 - 13.000 empresas

Stage 2 — Financial sanity check
~2.000 - 3.000 empresas

Stage 3 — Opportunity scoring
~400 - 600 candidatas

Stage 4 — Scouting profundo
Top 20 / Top 50 / Top 100
```

## Sistema de estados

### PASSED

La empresa pasa al siguiente stage.

### WATCHLIST

La empresa no pasa limpio, pero no debe descartarse.

Motivos típicos:

- datos incompletos;
- sector especial;
- empresa growth;
- empresa pequeña pero prometedora;
- valoración exigente;
- FCF temporalmente negativo;
- margen negativo pero crecimiento fuerte.

### REJECTED

La empresa queda descartada para el embudo principal.

Debe guardarse motivo.

## Regla de oro

No descartar una empresa interesante por un único dato incompleto o por una métrica que no aplica a su sector.

## Stage 0 — Universo global

Archivo:

```text
data/universe/global_universe.csv
```

Columnas mínimas:

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

## Stage 1 — Investable universe

Objetivo: eliminar empresas no invertibles, no negociables o no analizables.

Salidas:

```text
data/stages/stage1_passed.csv
data/stages/stage1_watchlist.csv
data/stages/stage1_rejected.csv
outputs/scouting/stage1_summary.json
```

## Stage 2 — Financial sanity check

Objetivo: eliminar empresas financieramente rotas o sin datos fundamentales útiles.

Salidas:

```text
data/stages/stage2_passed.csv
data/stages/stage2_watchlist.csv
data/stages/stage2_rejected.csv
outputs/scouting/stage2_summary.json
```

## Stage 3 — Opportunity scoring

Objetivo: seleccionar candidatas reales de scouting.

Scores:

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
final_stage3_score
```

Importante:

```text
risk_score: 0 = bajo riesgo, 10 = alto riesgo
```

## Stage 4 — Scouting profundo

Aquí entra Scout Finance v0.4.1:

- Dashboard;
- Ranking;
- Análisis empresa;
- Fase 2;
- Comparativa;
- Histórico;
- Feedback;
- OpenAI controlado.
