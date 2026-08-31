# PHASE 7 FINAL GATE — v2.36

## Decisión

`INSUFFICIENT_EVIDENCE`

## Qué se validó

- Contrato de backtesting congelado antes de observar rendimiento.
- Disponibilidad point-in-time estricta: publicación/filing obligatorios.
- Prohibición de `retrieved_at` como sustituto histórico.
- Ejecución posterior a la señal, costes y benchmark explícitos.
- Primitivas deterministas para percentiles, carteras y métricas.
- QA negativo de look-ahead y entradas inválidas.

## Qué no se validó

- Capacidad predictiva o rentabilidad del scoring.
- Resultado fuera de muestra.
- Robustez económica frente a costes.
- Generalización fuera de los 50 activos del piloto.

No se calcularon esos resultados porque el gate previo de suficiencia falló.

## Evidencia

- JPX: 42 activos, 368–486 sesiones entre 2024-06-10 y 2026-06-08. Es insuficiente para formar factores de 12 meses y disponer además de dos ventanas OOS.
- Auditoría local real: 10.227 registros JPX, 0 sin fecha de publicación; 88 registros TWSE, 88 sin fecha de publicación.
- TWSE: 8 activos y amplia profundidad de precios, pero precios sin ajustar y fundamentales sin fechas de publicación verificables.
- Universo: piloto actual, no reconstrucción histórica libre de survivorship bias.

## Condición de reapertura

Reabrir v2.36 únicamente cuando existan precios ajustados, fechas point-in-time verificables, universos históricos y profundidad para al menos 12 rebalanceos en dos ventanas OOS.

## Gate siguiente

`phase8_authorized: false`

FASE 8 NO AUTORIZADA: cualquier interfaz futura deberá presentar el ranking como experimental y no validado históricamente, salvo nueva evidencia y nuevo gate expreso.
