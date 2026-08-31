# Scout Finance v2.33L — auditoría, inventario y alcance del universo operativo (Bloque A)

Fecha: 2026-08-31. Alcance: **auditoría + análisis documental sobre el censo canónico real (21.165 candidatos elegibles)**, sin descargas nuevas, sin credenciales, sin scoring ni ranking.

## A1 — Auditoría inicial

- `git status`: limpio salvo los 6 archivos locales protegidos (intactos, sin versionar).
- `main` alineada con `origin/main` (0 commits de diferencia en ambas direcciones); no hizo falta `git pull` (ya estaba al día).
- Commit base canónico `52947b42f4e28e58f166f231e2d2e3f876c60ba9` confirmado presente en el historial.
- Tag `v2.33D1_EODHD_PRICE_PILOT_VALIDATED` confirmado. No existen tags adicionales v2.33E–K (coherente: solo v2.33D1 se marcó con tag, según lo publicado).
- Las 12 carpetas `v2_33a` a `v2_33k` existen en `outputs/full_universe_source_acquisition/`, coherente con el historial publicado.
- Escaneo de secretos sobre archivos rastreados: sin coincidencias.
- No se detectó documentación contradictoria en los cierres ya publicados.

## A2 — Inventario de mercados (censo completo, no solo los 240 del piloto)

**Hallazgo central que corrige el punto de partida:** el piloto de 240 activos de v2.33D usó una muestra proporcional, pero **no representa correctamente el peso real de cada mercado** en el universo canónico de 21.165 candidatos elegibles (`eligibility_census_v2_33b2.csv.xz`, filtrado por `eligibility_decision_v2_33b2 == eligible_for_financial_enrichment_v2_33b2`). La distribución real es:

| Mercado | Candidatos elegibles | % del universo elegible |
|---|---:|---:|
| CBOE_EUROPE | 10.483 | **49,53 %** |
| JPX | 3.701 | 17,49 % |
| NASDAQ | 3.016 | 14,25 % |
| NYSE | 1.761 | 8,32 % |
| ASX | 1.271 | 6,01 % |
| TWSE | 696 | 3,29 % |
| NYSE American | 233 | 1,10 % |
| BVC | 3 | 0,01 % |
| Cboe BZX | 1 | 0,00 % |
| **Total elegible** | **21.165** | **100 %** |

Además, **1.782 candidatos adicionales quedan retenidos fuera de este total** por corrupción de esquema, sin contarse todavía como elegibles: Xetra (1.424 filas, `hold_provider_schema_xetra`) y SGX (358 filas, `hold_provider_schema_sgx`).

**Esto significa que Cboe Europe —ya bloqueado indefinidamente en v2.33H— representa casi la mitad de todo el universo elegible actual**, no una fracción menor como sugería el piloto de 240. Es el hecho más importante para calibrar honestamente cualquier cifra de "cobertura" en el cierre final de la fase 4 (Bloque H).

Inventario completo, reproducible, en `market_universe_inventory_v2_33l.csv` (generado por `scripts/build_market_universe_inventory_v2_33l.py`, que vuelve a calcular estas cifras directamente del censo canónico, sin cachear números).

## A3 — Clasificación del universo operativo gratuito

| Mercado | Estado operativo | Motivo |
|---|---|---|
| CBOE_EUROPE | `EXCLUDED_USER_DECISION` | v2.33H: `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`. Usuario descarta pago. Bloqueado indefinidamente salvo hallazgo gratuito incidental. |
| JPX | `CONDITIONAL` | v2.33G: `PASS_FOR_NEXT_CONTROLLED_PILOT` sobre 42/42 símbolos. Ampliar a los 3.701 candidatos exige confirmar licencia (Bloque C) y autorización explícita por superar 500 activos. |
| NASDAQ / NYSE / NYSE American / Cboe BZX | `CONDITIONAL` | Bloque EE. UU. (v2.33M), sin fuente evaluada todavía. |
| ASX | `EXCLUDED_NO_FREE_SOURCE` | v2.33J: `NO_FREE_SOURCE_FOUND`, confirmado de primera mano. |
| TWSE | `CONDITIONAL` | v2.33I: `PASS_FOR_NEXT_CONTROLLED_PILOT` sobre 8/8 activos. Ampliar a los 696 candidatos exige piloto ampliado (Bloque D) y autorización explícita por superar 500 activos. |
| BVC | `EXCLUDED_USER_DECISION` | v2.33K: inconcluso, cerrado por decisión del usuario. |
| Xetra | `BLOCKED_METADATA_CORRUPTION` | 1.424 filas retenidas por esquema sospechoso; no elegibles todavía. Reparación en Bloque E. |
| SGX | `BLOCKED_METADATA_CORRUPTION` | 358 filas retenidas por esquema sospechoso; no elegibles todavía. Reparación en Bloque E. |

