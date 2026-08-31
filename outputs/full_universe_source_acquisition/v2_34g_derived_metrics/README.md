# v2.34G — métricas derivadas (Bloque G, fase 5)

Estado: **`COMPLETED`** — 3.602 registros derivados, 0 inválidos, 6/6 pruebas offline, sin score agregado.

## Resultado

- Márgenes (`operating_margin`, `net_margin`), `roa`: calculados para JPX + TWSE (404-416 OK cada uno). `gross_margin`/`current_ratio`: solo TWSE (8 OK cada uno) — JPX no reporta los componentes necesarios.
- `revenue_growth_yoy`/`net_income_growth_yoy`: solo JPX (203 OK cada una); 7 casos reales con base negativa, correctamente marcados, nunca presentados como un porcentaje ordinario.
- `gross_debt`/`net_debt`/`free_cash_flow`: 100% bloqueados con motivo explícito (648 cada uno) — ninguna fuente aprobada reporta deuda desglosada ni capex.
- División por cero y denominador negativo manejados sin excepción y sin ocultar el problema.
- Hallazgo y corrección durante este bloque: se detectó que el Bloque F no tenía una regla de prioridad restated-vs-original; se implementó y probó aquí antes de calcular ninguna métrica.
- Valores reales fuera de git; solo el manifiesto agregado de cobertura se publica.

Detalle completo en `DERIVED_METRICS_v2_34g.md`.
