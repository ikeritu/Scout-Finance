# v2.38BV — Fase 9C, bloque 2 de 3: el motor de scoring real, aplicado por primera vez

Fecha: 2026-09-08. Alcance: bloque 2 de la Fase 9C, autorizada explícitamente por el usuario. Aplica el motor de scoring ya validado del producto antiguo de 50 activos (`scripts/scoring_engine/core.py`, contrato `config/scoring_factor_contract_v1.json`, v2.35A3 — confirmado por lectura directa del código, NO los ficheros sueltos y desconectados `combined_scoring_v1.py`/`filter_stage2/3.py`) al universo elegible completo definido por `v2.38BO`.

## Cero metodología nueva inventada

Mismo contrato de 14 factores, mismos pesos, misma normalización por percentil (midrank), mismo mecanismo de renormalización de pesos por activo con el mismo suelo real de cobertura (0,50), mismos umbrales de confianza (HIGH ≥0,80, MEDIUM ≥0,65, LOW ≥0,50), mismos criterios de desempate. `core.build_raw_factors()`, `core.percentile_scores()`, `core.score_assets()` y `core.explain_result()` se importan y se llaman sin ninguna modificación — el único trabajo real de este bloque es construir los dos diccionarios de entrada que el motor ya espera (fundamentales, precios), con el vocabulario exacto de nombres de factor que su contrato ya usa.

## Dos poblaciones reales puntuadas en esta primera ejecución

- **Origen EE. UU.** (555 originales vía `v2.38G` + 538 nuevas de Cboe Europe secundaria vía `v2.38BK` + Joby Aviation vía `v2.38BA`): `net_margin`/`return_on_assets`/`return_on_equity`/`revenue_yoy_growth`/`net_income_yoy_growth` de esos tres ficheros, `operating_margin`/`eps_basic`/`book_value_per_share` de `v2.38BU`. El histórico real de precio (`v2.38I`, descubierto durante la construcción de este bloque — 554 ficheros CSV reales de precio diario, uno por empresa) solo existe para las 555 originales, así que momentum/riesgo/valoración solo aplican ahí — el resto cae por el propio mecanismo de renormalización ya existente del motor (solo calidad+crecimiento), el mismo mecanismo que ya usaba TWSE en el producto antiguo.
- **Austria** (`v2.38X` para las razones financieras + `v2.38AK` para el crecimiento, 17 empresas reales): la única población no estadounidense con un conjunto real de ratios calidad+crecimiento ya calculado. Sin precio, sin EPS/valor contable — mismo conjunto reducido de factores que las empresas de EE. UU. sin precio.

**Luxemburgo (26 empresas) y la única empresa real de Reino Unido todavía no tienen un adaptador de ratios/crecimiento construido en este bloque** — no se puntúan aquí, y quedan explícitamente reportadas como `NOT_YET_SCORED_NO_ADAPTER`, nunca calladas ni con un score inventado.

## Un segundo bug real encontrado y corregido antes de puntuar nada

Al construir el fichero real de precios para EE. UU. se descubrió `v2.38I` (histórico real de precio diario por empresa, 554 CSV reales) — no formaba parte del plan original, que preveía reutilizar solo el fichero ya agregado `v2.38H`. Usar el histórico diario real y la propia función `price_factors()` del motor antiguo (reutilizada sin cambios) en vez de reconstruir `volatility_12m` a mano resultó ser más fiel al método original, así que se adoptó directamente.

Más importante: al construir los datos reales de Austria se comprobó el propio fichero real de `v2.38AL` (la matriz de cobertura) y se encontró que **carga el texto literal "AST0" como `company_name`** para las 17 empresas austriacas nuevas — un marcador de posición real, no el nombre real de la empresa. Esto significa que el heurístico de entidad financiera de `v2.38BO` nunca tuvo un nombre real contra el que comprobar para esta población entera, y **dos entidades financieras reales pasaron sin marcar**: **Erste Group Bank AG** y **UNIQA Insurance Group AG**. Se corrigió en este bloque reaplicando el mismo heurístico real (importado sin cambios desde `build_global_scoring_eligibility_v2_38bo.is_financial_institution`) contra el nombre real de `v2.38X`, y enrutando ambas a `REVIEW_REQUIRED` mediante el mismo mecanismo de exclusiones que el motor ya usa — el mismo texto de motivo (`financial_institution_requires_separate_factor_contract`) que el producto antiguo ya usa para su propio banco real (P178). El bug real de "AST0" en `v2.38AL`/`v2.38BO` **no se corrige en su sitio** — mismo criterio ya aplicado por `v2.38BQ` (no alterar retroactivamente fases ya completadas y ya citadas); corregirlo allí y volver a ejecutar `v2.38BO` queda como una decisión real y explícita, pendiente, no tomada aquí.

