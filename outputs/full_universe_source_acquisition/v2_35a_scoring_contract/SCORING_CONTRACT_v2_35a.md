# Scout Finance v2.35A — contrato de scoring congelado

La fase 6 fue autorizada expresamente por el usuario después del cierre `v2.34J`. Este bloque define el contrato antes de aceptar ningún ranking como resultado.

## Primer cálculo real y corrección metodológica

El primer cálculo local verificó 50/50 activos con precios y fundamentales, pero mostró dos defectos de comparabilidad:

1. Un activo TWSE con confianza `LOW` aparecía segundo al renormalizar solo el 54% de los pesos disponibles. Los resultados `LOW` pasan a `PARTIAL_COMPARABILITY` y no participan en el ranking principal; sus scores se conservan y publican por separado.
2. `P178` es `The San-in Godo Bank,Ltd.`. Una entidad financiera no es comparable mediante el contrato industrial. Queda `REVIEW_REQUIRED` hasta disponer de un contrato específico para financieras.

Estos cambios corrigen defectos metodológicos observados; no optimizan rentabilidad ni favorecen empresas concretas. `P020` conserva su margen neto real del 316,5% y queda `REVIEW_REQUIRED` por la regla general de margen absoluto superior al 300%.

## Alcance

- 14 factores en calidad, crecimiento, valoración, momentum y riesgo.
- Pesos contractuales: 100%.
- Normalización: percentil global con midrank determinista.
- Cobertura mínima: 50%.
- Ranking principal: confianza `HIGH` o `MEDIUM`.
- Confianza `LOW`: clasificación parcial separada.
- Shortlist: top 10 predefinido.
- Sin imputación de ceros, medias o neutral 50.
- Sin fase 7, backtest ni recomendación de inversión.
