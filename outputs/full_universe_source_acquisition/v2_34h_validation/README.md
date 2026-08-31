# v2.34H — validación y score de calidad (Bloque H, fase 5)

Estado: **`COMPLETED`** — 13.917 registros validados, 0 inválidos, 50/50 activos `PROMOTABLE`, 11/11 pruebas offline.

## Resultado

- Ecuaciones contables (tolerancia 2%, nunca exacta): 16/16 pasadas donde comprobables (TWSE); `not_applicable` documentado para JPX (no tiene componentes independientes que comprobar — nunca una comprobación circular).
- 0 problemas temporales; 1 bandera de sanidad económica real (`P020`, margen neto 316%, investigada y marcada, no corregida).
- Score de calidad en 7 dimensiones (identidad/procedencia/completitud/continuidad/coherencia/comparabilidad/frescura); `coherence=null` cuando no hay ecuaciones comprobables, nunca tratado como 0.
- Umbrales de promoción definidos antes de calcular ningún score: `PROMOTABLE ≥ 0.75`, `PARTIAL ≥ 0.50`.
- 50/50 activos `PROMOTABLE`.
- Detalle con valores reales fuera de git; solo el informe agregado se publica.

Detalle completo en `FUNDAMENTAL_VALIDATION_v2_34h.md`.
