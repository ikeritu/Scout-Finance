# Scout Finance — Fase 5A: Diseño del embudo global de filtros

## Objetivo

Diseñar el embudo global que permitirá pasar de un universo amplio de empresas cotizadas a una lista reducida de candidatas para scouting profundo.

```text
~59.000 empresas
→ Stage 1: investable universe
→ Stage 2: financial sanity check
→ Stage 3: opportunity scoring
→ ~450 candidatas
→ IA solo para scouting profundo
```

## Principio clave

El embudo no debe funcionar como tres puertas cerradas de pasa/no pasa.

Debe funcionar con tres estados:

```text
PASSED
WATCHLIST
REJECTED
```

Así se puede descartar agresivamente sin perder empresas interesantes por datos incompletos, sector especial, momento financiero temporal o tipo de negocio.

## Qué incluye esta fase

```text
README_PHASE5A_GLOBAL_FUNNEL.md
GLOBAL_FUNNEL_DESIGN.md
FILTERING_RULES.md
DATA_REQUIREMENTS.md
REJECTION_LOG_DESIGN.md
filter_config.yaml
templates/global_universe_template.csv
templates/stage1_output_template.csv
templates/stage2_output_template.csv
templates/stage3_output_template.csv
templates/rejection_log_template.csv
templates/funnel_summary_template.json
```

## Qué NO incluye

Esta fase no implementa código de filtrado todavía.

No toca:

```text
app.py
OpenAI
pipeline actual
Fase 2
Dashboard
Ranking
Comparativa
Histórico
Ajustes
outputs existentes
```

## Siguiente fase recomendada

```text
Fase 5B — Cargar universo global mínimo desde CSV
```
