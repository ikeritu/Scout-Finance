# v2.38BH — Ampliación de Finlandia: 127/133 identidad y sector real, fundamentales confirmados sin vía para grandes cotizadas

Fecha: 2026-09-07. Alcance: tercer paso de la decisión "decide qué hacer con las 3.766 empresas nuevas" — extender Finlandia con las 133 empresas nuevas que reveló `v2.38BC` bajo `country=FI`, prácticamente toda la Bolsa de Helsinki (Nasdaq Helsinki): Nokian Renkaat, UPM-Kymmene, Fortum, Kesko, Sampo, Finnair, Marimekko, Stora Enso, y decenas más.

## Identidad y sector: 127/133, reutilizando el script ya existente sin ningún cambio

`scripts/fetch_europe_finland_tol_v2_38au.py` (búsqueda PRH por nombre, ya construido y probado en las 5 empresas originales) se reejecutó directamente con las 133 candidatas nuevas como entrada, sin modificar una sola línea. **Resultado: 127/133 resueltas (95,5%)** con Business ID real y código TOL/sector en inglés — la tasa de acierto más alta de cualquier búsqueda de identidad por nombre en toda esta sesión, muy por encima del 36-59% visto en Cboe Europe sin filtro de país.

Ejemplos reales verificados: Aspocomp Group (1547801-5, "Manufacture of electronic components"), Anora Group (1505555-7, "Distilling, rectifying and blending of spirits"), Bittium (1004129-5, "Activities of holding companies"), Boreo (0116173-8, "Wholesale of information and communication equipment").

**6 sin resolver, cada una con motivo real, nunca adivinado**: 4 ambiguas (Alma Media, Aspo, eQ, Lassila & Tikanoja — múltiples entidades distintas con Business ID distinto comparten el nombre, correctamente sin forzar una elección) y 2 sin coincidencia exacta (F-Secure Oyj, Verkkokauppa.com Oyj — probablemente una diferencia de puntuación/formato entre el nombre de Cboe y el registrado en PRH).

## Fundamentales: hallazgo real y confirmado — la API XBRL de PRH no cubre a las grandes cotizadas

Antes de construir cualquier pipeline, se investigó si existe una fuente real de estados financieros para Finlandia (nunca antes verificado — `v2.38AU` solo atacó sector, no fundamentales). Hallazgo real: PRH publica una **API XBRL separada** (`avoindata.prh.fi/opendata-xbrl-api/v3`), gratuita, oficial, CC-BY 4.0, indexada por el mismo Business ID — confirmada en vivo como real y con datos (10.272 empresas con estados financieros para el ejercicio 2024-12-31).

Pero una prueba en vivo con 7 de las empresas grandes de esta ampliación (Nokian Renkaat, Kesko, Marimekko, Fortum, Talenom, Kemira, Ponsse) dio **0/7 con datos XBRL disponibles** — confirmado también para Nokia Oyj de forma independiente. Conclusión real: este sistema cubre la declaración digital simplificada pensada para pymes (taxonomía `oytp_gaap_ind`), no las grandes cotizadas que reportan bajo NIIF/ESEF por una vía distinta — mismo patrón estructural ya visto en la Centrale des Bilans de Luxemburgo (donde ArcelorMittal y Spotify tampoco aparecían), pero aquí con una tasa de fallo total (100%) para la población que interesa a este proyecto.

**No se construye ningún pipeline de fundamentales para Finlandia** — sería repetir un patrón ya confirmado negativo para exactamente el tipo de empresa que este proyecto prioriza (grandes cotizadas con potencial de crecimiento).

## Qué NO hace este bloque

No extrae ningún fundamental financiero — confirmado sin vía real para las empresas grandes. No reconstruye `v2.38AL` ni `v2.38AM` todavía. No investiga las 6 empresas sin resolver ni reintenta con un método distinto.

## Pruebas offline

Reutiliza sin cambios las pruebas ya existentes de `v2.38AU` (7 casos, sin modificaciones al script). No se necesitan pruebas nuevas — misma lógica, mismo código, distinta lista de entrada.

## Seguridad y alcance

Sin credenciales (PRH es gratis, sin cuenta). Red real usada para 133 búsquedas de empresa (con paginación real cuando fue necesaria, mismo comportamiento ya probado) y 8 consultas de prueba a la API XBRL (Nokia + 7 empresas). Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `PARTIAL_EUROPE_CBOE_FINLAND_EXTENSION_FUNDAMENTALS_NO_VIABLE_SOURCE_FOR_LARGE_CAPS`.** Identidad y sector reales para 127/133 empresas (95,5%) — el mejor resultado de identidad de toda la campaña de Cboe Europe. Fundamentales confirmados sin vía gratuita para las grandes cotizadas que interesan a este proyecto, un hallazgo negativo real, no una tarea pendiente.
