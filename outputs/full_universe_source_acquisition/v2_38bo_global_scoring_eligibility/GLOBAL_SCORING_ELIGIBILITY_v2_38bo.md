# v2.38BO — el subconjunto elegible para scoring, definido y auditable, cero puntuaciones calculadas

Fecha: 2026-09-08. Alcance: el usuario pidió explícitamente "define el subconjunto elegible para scoring" — el primer punto del "camino a producto" que quedaba por decidir tras construir el botón "Actualizar" (`v2.38BN`). Este bloque responde a esa pregunta para las 43.089 empresas del censo, sin calcular ningún score, ranking ni factor — solo clasifica quién tiene datos reales suficientes para que un futuro scoring tenga sentido.

## Por qué esto no es una respuesta binaria

El único precedente real de este proyecto es el producto antiguo de 50 activos (`src/ui_v2_37/repository.py`), que ya distingue implícitamente varios niveles de confianza: `ELIGIBLE_PARTIAL` (JPX), `PARTIAL_COMPARABILITY` (TWSE, un solo periodo fundamental utilizable y precio sin ajustar), y `REVIEW_REQUIRED` (dos casos reales: un margen extremo real, y un banco que necesita un modelo de factores distinto). Este bloque generaliza exactamente esa misma disciplina a las 43.089 empresas, reutilizando la escalera identidad→fundamentales→crecimiento ya calculada por `v2.38AL` — sin recalcular nada, solo clasificando.

## Los cinco niveles reales, y por qué cada corte está donde está

1. **`ELIGIBLE_FULL`** — escalera de crecimiento completa (`GROWTH_READY`/`GROWTH_PARTIAL`) **y** una señal de precio real (`PRICE_FEATURES_READY` o `PRICE_FEATURES_PARTIAL` — un histórico parcial sigue siendo una señal real, distinto de "nunca intentado"), y sin indicio de ser una entidad financiera. Es el único nivel con los cinco pilares potenciales disponibles (calidad, crecimiento, valoración, precio/momentum, riesgo).

2. **`ELIGIBLE_PARTIAL_NO_PRICE`** — misma escalera completa de crecimiento, pero sin señal de precio real. Deliberadamente **no penalizado hasta la exclusión**: el hueco de precio en Europa (`v2.38AJ`, 0% de cobertura gratuita confirmada tras agotar 5 fuentes) y el hecho de que las 538 empresas nuevas de EE. UU. (`v2.38BI`/`BK`) nunca han sido investigadas para precio (a diferencia de un hallazgo negativo confirmado) son huecos estructurales de la fuente, no un defecto de la propia empresa — exactamente el mismo principio que ya justificó mantener `price_status` fuera de la escalera de `v2.38AL`.

3. **`ELIGIBLE_PARTIAL_SINGLE_PERIOD`** — fundamentales reales pero sin evidencia de crecimiento interanual (`FUNDAMENTALS_READY_NO_GROWTH_YET`/`FUNDAMENTALS_PARTIAL_NO_GROWTH_YET`). El nivel de confianza más bajo entre los elegibles: mismo espíritu que el trato ya dado a TWSE en el producto antiguo (un único periodo fundamental utilizable, comparabilidad parcial, nunca excluido pero tampoco en el ranking principal).

4. **`REVIEW_REQUIRED_FINANCIAL_INSTITUTION`** — cualquier empresa con datos reales suficientes (escalera de crecimiento o fundamentales) pero cuyo nombre coincide con un patrón real de entidad financiera (banco, bancorp/bancorporation, aseguradora, reaseguradora, caja de ahorros...). Mismo precedente ya establecido por el propio producto antiguo con P178 ("banco, requiere un contrato de factores específico") — nunca se aplican ratios industriales genéricos a un banco o aseguradora, ni se le excluye silenciosamente; queda marcado para un modelo de factores separado, todavía no construido.

5. **`NOT_ELIGIBLE`** — todo lo demás, conservando siempre el motivo real ya calculado por `v2.38AL` (nunca un rechazo genérico): sin ningún dato (`NO_DATA_YET`), solo identidad sin fundamentales, sin obligación legal de divulgación, bloqueado por un motivo real confirmado (cuota agotada, sin fuente para grandes cotizadas), o no ser una empresa operativa (compartimento de fondo).