## Resultado real

Universo real de entrada: 1.111 empresas (1.088 elegibles + 23 entidades financieras de `v2.38BO`).

| Estado real | Empresas |
|---|---:|
| `ELIGIBLE_PARTIAL` (ranking principal, confianza HIGH/MEDIUM) | **318** |
| `PARTIAL_COMPARABILITY` (puntuada, confianza LOW, fuera del ranking principal) | 373 |
| `REVIEW_REQUIRED` (99 por margen fuera de ±300%, 25 por entidad financiera — 23 de `v2.38BO` + 2 recuperadas de Austria) | 124 |
| `BLOCKED` (cobertura real por debajo del 50%) | 270 |
| `NOT_YET_SCORED_NO_ADAPTER` (Luxemburgo + Reino Unido, sin adaptador todavía) | 26 |
| **Total** | **1.111** |

**Determinismo real verificado**: la misma ejecución dos veces produce un JSON byte a byte idéntico.

Primeras 10 posiciones reales del ranking principal (318 empresas, confianza HIGH/MEDIUM): Compugen Ltd. (82,59), Aurinia Pharmaceuticals (80,40), Affirm Holdings (79,06), Comstock Holding Companies (77,88), BUUU Group (77,70), Air T (77,54), Kanzhun Limited (75,72), ACADIA Pharmaceuticals (75,41), Airbnb (75,17), Enact Holdings (74,63) — resultado cuantitativo experimental, nunca una recomendación.

## Qué NO hace este bloque

No es una recomendación de inversión, ni una predicción, ni una señal de trading — mismo lenguaje de explicación ya usado en el producto antiguo (`explain_result`, reutilizado sin cambios). No construye ningún modelo de factores alternativo para las 25 entidades financieras — quedan `REVIEW_REQUIRED`, sin score, igual que P178 en el producto antiguo; nunca se aplican ratios industriales a un banco. No puntúa Luxemburgo ni Reino Unido todavía. No modifica el motor real (`scripts/scoring_engine/core.py`), su contrato, ni ninguna fase ya completada (`v2.38AL`, `v2.38BO`, `v2.38F`, `v2.38G`).

## Pruebas offline

7 casos en `tests/qa_global_research_ranking_v2_38bv.py` (no repiten las pruebas ya reales del propio motor en `tests/qa_scoring_engine_v2_35.py`, que se re-ejecutan y siguen pasando sin cambios): una empresa de EE. UU. con solo fundamentales reales se puntúa correctamente, una empresa de Austria se puntúa desde sus ficheros reales de ratios y crecimiento con el nombre real de `v2.38X` (no el marcador "AST0"), el caso real de recuperación de Erste Group Bank AG confirma que una entidad financiera real nunca se puntúa con ratios industriales, una entidad financiera ya marcada por `v2.38BO` queda excluida, una empresa sin adaptador (Luxemburgo) queda explícitamente `NOT_YET_SCORED_NO_ADAPTER`, una empresa con precio real recibe factores reales de momentum/riesgo, y una prueba dedicada de determinismo confirma una salida byte a byte idéntica en dos ejecuciones.

## Seguridad y alcance

Cero red nueva — todo el cálculo es local, sobre datos ya reales y ya recolectados por fases anteriores. Sin credenciales. Sin recomendaciones, sin ejecución de operaciones, sin conexión a broker.

**Estado del bloque: `COMPLETED_GLOBAL_RESEARCH_RANKING_EXPERIMENTAL`.** Bloque 2 de 3 de la Fase 9C. Sigue `v2.38BW`: la pantalla real "🏆 Ranking global" en la propia app.
