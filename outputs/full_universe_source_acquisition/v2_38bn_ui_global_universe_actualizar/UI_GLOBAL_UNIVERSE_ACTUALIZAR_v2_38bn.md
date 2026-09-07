# v2.38BN — el botón "Actualizar": primera pieza real de "camino a producto"

Fecha: 2026-09-08. Alcance: el usuario pidió explícitamente empezar por el botón "Actualizar" en la UI, la primera pieza del "camino a producto" identificado en el roadmap. Hasta hoy, todo el trabajo de identidad/fundamentales/crecimiento de este proyecto vivía únicamente en ficheros de investigación (CSV/JSON) generados por scripts de línea de comandos — ninguna app mostraba nada de esto.

## Estado previo de la UI, investigado antes de escribir ningún código

Investigación real (agente de exploración) antes de tocar nada: la app existente es 100% Streamlit, local, sin ningún backend API ni framework web adicional (no hay Flask/FastAPI/Django/React/Vue en el proyecto real). Hay tres generaciones: `app.py` (v1.1C, congelada), `app_v2_28.py` (v2.32F, congelada), y `app_v2_37.py` + `src/ui_v2_37/` (la más reciente, 8 pantallas en español: Inicio, Universo, Ranking experimental, Ficha de empresa, Comparador, Watchlist, Informes, Ayuda). Ninguna de las tres leía nunca `global_coverage_matrix_v2_38al.csv.xz` — todas seguían ancladas al dataset canónico fijo de 50 activos (`src/ui_v2_37/repository.py`, con `_validate_assets()` que **lanza una excepción si el número de activos no es exactamente 50**).

La única mención explícita de "botón actualizar" en todo el código es el propio docstring de `build_global_coverage_matrix_v2_38al.py`: *"press an 'actualizar' button and see the full 43,000-company universe, with companies lacking real data plainly marked 'sin datos todavía' rather than hidden"* — una intención de arquitectura documentada, nunca antes diseñada ni conectada.

## Decisión de diseño: nunca tocar el dataset fijo de 50 activos

Dado que `repository.py` está deliberadamente protegido por un contrato de conteo exacto (50 activos), y que la matriz de las 43.089 es un dataset completamente distinto en escala y en naturaleza (identidad/fundamentales/crecimiento/precio por empresa, nunca un score ni un ranking), esta pieza se construyó como un módulo **totalmente nuevo y separado** (`src/ui_v2_37/global_universe.py`), reutilizando el shell visual ya existente (`ui.py`: `apply`/`banner`/`heading`) pero sin tocar ni una línea de `repository.py`. Misma disciplina que el resto del proyecto: nunca modificar código protegido por un contrato fijo, construir algo nuevo al lado.

## Qué hace el botón realmente, y qué decide deliberadamente no hacer

El botón "Actualizar" re-ejecuta, con el mismo intérprete de Python que ya está corriendo la app (`sys.executable`), los dos únicos builders puros y sin red que ya existían: `build_global_coverage_matrix_v2_38al.py` y `build_global_macro_geopolitical_context_v2_38am.py`. Ambos leen únicamente ficheros ya recolectados en fases anteriores y los reensamblan — **nunca descargan ni consultan nada nuevo de ninguna fuente externa**. Esto es una frontera de seguridad deliberada: el botón nunca dispara una recolección de datos en vivo desde la UI, que sigue siendo una decisión manual y explícita por fuente, consistente con la disciplina de todo el proyecto de no automatizar la recolección de datos sin supervisión explícita.

La nueva pantalla ("🌍 Universo global (43.089)") muestra: fecha de la última actualización (hora real del fichero), métricas agregadas reales (empresas con identidad, con fundamentales, con crecimiento), un desglose por los 9 estados reales de `overall_coverage_status`, y una tabla filtrable/buscable por nombre, ticker, país y estado — con las empresas sin ningún dato marcadas explícitamente como "Sin datos todavía", nunca ocultas, exactamente como pedía el docstring original.

## Verificación real en vivo (no solo pruebas offline)

Se lanzó la app real (`streamlit run app_v2_37.py`, mismo lanzador que ya usa el proyecto) y se verificó en el navegador: la pantalla nueva carga las 43.089 filas reales, las métricas coinciden exactamente con el fichero real (5.034 con identidad, 1.111 con fundamentales, 1.028 con crecimiento), la búsqueda por "Moderna" encuentra correctamente la fila real `U09211` con su identidad y fundamentales reales de hoy (`v2.38BI`/`v2.38BK`), y el botón "Actualizar" ejecuta la reconstrucción real (1,7 s para la matriz de cobertura) y refresca la vista con la marca de tiempo actualizada.

**Hallazgo real durante esta misma verificación en vivo, corregido de inmediato**: la primera versión de la rama nueva de `build_row()` (añadida hoy mismo para las 538 empresas de EE. UU. de `v2.38BI`/`BK`) nunca fijaba el campo `country` — al pulsar "Actualizar" de verdad, esas 538 filas perdieron su etiqueta de país (`US`→vacío), un hallazgo real solo visible al ejecutar el pipeline completo en vivo, no solo con pruebas offline sintéticas. Corregido añadiendo `row["country"] = "US"` a esa rama, con una prueba nueva que usa la forma real del censo (país vacío para estos activos solo-Cboe) en vez de un país ya relleno que ocultaba el bug.

## Qué NO hace este bloque

No toca el dataset de 50 activos ni su ranking experimental. No añade scoring, ranking ni recomendaciones sobre las 43.089 empresas — solo muestra su estado real de cobertura. No dispara ninguna recolección de datos en vivo. No pagina más allá de las primeras 2.000 filas filtradas en la tabla (con aviso explícito) — una limitación de rendimiento de la tabla de Streamlit, no de los datos.

## Pruebas offline

7 casos nuevos en `tests/qa_ui_global_universe_v2_38al.py`: matriz ausente (nunca un crash, mensaje que invita a pulsar Actualizar), carga real de una matriz sintética con marca de tiempo real, fichero corrupto manejado sin crash, la reconstrucción ejecuta ambos scripts en el orden correcto con el mismo intérprete, la reconstrucción se detiene si la matriz de cobertura falla (nunca construye el contexto geopolítico sobre una base rota), una excepción real de subproceso se captura y se reporta sin tumbar la app, y protección contra traversal de rutas fuera del repositorio. Además, 2 pruebas ya existentes de `qa_global_coverage_matrix_v2_38al.py` se corrigieron para usar la forma real del censo y así detectar el bug de país en blanco descrito arriba (23 pruebas en total en ese fichero).

## Seguridad y alcance

Sin red disparada por el botón (los dos scripts reconstruidos son puramente locales). Sin credenciales nuevas. Sin scoring, ranking, recomendaciones ni fase 9C. `.claude/launch.json` añadido para poder previsualizar la app durante el desarrollo (no forma parte de la app en sí).

**Estado del bloque: `COMPLETED_UI_GLOBAL_UNIVERSE_ACTUALIZAR`.** Primera pieza real de "camino a producto": el trabajo de más de 40 bloques de investigación ya no vive solo en ficheros — es visible y actualizable desde la app real, con lo que falta siempre marcado, nunca oculto.
