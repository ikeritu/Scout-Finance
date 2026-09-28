# v2.46E — deduplicar el ranking global por registrante SEC

Estado: `GLOBAL_RANKING_DEDUPLICATION_COMPLETED`. No modifica v2.38BV (los ficheros que citan las auditorías v2.38BX/v2.41D/v2.43A/v2.44A siguen bit a bit idénticos); añade un fichero de salida nuevo y opcional, y hace que la app lo prefiera cuando existe.

## El problema
El ranking v2.38BV puntúa y clasifica cada fila del censo elegible de forma independiente. 44 de las 1.111 empresas puntuadas son la misma empresa cotizando dos veces (mismo registrante/CIK de la SEC: la matriz original en EE. UU. y su cotización secundaria en Cboe Europe, ya detectadas por el flag de unicornios v2.38BT). El ranking principal las contaba dos veces: 3 de ellas ocupaban directamente una posición en el ranking principal de 318.

## La solución
`scripts/build_global_research_ranking_v2_38bv.py` acepta ahora `--dedupe-by-cik-from` (por defecto lee `outputs/full_universe_source_acquisition/v2_38bt_global_unicorn_flag/global_unicorn_flag_v2_38bt.csv`). Con esa opción:
- Excluye del universo puntuable a las 44 cotizaciones no primarias (se queda con la de mejor prioridad de fuente, igual que ya decide v2.38BT).
- Cada una recibe su propia fila con estado nuevo `DUPLICATE_LISTING`, motivo `duplicate_listing_of_<primary>_same_sec_registrant` y sin score (nunca desaparece silenciosamente).
- Escribe una salida separada con su propio prefijo `v2_46e` en `outputs/full_universe_source_acquisition/v2_46e_global_research_ranking_deduplicated/`.
- Sin la opción, el comportamiento y los ficheros son exactamente los de v2.38BV — verificado byte a byte tras cada cambio.

## Resultado real
| | v2.38BV (sin deduplicar) | v2.46E (deduplicado) |
|---|---|---|
| Universo puntuado | 1.111 | 1.067 |
| Ranking principal | 318 | 315 |
| Comparabilidad parcial | 373 | 354 |
| Revisión requerida | 124 | 121 |
| Cobertura insuficiente | 270 | 251 |
| Sin adaptador | 26 | 26 |
| Cotización duplicada | — | 44 |

El top 10 del ranking principal no cambia. Una empresa (Bel Fuse Inc. — Class B, duplicado de la Class A) sale del top 50; otra entra al ascender un puesto.

## App
`src/ui_v2_37/global_ranking.py` prefiere el fichero v2.46E cuando existe localmente y usa v2.38BV si no (fail-closed, nunca inventa ni recalcula). La pantalla "🏆 Ranking global (experimental)" muestra un aviso de qué fuente está activa, una pestaña "Cotizaciones duplicadas" cuando corresponde, y el motivo de cada duplicado enlaza a la empresa primaria legible (ticker y nombre), no a su ID interno.

## Cómo generarlo
```
python scripts/build_global_research_ranking_v2_38bv.py --dedupe-by-cik-from
```

## Pruebas
`tests/qa_global_research_ranking_v2_38bv.py` (parseo del flag v2.38BT, modo deduplicado, ficheros v2.38BV intactos); `tests/qa_ui_global_ranking_v2_38bv.py` (preferencia del fichero deduplicado, fallback, error propio sin fallback silencioso si está corrupto).
