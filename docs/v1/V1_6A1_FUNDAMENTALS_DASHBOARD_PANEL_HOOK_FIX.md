# v1.6A1 — Fundamentals Dashboard Panel Hook Fix

## Objetivo

Corregir que v1.6A validaba correctamente por consola, pero el panel visual `Fundamentals input` no aparecía en el Dashboard.

## Causa

El helper `_sf16a_render_fundamentals_panel()` existía, pero no estaba enganchado en la ruta real:

```python
_render_dashboard_tab()
```

## Cambio

Inserta:

```python
_sf16a_render_fundamentals_panel()
```

antes de los controles de ejecución del dashboard.

## No toca

- scoring
- ranking
- market data
- outputs de scoring
- OpenAI
- broker
- yfinance
- APIs externas
