# Scout Finance v2.34G — métricas derivadas (Bloque G, fase 5)

Fecha: 2026-08-31. Alcance: **calcular métricas derivadas solo cuando sus componentes son reales y comparables**, a partir de los 10.315 registros normalizados del Bloque F. Sin red, sin credenciales, sin score agregado de ningún tipo (explícitamente fuera de alcance).

## Métricas nuevas añadidas al catálogo (extensión no destructiva de `config/fundamental_metrics_v1.json`)

| Métrica | Fórmula | Alcance real |
|---|---|---|
| `gross_margin` | `gross_profit / revenue` | Solo TWSE (`gross_profit` no existe en J-Quants `/fins/summary`) |
| `operating_margin` | `operating_income / revenue` | JPX + TWSE |
| `net_margin` | `net_income / revenue` | JPX + TWSE |
| `roa` | `net_income / total_assets` | JPX + TWSE |
| `current_ratio` | `current_assets / current_liabilities` | Solo TWSE (JPX no reporta el desglose corriente/no corriente) |
| `revenue_growth_yoy` | `(rev_t − rev_t-1y) / \|rev_t-1y\|`, mismo `CurPerType`, un año fiscal de diferencia | Solo JPX (TWSE tiene un único periodo, sin periodo previo con el que comparar) |
| `net_income_growth_yoy` | Igual método, sobre `net_income` | Solo JPX |

`gross_debt`, `net_debt` y `free_cash_flow` ya existían en el catálogo del Bloque C marcados `reported_by: []`; este bloque los deja explícitamente **bloqueados con motivo documentado** (`calculation_impossible_missing_components`) en vez de omitirlos en silencio — evidencia de que se intentó, no ausencia sin explicar.

## Extensión del esquema

`statement_type` gana un nuevo valor de enum: `derived_calculated_by_scout_finance`, distinto de `derived_reported_by_provider` (una ratio que el propio proveedor calcula y reporta, p. ej. `ROE` de J-Quants). Confundir ambos habría mezclado "esto lo dijo la fuente" con "esto lo calculamos nosotros" — exactamente la distinción que la regla de "reportado vs calculado" exige. Cambio puramente aditivo al enum; las 10.315 filas del Bloque C/F ya comiteadas siguen validando sin cambios (verificado re-ejecutando sus 16 pruebas offline previas).

## Reglas duras aplicadas (todas verificadas con casos reales, no solo con fixtures)

1. **Ningún componente ausente se aproxima.** Un margen o ratio solo se calcula si AMBOS componentes tienen `value` no nulo en el mismo periodo; si falta uno, no se emite el registro de esa ratio para ese periodo (verificado: `gross_margin` solo aparece 8 veces, exactamente los 8 activos TWSE, nunca para JPX).
2. **División por cero nunca lanza excepción ni produce `inf`/`nan`.** Se convierte en `value=None` + `missing_reason="calculation_impossible_missing_components"`.
3. **Denominador negativo se marca, no se oculta.** Bandera `negative_denominator_ratio_not_directly_comparable` cuando el denominador de un ratio es negativo (patrimonio negativo, por ejemplo) — el número se calcula igualmente (la división es aritméticamente válida) pero se marca como no directamente comparable con un ratio normal.
4. **Crecimiento con base negativa se marca, no se presenta como un porcentaje ordinario.** Confirmado con datos reales: **7 registros reales** de `net_income_growth_yoy` (activos `P145`, `P154`, `P163`, `P181`×2, `P182`, `P183`) tienen un periodo base con pérdida neta; todos llevan la bandera `negative_base_period_growth_not_directly_comparable`.
5. **Prioridad explícita restated-vs-original** (requisito del Bloque F que faltaba y se corrigió en este mismo bloque, ver más abajo): cuando dos disclosures cubren el mismo asset+periodo+métrica, la versión `restated` siempre prevalece sobre `original`; en empate de estado, prevalece la de `filing_date` más reciente. Nunca "gana la que llegó última en el orden del fichero".
6. **Sin score agregado.** Cada métrica derivada es un `FundamentalRecord` independiente; no existe ningún campo ni fichero que combine varias métricas en una sola puntuación.

