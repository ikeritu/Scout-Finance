# Fase 7 — validación histórica v2.36

## Decisión

`INSUFFICIENT_EVIDENCE`

La decisión se tomó por suficiencia temporal antes de calcular rentabilidades. No es un resultado negativo del scoring: significa que los datos actuales no permiten medirlo de forma confirmatoria sin introducir sesgos.

## Auditoría de evidencia

### JPX

- 42 activos.
- Precios ajustados entre 2024-06-10 y 2026-06-08.
- Mediana: 486 sesiones; mínimo: 368.
- El scoring contiene factores de 12 meses.
- Tras formar la primera señal completa queda aproximadamente un año evaluable.
- No hay dos ventanas fuera de muestra ni 12 rebalanceos OOS defendibles.

Clasificación: `INSUFFICIENT_HISTORY`.

### TWSE

- 8 activos.
- Precios desde 2010, pero sin ajustar por dividendos y splits.
- Los fundamentales normalizados tienen `publication_date: null`.
- Usar la fecha de descarga como disponibilidad histórica produciría look-ahead.

Clasificación: `BLOCKED_BY_TEMPORAL_METADATA`.

## Sesgos residuales

- Los 50 activos proceden de un piloto seleccionado antes de fase 7, no de universos históricos point-in-time.
- No existe evidencia suficiente para eliminar survivorship/selection bias.
- JPX tiene profundidad insuficiente.
- TWSE carece de temporalidad fundamental verificable y precio ajustado.

## Trabajo completado

- Contrato y gate congelados antes del rendimiento.
- Capa point-in-time que exige publicación verificable.
- Bloqueo de `retrieved_at` como fallback histórico.
- Retardo mínimo de una sesión.
- Métricas deterministas, costes y benchmark equiponderado.
- Pruebas negativas de look-ahead, fechas, costes, pesos, `NaN`, empates y evidencia insuficiente.
- Informe agregado reproducible sin datos licenciados.

No se publican rentabilidad, Sharpe, drawdown ni exceso frente al benchmark porque calcularlos sobre este alcance no superaría el gate predefinido y podría inducir una conclusión espuria.

## Requisitos para repetir la fase 7

1. JPX: al menos tres años de precios ajustados anteriores a la primera evaluación y universos históricos point-in-time.
2. Fundamentales con fecha de publicación verificable para cada señal.
3. TWSE: precios ajustados y fechas de publicación de MOPS verificables.
4. Al menos dos ventanas OOS y doce rebalanceos OOS.
5. Mantener congelados los contratos o versionar cualquier modificación antes de observar resultados.

## Gate siguiente

La fase 8 no queda promocionada por evidencia cuantitativa.

`phase8_authorized: false`

FASE 8 NO AUTORIZADA: se requiere decisión expresa del usuario y no debe presentarse el ranking como históricamente validado.
