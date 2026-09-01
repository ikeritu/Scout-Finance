# Gate final de fase 9A — v2.38A

## Decisión

**`COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING`**

## Evidencia del gate

- Dataset canónico resuelto y fijado por hash: sí.
- Total exacto y conservación fila a fila: 43.089/43.089.
- Elegibilidad vigente separada: 21.165 elegibles, 10.432 excluidas, 9.710 revisables, 1.782 bloqueadas.
- Identidad estable y sin colisiones de `asset_id`: sí.
- Ausencias de país, MIC, moneda, ISIN, sector, industria y capitalización cuantificadas: sí.
- Matriz de rutas, licencias y limitaciones para los 15 mercados: sí.
- Artefacto detallado comprimido y resúmenes agregados reproducibles: sí.
- QA offline y fail-closed: sí.

Regresión heredada observada: `tests/qa_eligibility_refinement_v2_33b2.py` conserva una ruta antigua (`outputs/v2_33b2`) y falla antes de leer datos. El fallo existe fuera del cambio 9A; no se modificó una fase histórica para ocultarlo. El gate equivalente vigente `qa_market_universe_inventory_v2_33l.py`, que lee el censo canónico actual, sí pasa.

## Límites y bloqueos

La decisión no significa que las 43.089 filas estén listas para scoring. Solo 50 activos poseen el conjunto local de precios y fundamentales usado en fases 5–8. JPX/TWSE no están escalados; Estados Unidos requiere cuenta y piloto; Europa/ASX/BVC carecen de ruta accionable; Xetra/SGX requieren reparación; la mayoría del censo carece de metadatos financieros suficientes.

No se ejecutó red, no se usaron credenciales, no se descargaron datos, no se calcularon scores, rankings ni recomendaciones y no se modificó la aplicación.

## Autorización posterior

`phase9b_authorized: false`. La fase 9B deberá recibir autorización explícita y un contrato previo de lotes, presupuesto, licencias, reanudación y almacenamiento antes de cualquier adquisición masiva.
