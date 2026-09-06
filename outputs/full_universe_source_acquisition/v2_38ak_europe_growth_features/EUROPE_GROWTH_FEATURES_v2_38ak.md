# v2.38AK — Europa: primeras features de crecimiento interanual reales (no ratios de un solo periodo)

Fecha: 2026-09-06. Alcance: calcular, por primera vez para Europa, features de **crecimiento interanual real** (year-over-year) a partir de los datos multi-año ya reales en el pipeline — reutilizando la misma metodología ya validada en EE. UU. (`v2.38G`), adaptada a las claves de periodo (`period_end`, formato ISO) en vez del entero `fy` que usa SEC.

## Por qué este bloque

El usuario replanteó el objetivo del proyecto hacia una "lista de candidatos con potencial de crecimiento" (nunca "recomendaciones de inversión"), y confirmó explícitamente, tras una pregunta de aclaración con tres opciones, que la prioridad inmediata debe ser **crecimiento multi-año antes que cualquier otra pieza del sistema** ("Sí, primero crecimiento multi-año (Recomendado)"). `v2.38X` ya calcula ratios reales (`net_margin`, `ROA`, `ROE`, etc.), pero **solo del periodo más reciente de cada empresa** — estructuralmente incapaz de distinguir "empresa sana" de "empresa que está mejorando". Este bloque llena ese hueco concreto.

## Alcance real de los datos de hoy

Hoy **solo Austria** (`v2.38AI`, 20 empresas vía firmenakte.at) tiene más de un ejercicio fiscal real por empresa en este pipeline (entre 2 y 5 años según la empresa). La extracción iXBRL de GB/Irlanda (`v2.38W`/`v2.38Y`) siempre capturó un único periodo por empresa — nunca puede superar el umbral de "≥2 periodos" que exige este script, y así lo reporta honestamente (`INSUFFICIENT_FEATURE_EVIDENCE`) si algún día se le pasa como entrada.

## Qué se calculó y qué no

De la metodología real de EE. UU. (`v2.38G`) se reutilizan: `yoy()` (crecimiento interanual, con la misma regla de fail-closed: `previous <= 0` → `None`, nunca una división por cero o negativo), `growth_acceleration_flag` (compara el crecimiento del último periodo contra el del periodo anterior, exige 3+ periodos) y `margin_expansion_flag` (compara el margen neto del periodo actual contra el anterior).

**No se reproducen aquí** las features derivadas de flujo de caja libre (`free_cash_flow`, `capex_to_revenue`, `cash_conversion_ratio`, `positive_fcf_flag`, `fundamental_momentum_flag`): los conceptos capturados de Austria (`v2.38AI`) no incluyen flujo de caja operativo ni capex — no es una omisión, es una limitación real y confirmada de los datos disponibles hoy.

Cuatro features de crecimiento calculadas: `revenue_yoy_growth`, `net_profit_yoy_growth`, `assets_yoy_growth`, `equity_yoy_growth` — cada una a partir de los dos periodos más recientes reales en el fichero, no necesariamente años calendario consecutivos (ver hallazgo real más abajo).

## Hallazgo real: un hueco de datos ya conocido, ahora visible en el crecimiento

`RAW` (una de las 20 empresas austriacas) tiene los 5 ejercicios fiscales completos en el fichero, con la clave de concepto `umsatzerloese` presente en cada uno — pero **con valor `null` en los 5**. Esto es consistente con la limitación ya documentada en `v2.38AI` (solo 27/54 combinaciones empresa-año reconcilian exactamente la identidad contable; bancos y aseguradoras bajo esquemas BWG/VAG probablemente usan una estructura estatutaria distinta). El script trata correctamente cualquier concepto con valor `null` como ausente (nunca como cero), así que `RAW` queda en `FEATURES_PARTIAL` con las cuatro features de crecimiento como `missing_current_period_value` — nunca un crecimiento inventado a partir de un cero falso.

## Ejecución real

- **20/20 empresas austriacas** procesadas, **0 insuficientes** (las 20 tienen ≥2 periodos reales en el fichero).
- **9 `FEATURES_READY`** (las 6 features de crecimiento completas): XD4, ABS2, AZ2, OMV, SLL, KTN, O3P, 1AST, FQT.
- **11 `FEATURES_PARTIAL`**: RAW, EBO, OEWA, FAA, UN9, WIB, VAS, WAH, GEPH, 4X0, 0B2 — cada una con al menos un concepto real ausente en alguno de sus dos periodos más recientes, documentado fila a fila en `europe_growth_feature_rejections_v2_38ak.csv` con una razón específica (`missing_current_period_value`, `missing_previous_period_value`, `nonpositive_previous_period_value`).
- **35 filas de rechazo** en total, cada una trazable a una empresa, un feature y una razón concreta.
- **OMV AG** (la única empresa de las 20 que ya se documentó como caso de holding con margen neto no consolidado extremo en `v2.38AI`) muestra `revenue_yoy_growth=7.67%`, `net_profit_yoy_growth=10.36%` — un crecimiento año a año coherente y calculable, aunque el nivel absoluto de margen siga sin ser comparable al grupo consolidado (ver advertencia de `v2.38AI`, que sigue aplicando aquí sin cambios).

## Salvaguardas

Sin red, sin scoring, sin ranking, sin recomendaciones, sin fase 9C — igual que todo el resto de este pipeline. Cada valor de crecimiento que no puede calcularse honestamente queda como `None` con una fila de rechazo trazable, nunca inventado ni interpolado.

**Estado del bloque: `COMPLETED_EUROPE_GROWTH_FEATURES_AUSTRIA_ONLY_NOT_RECOMMENDATIONS`.** Primera pieza real de la nueva dirección de "crecimiento antes que ratios estáticos" — limitada hoy a las 20 empresas austriacas porque son las únicas con evidencia multi-año real; se extenderá automáticamente a cualquier país futuro que aporte 2+ ejercicios fiscales reales, sin tocar la lógica de este script.