## Limitación real y explícita: el heurístico de entidad financiera no es una clasificación SIC/NAICS verificada

Se basa en coincidencias de palabra completa en el nombre de la empresa (bank, bancorp\*, bancshares, insurance, assurance, reinsurance, savings, "financial group", "trust financial", thrift) — deliberadamente amplio, para minimizar falsos negativos a costa de alguna posible sobre-inclusión. Verificado en vivo que evita los falsos positivos obvios por subcadena ("Databank Inc", "Something Savingsware LLC" no coinciden, gracias al límite de palabra completa) y captura variantes reales de nomenclatura bancaria estadounidense ("Auburn National Bancorporation, Inc." vía `bancorp\w*`). Una entidad financiera real sin ninguna de estas palabras en su nombre (p. ej. "Ally Financial" no coincide, ya que "financial" solo no es suficiente para no disparar sobre cualquier "... Financial Inc" no bancario) quedará sin marcar — un hallazgo negativo honesto, documentado, no oculto.

## Resultado real

| Nivel | Empresas |
|---|---:|
| `ELIGIBLE_FULL` | 474 |
| `ELIGIBLE_PARTIAL_NO_PRICE` | 531 |
| `ELIGIBLE_PARTIAL_SINGLE_PERIOD` | 83 |
| `REVIEW_REQUIRED_FINANCIAL_INSTITUTION` | 23 |
| `NOT_ELIGIBLE` | 41.978 |
| **Total** | **43.089** |

**Elegibles en cualquier nivel (incluyendo revisión): 1.111 de 43.089 (2,6%)** — coincide exactamente con el número de empresas con fundamentales reales de `v2.38AL`. De esas, 474 (43%) tienen también precio real y quedan en el nivel de máxima confianza; 531 (48%) tienen la escalera completa de crecimiento pero ningún precio real todavía; 83 (7%) solo tienen un periodo fundamental; 23 (2%) son bancos/aseguradoras reales que necesitan su propio modelo antes de aplicarles cualquier ratio genérico.

## Qué NO hace este bloque

No calcula ningún score, ranking ni factor. No decide todavía qué hacer con `ELIGIBLE_PARTIAL_NO_PRICE` (¿se puntúa sin el pilar de precio, o se espera a tener precio real?) ni con `ELIGIBLE_PARTIAL_SINGLE_PERIOD` (¿se puntúa sin crecimiento, o se excluye del ranking principal como ya se hacía con TWSE?) — esas son decisiones de metodología de la Fase 9C, todavía no autorizada. No construye ningún modelo de factores para las 23 entidades financieras. No modifica `v2.38AL` ni ningún dato ya calculado — es una clasificación derivada, de solo lectura.

## Pruebas offline

9 casos nuevos en `tests/qa_global_scoring_eligibility_v2_38bo.py`: escalera completa con precio real (incluyendo precio parcial, que cuenta como señal real), escalera completa sin precio real (el caso real de las 538 empresas de EE. UU. y las 17 de Austria), solo fundamentales sin crecimiento, entidad financiera real enrutada a revisión en los tres estados de entrada posibles, el heurístico de nombre evita los falsos positivos por subcadena obvios, cada motivo de exclusión real se conserva textualmente, ninguna fila del censo se pierde, y bloqueo real si falta la matriz de entrada.

## Seguridad y alcance

Sin red, sin credenciales, sin scoring, sin ranking, sin recomendaciones, sin fase 9C. Solo lectura sobre `v2.38AL`, nunca lo modifica.

**Estado del bloque: `COMPLETED_GLOBAL_SCORING_ELIGIBILITY_DEFINED_NOT_SCORED`.** Responde por primera vez, con evidencia real y auditable para las 43.089 empresas, a la pregunta "¿quién podría entrar en un scoring real?" — sin construir ese scoring. Las decisiones de metodología que quedan (cómo tratar cada nivel parcial, cómo puntuar las entidades financieras) siguen siendo del usuario.
