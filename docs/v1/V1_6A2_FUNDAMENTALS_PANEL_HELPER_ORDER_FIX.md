# v1.6A2 — Fundamentals Panel Helper Order Fix

## Objetivo

Corregir el runtime error:

```text
NameError: name '_sf16a_render_fundamentals_panel' is not defined
```

## Causa

La llamada al panel estaba dentro de `_render_dashboard_tab()`, pero el helper quedaba definido demasiado tarde.

## Cambio

- Mueve el bloque `v1.6A FUNDAMENTALS INPUT BRIDGE PANEL` antes de `_render_dashboard_tab()`.
- Mantiene la llamada al panel en Dashboard antes de `Ejecución`.

## No toca

- scoring
- ranking
- market data
- outputs de scoring
- OpenAI
- broker
- yfinance
- APIs externas
