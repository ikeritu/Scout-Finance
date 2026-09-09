# v2.38BW — Fase 9C, bloque 3 de 3: la pantalla real "🏆 Ranking global (experimental)"

Fecha: 2026-09-08. Alcance: bloque final de la Fase 9C, autorizada explícitamente por el usuario. Lleva el resultado real de `v2.38BV` (el primer score real de todo este proyecto) a la propia app, sin tocar nada del producto fijo de 50 activos.

## Decisión de diseño: un tercer módulo independiente, no una extensión de los otros dos

`src/ui_v2_37/global_universe.py` documenta explícitamente que es "never a score or a ranking". `src/ui_v2_37/repository.py` está protegido por su propio contrato fijo de 50 activos. En vez de forzar el ranking real nuevo dentro de cualquiera de los dos, se creó `src/ui_v2_37/global_ranking.py` — una tercera lente independiente, de solo lectura, fail-closed, siguiendo el mismo patrón ya usado por `global_universe.py` (`_rooted()` contra traversal de rutas, `GlobalRankingData` con `available`/`error` en vez de una excepción). A diferencia del botón "Actualizar", este módulo no dispara ningún recálculo desde la app — `v2.38BV` es una computación más pesada (dos bloques previos de Fase 9C) que se ejecuta deliberadamente desde la línea de comandos, no desde un clic.

## Qué muestra la pantalla real

Métricas reales (Ranking principal, Comparabilidad parcial, Revisión requerida, Cobertura insuficiente, Sin adaptador todavía), una tabla filtrable por país y confianza del ranking principal, una "ficha rápida" por empresa seleccionada (score, confianza, cobertura real, posición, puntuación real por pilar, el resumen textual determinista ya generado por `explain_result()`, y un enlace de conveniencia a Google Finance), y tres desplegables con la población completa de comparabilidad parcial, revisión requerida (con el motivo real: margen anómalo o entidad financiera) y sin adaptador todavía.

**Watchlist real reutilizada sin cambios**: `src/ui_v2_37/watchlists.py` ya era genérico por `asset_id` (nunca atado al contrato de 50 activos), así que añadir una empresa del ranking nuevo a una watchlist ya existente funciona sin ningún cambio en ese módulo.

## Verificación real en vivo

Se lanzó la app real y se verificó en el navegador: las 5 métricas coinciden exactamente con el fichero real de `v2.38BV` (318/373/124/270/26), la tabla del ranking principal muestra correctamente 318 empresas reales ordenadas por posición (Compugen Ltd. en el puesto 1, score real 82,59), la ficha rápida de esa misma empresa muestra sus 5 pilares reales (Calidad 95,1, Riesgo 58,2, Valoración 74,3, Tendencia 77,4) y su resumen textual real generado por el motor. Los tres desplegables muestran población real reconocible: NVIDIA Corp y Palantir Technologies en comparabilidad parcial (score alto, 50% de cobertura real por no tener precio todavía — correctamente fuera del ranking principal por el propio diseño del motor, no un error), American Coastal Insurance Corporation con el motivo real "Entidad financiera" en revisión requerida, y Allegro.eu SA (Luxemburgo) en "sin adaptador todavía". Se probó de verdad añadir una empresa nueva (Compugen Ltd., `U00597`) a una watchlist real ya existente que solo contenía un activo del producto antiguo (`P155`, JPX) — el fichero JSON real confirma ambos activos conviviendo correctamente en la misma lista, demostrando la interoperabilidad real entre el espacio de `asset_id` nuevo y el sistema de watchlist ya existente. La entrada de prueba se retiró después de la verificación, sin dejar rastro en los datos reales del usuario.

## Qué NO hace este bloque

No toca `repository.py`, `app.py`'s "Ranking experimental" ni ningún dato del producto fijo de 50 activos — verificado que sigue funcionando exactamente igual. No recalcula nada desde la app — solo lee el fichero real ya generado por `v2.38BV` desde la línea de comandos. No añade ninguna recomendación, predicción ni conexión a broker — mismo lenguaje de disclaimer ya usado en el resto de la app.

## Pruebas offline

4 casos nuevos en `tests/qa_ui_global_ranking_v2_38bv.py`: fichero de resultados ausente (nunca un crash, mensaje real), carga real de una fila sintética con marca de tiempo real, fichero corrupto manejado sin crash, y protección contra traversal de rutas fuera del repositorio — mismo patrón ya usado por `qa_ui_global_universe_v2_38al.py`.

## Seguridad y alcance

Sin red disparada por esta pantalla. Sin credenciales nuevas. Sin scoring nuevo calculado desde la app — solo lectura del resultado real ya calculado por `v2.38BV`. Mismo lenguaje de disclaimer que el resto del producto: nunca una recomendación de inversión, nunca una predicción.

**Estado del bloque: `COMPLETED_UI_GLOBAL_RANKING`.** Con esto se cierran los tres bloques de la Fase 9C: el primer score real de este proyecto (`v2.38BU`+`v2.38BV`) es ahora visible y consultable desde la app real, con lo que falta siempre marcado, nunca oculto — mismo criterio que todo el proyecto.
