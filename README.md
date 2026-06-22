# Scout Finance v0.4 — Private Research MVP

## Qué es

Scout Finance es una herramienta privada para priorizar empresas investigables mediante:

- pipeline cuantitativo;
- análisis asistido por IA;
- outputs estructurados;
- comparativa visual;
- histórico por empresa;
- feedback manual.

No es una app de trading, no se conecta a brokers y no da recomendaciones de compra/venta.

## Estado actual

Versión estable: `v0.4`

Esta versión consolida las fases:

- Fase 2: outputs estructurados Markdown + JSON + PNG + HTML.
- Fase 4C: Dashboard ejecutivo.
- Fase 4D: Comparativa visual de empresas.
- Fase 4E: Histórico por empresa.
- Fase 4F: Ajustes / panel técnico.
- Fase 4G: Revisión de estabilidad.
- Fase 4H: Documentación + FAQ actualizado.

## Flujo recomendado

1. Ejecutar pipeline cuantitativo.
2. Revisar Ranking.
3. Abrir Análisis empresa.
4. Generar o consultar outputs Fase 2.
5. Comparar empresas.
6. Revisar histórico.
7. Registrar feedback.
8. Revisar Ajustes si algo falla.

## Ejecutar app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Checker de estabilidad

```powershell
.\.venv\Scripts\python.exe check_phase4g_stability.py
```

## Outputs Fase 2

Los análisis estructurados se guardan en:

```text
outputs/analyses
```

Archivos esperados:

```text
TICKER_FECHA.md
TICKER_FECHA.json
TICKER_FECHA_scorecard.png
TICKER_FECHA_scenarios.png
TICKER_FECHA_executive_card.html
```

## Pestañas principales

### Dashboard

Vista ejecutiva del estado general.

### Ranking

Tabla priorizada de empresas.

### Análisis empresa

Ficha individual, análisis legacy y outputs Fase 2.

### Comparar empresas

Comparativa visual basada en JSON ya generados.

### Histórico / técnico

Evolución por ticker usando históricos JSON.

### Ajustes

Panel técnico con estado OpenAI, costes, rutas, outputs y checks.

## Aviso

Scout Finance es una herramienta de investigación. No ofrece asesoramiento financiero.
