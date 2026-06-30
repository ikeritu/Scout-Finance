# v1.5D3 — Final UX Polish Render Path Fix

## Objetivo

Aplicar el pulido en las rutas reales de renderizado observadas en la app.

## Problemas corregidos

- El ranking seguía mostrando `local_score_high`.
- El ranking seguía mostrando `manual_market_data.csv`.
- La ficha seguía mostrando categoría técnica cortada.
- No aparecía el bloque `Lectura del ranking`.

## Solución

- Humaniza `clean_df` dentro de `_build_clean_ranking_table()`.
- Cambia la métrica de categoría para usar `_sf15d3_human_category`.
- Cambia proveedor/estado a etiquetas humanas.
- Inserta `Lectura del ranking` antes de `Estado IA legacy resumido`.

## No toca

- scoring
- market data
- outputs
- OpenAI
- broker
- yfinance
- pipeline
