# v2.38AL — Matriz de cobertura global: las 43.089 empresas, cobertura real marcada honestamente

Fecha: 2026-09-06. Alcance: construir, por primera vez, **una fila para cada una de las 43.089 empresas** del censo operativo (`v2.38A`), mostrando con exactitud hasta dónde ha llegado realmente el trabajo de este pipeline para cada una — nunca inventando cobertura, nunca ocultando lo que falta.

## Por qué este bloque

El usuario, tras replantear el objetivo del proyecto hacia una lista de candidatos con potencial de crecimiento, confirmó explícitamente (pregunta de aclaración con 3 opciones) que el futuro botón "actualizar" debe **analizar las 43.000 empresas, marcando "sin datos todavía" las que falten** ("Mostrar las 43.000, marcar sin datos las que falten (Recomendado)"). Este bloque es la primera pieza concreta de esa arquitectura: no ejecuta ningún escaneo nuevo ni recolecta ningún dato — une, por `asset_id`, todo lo que este pipeline ya ha calculado de verdad hasta hoy, y lo expone como una única tabla de 43.089 filas.

## Diseño: identidad → fundamentales → crecimiento es una escalera; precio es independiente

Cada etapa exige la anterior en este pipeline (nunca hay fundamentales sin identidad real, nunca hay crecimiento sin fundamentales), así que `overall_coverage_status` las trata como una única escalera de profundidad. El precio se mantiene en una columna **separada** (`price_status`), deliberadamente fuera de esa escalera: el hallazgo real y confirmado de `v2.38AJ` (ninguna fuente de precios europea gratuita encontrada, tras investigar 5 vías) haría que **toda** empresa europea con crecimiento real calculado pareciera indistinguible de una sin ningún dato — enterraría la señal real que sí existe (identidad, fundamentales, crecimiento) bajo un hueco estructural que nada tiene que ver con la calidad de los datos de esa empresa concreta.

## Principio central: ninguna fila se descarta nunca

A diferencia de cualquier otro constructor de este pipeline (que reporta rechazos por lo que NO pudo calcular), este script no tiene concepto de "rechazo": su función entera es que **las 43.089 filas del censo aparezcan siempre** en la salida, con cobertura mixta o ninguna, nunca excluidas.

## Fuentes unidas (todas ya reales, ninguna nueva)

- **Censo base**: `v2.38A` (43.089 filas, `asset_id` como clave universal).
- **EE. UU.**: `v2.38G` (fundamentales + crecimiento, un mismo fichero de 555 empresas dividido de vuelta en dos etapas según qué campos concretos estén presentes) y `v2.38H` (precio real, 554 empresas).
- **Europa**: `v2.38AB` (identidad real vía Xetra/GLEIF, 689 activos), `v2.38X` (fundamentales, 21 empresas tras la exclusión de identidad conocida), `v2.38AK` (crecimiento, 20 empresas austriacas).

## Resultado real (ejecución completa de las 43.089 filas)

| `overall_coverage_status` | Empresas |
|---|---|
| `NO_DATA_YET` | 41.845 |
| `IDENTITY_ONLY_NO_FUNDAMENTALS_YET` | 690 |
| `FUNDAMENTALS_PARTIAL_NO_GROWTH_YET` | 34 |
| `FUNDAMENTALS_READY_NO_GROWTH_YET` | 9 |
| `GROWTH_PARTIAL` | 391 |
| `GROWTH_READY` | 120 |

**Verificación cruzada real**: identidad resuelta = 690+34+9+391+120 = **1.244**, que coincide exactamente con 555 (EE. UU.) + 689 (Europa) = **1.244** — ninguna empresa contada dos veces, ninguna perdida.

Desglose por país (empresas con identidad real, top 15): EE. UU. 555 de 9.200 filas censadas bajo el país `USA` (34 fundamentales parciales, 8 fundamentales listos sin crecimiento, 383 crecimiento parcial, 111 crecimiento listo, 19 solo identidad) — **hallazgo real, no un bug nuevo**: otras 700 filas del censo llevan la etiqueta de país distinta `US` (en vez de `USA`) y hoy quedan las 700 en `NO_DATA_YET`, ninguna con cobertura real todavía; es una inconsistencia de etiquetado ya presente en el censo `v2.38A`, no algo introducido por este bloque. Alemania 413/413 solo identidad, Francia 53/53 solo identidad, Países Bajos 44/44 solo identidad, Reino Unido 40/40 (1 con fundamentales listos — Kingfisher plc, sin crecimiento posible por ser periodo único), Suiza 29/29 solo identidad, **Austria 20/20 con evidencia real de crecimiento** (9 `GROWTH_READY`, 8 `GROWTH_PARTIAL`, 3 quedan en `IDENTITY_ONLY` porque su Bilanz real tiene valores `null` — el mismo hueco de esquema BWG/VAG ya documentado en `v2.38AI`/`v2.38AK`).

## Qué significa esto para el objetivo del usuario

De 43.089 empresas, hoy el pipeline tiene **algo real** para 1.244 (2,9%) y **crecimiento interanual real y calculable** para solo 140 (120 completas + parte de las 391 parciales) — casi todas de EE. UU., más las 9 austriacas. Esto no es un fallo de este bloque: es la fotografía honesta de dónde está realmente el proyecto, exactamente lo que el usuario pidió ver. El resto de la hoja de ruta (más países, más fuentes de fundamentales/precio, y finalmente el contexto geopolítico) es lo que irá reduciendo la columna `NO_DATA_YET`, fila a fila, de forma visible en esta misma matriz cada vez que se reconstruya.

## Salvaguardas

Sin red (todas las fuentes ya eran ficheros locales de fases anteriores), sin scoring, sin ranking, sin recomendaciones, sin fase 9C. 7 pruebas offline nuevas, todas con datos sintéticos.

**Estado del bloque: `COMPLETED_GLOBAL_COVERAGE_MATRIX_V1_NOT_RECOMMENDATIONS`.** Primera pieza real de la arquitectura de "las 43.000 empresas con banderas honestas" — se reconstruirá automáticamente cada vez que una fase futura (más países, más fuentes) añada cobertura real, sin tocar la lógica de este script salvo para añadir la nueva fuente a la lista de entradas.