**Importante:** ningún mercado se marca como "promovido a producción" en este cierre. JPX y TWSE solo superaron pilotos controlados y acotados (42 y 8 activos respectivamente); su condición de `CONDITIONAL` refleja exactamente eso, no una promoción.

## A4 — Gate de producto

**Decisión: opción 2 — MVP multifuente de alcance limitado**, no cobertura mundial gratuita.

La evidencia acumulada en v2.33D1–v2.33K y confirmada aquí con el censo completo hace que la opción 1 (insistir en cobertura mundial gratuita) sea previsiblemente inviable en el corto plazo: el bloque más grande del universo (Cboe Europe, 49,5 %) está bloqueado indefinidamente, y ASX (6,0 %) no tiene fuente gratuita conocida. No hay evidencia nueva que revierta estas conclusiones.

**Cobertura que se acepta perder (en el mejor escenario, si JPX/TWSE se amplían y EE. UU. se resuelve):** Cboe Europe (49,53 %) + ASX (6,01 %) = **55,54 % del universo elegible actual queda fuera de cobertura de precios gratuita**, más los 1.782 candidatos de Xetra/SGX retenidos por corrupción de esquema (pendientes del Bloque E, con precio todavía sin resolver incluso si se reparan los metadatos).

**Impacto sobre los 21.165 candidatos:** en el escenario más favorable (JPX y TWSE ampliados con éxito, EE. UU. resuelto con una fuente viable), la cobertura máxima teórica sería JPX (17,49 %) + NASDAQ/NYSE/NYSE American/Cboe BZX (23,67 %) + TWSE (3,29 %) = **44,45 %** de los 21.165 candidatos actuales. Esto es un techo teórico, no una cifra ya alcanzada — los tres bloques siguen pendientes de piloto ampliado o evaluación (Bloques B, C, D).

**Riesgo de sesgo geográfico:** el universo operativo gratuito, si se completan los bloques pendientes, quedaría concentrado en EE. UU., Japón y Taiwán. Excluye sistemáticamente Europa continental y el Reino Unido (vía Cboe Europe) y Australia — un sesgo geográfico real y explícito, no accidental, que debe quedar visible en cualquier informe o interfaz que use este universo en el futuro.

**Cómo se mostrará "sin cobertura" sin penalizar artificialmente a las empresas:** cualquier empresa en un mercado `EXCLUDED_*` o `BLOCKED_*` debe etiquetarse explícitamente como "sin fuente de precios gratuita disponible", nunca como una ausencia de datos indistinguible de un fallo de descarga o de una puntuación baja. Esta regla se traslada al contrato de datos común del Bloque F (`license_status` / `quality_status`).

**Requisitos exactos para añadir un nuevo mercado en el futuro:** (1) fuente con licencia documentada compatible con uso personal y almacenamiento derivado; (2) validación mediante piloto acotado (≤500 activos) con cero emparejamientos falsos; (3) cobertura ≥90 % de la ventana declarada; (4) esquema de identidad limpio (sin corrupción tipo Xetra/SGX); (5) documentación siguiendo el mismo patrón de este proyecto (STATUS.md + clasificación de evidencia).

## Seguridad y alcance

- No se ha creado ninguna cuenta, no se ha usado ninguna credencial, no se ha gastado dinero.
- No se ha descargado ningún precio nuevo; este cierre es análisis sobre datos ya existentes localmente (censo v2.33B2) más los cierres ya publicados.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No reabre ni modifica ninguna decisión ya publicada (v2.33D1–v2.33K).
- Decisión de este bloque: **`COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`** para el Bloque A (auditoría + alcance) — el proyecto adopta explícitamente un MVP multifuente de alcance limitado, no cobertura mundial.
- Siguiente paso: Bloques B (EE. UU.), C (JPX), D (TWSE), E (SGX/Xetra) — en curso o documentados a continuación en este mismo cierre.