## Hallazgo y corrección durante este bloque

Al diseñar el agrupador de periodos para calcular ratios, se detectó que la implementación inicial no aplicaba ninguna regla de prioridad entre un disclosure `restated` y uno `original` del mismo periodo — simplemente se quedaba con el último visto en el orden de iteración, lo cual el Bloque F ya debía haber resuelto explícitamente y no lo hizo. Se corrigió aquí (`_prefer()` en `scripts/fundamental_adapters/derived_metrics.py`) antes de calcular ninguna métrica real, y se añadió una prueba offline específica (`test_restated_disclosure_takes_priority_over_original_for_same_period`) que construye deliberadamente el caso adversarial (el registro `restated` aparece PRIMERO en la lista de entrada, para que un "gana el último" fallara de forma visible si reapareciera).

## Resultado real (evidencia, `derived_metrics_coverage_manifest_v2_34g.json`)

- **3.602 registros derivados**, **0 inválidos contra el esquema**.
- `operating_margin`: 404 OK · `net_margin`: 416 OK · `roa`: 416 OK (JPX + TWSE).
- `gross_margin`: 8 OK · `current_ratio`: 8 OK (TWSE únicamente, tal como predice la asimetría de fuentes).
- `revenue_growth_yoy` / `net_income_growth_yoy`: 203 OK cada una (JPX únicamente); 7 de `net_income_growth_yoy` llevan la bandera de base negativa.
- `gross_debt` / `net_debt` / `free_cash_flow`: 648 registros cada una, **100% bloqueados con motivo documentado** — ninguna de las dos fuentes aprobadas reporta deuda desglosada ni capex.

## Pruebas offline

`tests/qa_fundamental_derived_metrics_v2_34g.py` — 6 casos, sin red, sin datos reales:

1. Un margen/ROA solo se calcula cuando ambos componentes están presentes; `gross_margin` no se inventa cuando `gross_profit` nunca se reportó.
2. División por cero nunca lanza excepción; produce el bloqueo documentado.
3. Denominador negativo se marca con la bandera correspondiente, el valor sigue siendo el cálculo aritmético real.
4. `gross_debt`/`net_debt`/`free_cash_flow` se emiten siempre como bloqueados de forma explícita, nunca omitidos en silencio.
5. Prioridad restated-vs-original verificada con el caso adversarial descrito arriba.
6. Crecimiento interanual calculado correctamente entre periodos coincidentes, con la bandera de base negativa activada en el caso correspondiente; sin periodo previo, no se emite ningún registro de crecimiento (nunca un valor inventado).

```
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/derived_metrics.py scripts/build_fundamental_derived_metrics_v2_34g.py tests/qa_fundamental_derived_metrics_v2_34g.py
.venv/Scripts/python.exe tests/qa_fundamental_derived_metrics_v2_34g.py
PASS: v2.34G-fundamental-derived-metrics/no-division-by-zero/negative-flags/restated-priority/growth-yoy/no-silent-blocked-metrics
.venv/Scripts/python.exe scripts/build_fundamental_derived_metrics_v2_34g.py
{"status": "COMPLETED", "total_derived_records": 3602, "total_invalid_schema_records": 0}
```

Verificado además: dos ejecuciones consecutivas producen un manifiesto de cobertura byte-idéntico. También se re-ejecutaron las 16 pruebas offline de los Bloques C-F tras el cambio de esquema (nuevo valor de enum en `statement_type`) — todas siguen en verde.

## Seguridad y alcance

- Ningún valor derivado real se ha comiteado: `derived_records_v2_34g.jsonl` está en `.gitignore` (añadido antes de crearse). Solo el manifiesto agregado (recuentos por métrica, sin cifras) se publica.
- Sin red, sin credenciales en este bloque.
- `production_scoring_authorized: false`, `allow_ranking: false` — ningún score, ranking ni recomendación se ha producido ni se producirá en este bloque.

**Estado del bloque: `COMPLETED`.** Los 3.602 registros derivados quedan listos para el Bloque H (validación económica/contable y score de calidad de los datos, no de inversión).
