# Scout Finance v2.35B — metodología y explicabilidad del scoring

El ranking de fase 6 es experimental y determinista. No utiliza IA generativa, noticias, predicciones ni datos posteriores al 31 de agosto de 2026.

## Flujo

1. Selección temporal fail-closed de fundamentales y precios.
2. Preferencia por periodos fundamentales anuales.
3. Cálculo de 14 factores autorizados.
4. Percentiles globales con midrank para empates.
5. Inversión de dirección en volatilidad y drawdown.
6. Renormalización de pesos solo con cobertura mínima del 50%.
7. Confianza separada del score.
8. Ranking principal limitado a confianza `HIGH` o `MEDIUM`.
9. `LOW` conservado como `PARTIAL_COMPARABILITY`, sin rango principal.
10. Explicaciones por plantilla: tres contribuciones principales, tres débiles, ausencias y limitaciones.

## Controles

- Las contribuciones suman exactamente el score dentro de tolerancia numérica.
- Los empates se resuelven por cobertura, calidad, riesgo y `asset_id`.
- `P020` conserva su anomalía y queda en revisión.
- `P178` queda en revisión por ser una entidad financiera incompatible con el contrato industrial.
- Ningún resultado es una recomendación de inversión.
- La fase 7 y el backtesting permanecen bloqueados.
