# v2.37A — auditoría de producto

## Base seleccionada

La base canónica de producto es `app_v2_28.py` y `src/ui_v2_28/`, no `app.py`.

`app_v2_28.py` ya separa catálogo, navegación, persistencia local, informes, estado y estilos. `app.py` conserva numerosas generaciones históricas, fuentes descartadas y scoring anterior; integrarlo directamente crearía riesgo de mezclar contratos incompatibles.

## Reutilización

- Se conserva `app_v2_28.py` como versión estable congelada.
- Se reutilizan los principios de rutas seguras, escritura atómica, accesibilidad y UI local.
- La fase 8 crea `app_v2_37.py` y `src/ui_v2_37/`.

## Flujo objetivo

Inicio → Universo → Ranking experimental → Ficha → Comparador → Watchlist → Informes → Ayuda.

## Riesgos corregidos

- El pointer histórico de scoring sigue fail-closed y no representa el contrato v2.35.
- El nuevo repositorio lee únicamente el universo de 50 activos y el resultado v2.35.
- `AGGREGATE_ONLY` nunca se presenta como datos reales completos.
- TWSE permanece fuera del ranking principal.
- P020 y P178 permanecen sin posición.
- La decisión `INSUFFICIENT_EVIDENCE` es visible y no puede convertirse en promoción desde la UI.
