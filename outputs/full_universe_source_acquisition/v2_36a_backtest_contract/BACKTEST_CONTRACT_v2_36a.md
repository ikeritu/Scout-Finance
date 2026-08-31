# v2.36A — contrato de validación histórica

Este contrato se congeló antes de observar cualquier rentabilidad de fase 7.

## Alcance

- Mercado principal: JPX.
- TWSE: diagnóstico limitado, nunca promoción conjunta automática.
- P020 y P178: fuera del análisis principal por los gates heredados.
- Ranking: contrato v2.35 sin recalibración de pesos.
- Cartera: equiponderada; top 5, top 10 y quintiles.
- Rebalanceo principal: mensual; trimestral como sensibilidad.
- Ejecución: primera sesión posterior a la señal, nunca el mismo cierre.
- Benchmark: universo elegible equiponderado.
- Costes unidireccionales: 0 pb solo como referencia, 25 pb base y 75 pb adverso.

## Reglas point-in-time

La fecha de publicación o filing es obligatoria. `retrieved_at` no prueba cuándo el mercado conoció un dato y está prohibido como fallback histórico. La normalización se calcula únicamente con el corte transversal disponible en cada fecha de señal.

## Evidencia mínima

- 756 sesiones por activo.
- 20 activos.
- 12 rebalanceos fuera de muestra.
- 2 ventanas fuera de muestra independientes.

Si falta cualquiera de estas condiciones, la decisión debe ser `INSUFFICIENT_EVIDENCE` aunque una simulación corta resulte positiva.

El contrato canónico está en `config/backtest_contract_v1.json`; el gate previo, en `config/backtest_promotion_gate_v1.json`.

`phase8_authorized: false`
