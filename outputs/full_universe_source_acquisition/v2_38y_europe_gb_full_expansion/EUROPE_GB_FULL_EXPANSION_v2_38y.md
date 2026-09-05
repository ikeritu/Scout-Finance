# v2.38Y — Europe GB Companies House + iXBRL, full 40-company expansion (real)

Fecha: 2026-09-05. Alcance: ampliar la recolección real de v2.38V/W a las 40 identidades GB ahora correctamente resueltas vía la fuente Xetra (corrección post-v2.38X), en vez de las 3-4 identidades parciales (2 de ellas erróneas) con las que se trabajó antes. Misma lógica, mismos scripts base (copiados a versión `_v2_38y`, sin tocar el historial de V/W), ejecutados a escala real con la credencial real del usuario.

## Por qué scripts nuevos, no una reejecución de V/W

`run_europe_companies_house_lookup_v2_38v.py` y `fetch_europe_accounts_documents_v2_38w.py`/`normalize_europe_ixbrl_fundamentals_v2_38w.py` ya produjeron un resultado real, documentado y comiteado (3-4 identidades, con la corrección de identidad ya señalada con avisos). Reescribir esos ficheros para apuntar a las 40 identidades habría mezclado ese historial con este resultado nuevo. En su lugar: tres scripts nuevos (`*_v2_38y.py`), mismo contrato conceptual, un nuevo `config/europe_gb_full_expansion_contract_v1.json`, escribiendo a un directorio de salida propio (`v2_38y_europe_gb_full_expansion/`).

## Parte 1 — Companies House, 40 identidades reales

**Dos correcciones reales encontradas y corregidas durante esta ejecución, antes de aceptar el resultado final** (ninguna estaba en el alcance original de "solo ampliar la escala"):

1. **`DENOMINATION_SUFFIX_RE` no cubría un espacio entre el marcador de divisa y el valor** (p. ej. `"BARCLAYS PLC      LS 0,25"`, `"UNILEVER PLC     LS -,035"`, `"RENTOKIL INITIAL  LS 0,01"`) — el regex original solo limpiaba el sufijo cuando estaba pegado sin espacio. Corregido en `resolve_europe_gb_identity_xetra_source_v2_38v.py` (regex ahora acepta `\s*` entre el marcador y el valor); la matriz de identidad de v2.38V se regeneró (offline, sin red, mismo fichero fuente Xetra) — **sigue siendo 40/40 resuelto por ISIN**, solo mejora la limpieza cosmética del nombre usado para la búsqueda en Companies House. Prueba de regresión añadida a `qa_europe_gb_identity_xetra_source_v2_38v.py`.
2. **`normalize()` rompía el sufijo legal cuando Companies House registra el nombre con puntos entre cada letra** — confirmado en vivo: el nombre real registrado de BP es **"BP P.L.C."**, no "BP PLC". La sustitución de puntuación por un espacio convertía "P.L.C." en tres palabras sueltas ("P", "L", "C") que nunca coincidían con el token de sufijo "PLC". Corregido en `run_europe_companies_house_lookup_v2_38y.py`: los puntos se eliminan directamente (no se sustituyen por espacio) antes de convertir coma/paréntesis/guion en espacio. Prueba de regresión añadida reproduciendo exactamente "BP P.L.C." vs. "BP PLC".

**Resultado real, tras ambas correcciones (ejecutado con la credencial real del usuario, fail-closed, sin adivinar ningún nombre):**

| Iteración | Perfiles confirmados | Sin resolver |
|---|---:|---:|
| Antes de corregir el regex de denominación | 18/40 | 22 |
| Tras corregir el regex de denominación | 28/40 | 12 |
| Tras corregir `normalize()` (puntos en el sufijo) | **29/40** | **11** |

Las 11 restantes son casos genuinamente distintos, no forzados:
- Nombres Xetra abreviados de forma no mecánica (p. ej. `"LLOYDS BKG GRP"` en vez de "Lloyds Banking Group plc", `"RECKITT BENCK."` en vez de "Reckitt Benckiser Group plc", `"NATWEST GR.PLC"`, `"INTERCONT.H."`, `"ROLLS ROYCE HLDGS"`, `"LEGAL GENL GRP PLC"`, `"SMITH + NEP."`, `"VIDAC PHARMA HLDG PLC"`) — ninguna heurística adicional de expansión de abreviaturas se ha intentado, porque intentarlo sería exactamente el tipo de adivinanza que causó el error real de v2.38V (colisión SCT/BMT). Correctamente sin resolver.
- Empresas que probablemente no están constituidas en UK pese a cotizar en Londres (`"SENSATA TECHN.HLDG"`, `"ROYALTY PHARMA OA"`, `"BRIT.AMER.TOBACCO"` — este último con nombre abreviado además) — Companies House solo indexa entidades registradas en UK; correctamente sin resolver, sin inventar un número de empresa.

**Publicado en git**: `europe_companies_house_lookup_matrix_v2_38y.csv` (identidad + estado societario, nunca cifras financieras) y su resumen agregado. Nunca se ha visto ni registrado el valor de la credencial — verificado con el mismo escaneo de secretos que en V/W.

## Parte 2 — descarga y clasificación de documentos de cuentas (29 empresas confirmadas)

Mismo comportamiento que v2.38W: se consulta el historial de filings de cada una de las 29 empresas confirmadas y se descarga el ZIP real solo cuando el formato disponible es `application/zip` (paquete ESEF/iXBRL); todo lo demás queda bloqueado con motivo explícito, nunca forzado a OCR.

**Resultado real: 1/29 con paquete iXBRL real (KINGFISHER, filing 2026-07-01); 28/29 solo tienen PDF** (`accounts_format_not_parseable_pdf_only`). Esto es consistente con el hallazgo ya documentado en v2.38W: la mayoría de los grandes PLC británicos depositan solo PDF en Companies House, no iXBRL, incluso aunque presenten iXBRL a HMRC por separado (fuera del alcance de la API pública de documentos de Companies House).

## Parte 3 — normalización iXBRL real (Kingfisher plc)

Mismo extractor específico de 14 conceptos IFRS que v2.38W (contexto no dimensional únicamente, período más reciente únicamente). **13/14 conceptos extraídos** para el ejercicio cerrado a 2026-01-31 (`ifrs-full:ProfitLossAttributableToOwnersOfParent` no está etiquetado en el documento — registrado honestamente como `not_tagged_in_document`, nunca inventado).

**Verificación cruzada real antes de aceptar el resultado** (misma disciplina que Softcat en v2.38W):
- Activos = Pasivos + Patrimonio ✓ **exacto**.
- Activo corriente + Activo no corriente = Activo total ✓ **exacto**.
- Pasivo corriente + Pasivo no corriente = Pasivo total ✓ **exacto**.
- Activos netos = Patrimonio ✓ **exacto**.

Las cuatro identidades contables cuadran de forma exacta con datos reales — segunda confirmación independiente (tras Softcat) de que el extractor de v2.38W/Y funciona correctamente a escala real, no solo en el caso original con el que se construyó.

## Pruebas offline

- `tests/qa_europe_companies_house_lookup_v2_38y.py` — 5 casos: dry-run sin red, bloqueo sin credencial, coincidencia exacta vs. ambigua a escala (13 filas sintéticas), continuación tras error HTTP sin fuga de credencial, y la **prueba de regresión del sufijo con puntos** ("BP P.L.C." vs "BP PLC").
- `tests/qa_europe_accounts_document_fetch_v2_38y.py` — 3 casos, incluida continuación del run tras un error HTTP intercalado entre un PDF bloqueado y un ZIP descargado.
- `tests/qa_europe_ixbrl_fundamentals_v2_38y.py` — 4 casos, mismo fixture sintético que v2.38W (misma regresión del contexto dimensional).
- `tests/qa_europe_gb_identity_xetra_source_v2_38v.py` — ampliado con 1 caso nuevo para el fix del regex de denominación con espacio.

```
.venv/Scripts/python.exe tests/qa_europe_gb_identity_xetra_source_v2_38v.py
PASS: v2.38V-gb-identity-xetra-source/ticker-collision-regression/ambiguous-isin/no-network
.venv/Scripts/python.exe tests/qa_europe_companies_house_lookup_v2_38y.py
PASS: v2.38Y-companies-house-lookup-full-expansion/blocked-by-default/fail-closed-name-match/at-scale/no-credential-leak
.venv/Scripts/python.exe tests/qa_europe_accounts_document_fetch_v2_38y.py
PASS: v2.38Y-accounts-document-fetch/dry-run-gate/pdf-vs-zip-classification/continues-past-errors/no-credential-leak
.venv/Scripts/python.exe tests/qa_europe_ixbrl_fundamentals_v2_38y.py
PASS: v2.38Y-ixbrl-normalizer/dimensional-context-regression/number-cleaning/latest-period-only/no-guessing
```

## Seguridad y alcance

- Red real usada: Companies House (con la credencial real del usuario, nunca vista ni registrada por este proyecto) — 40 llamadas de búsqueda + 29 de historial de filings + 29 de metadatos de documento + 1 descarga real de ZIP.
- El documento real (XHTML de Kingfisher) y el JSONL con los valores extraídos quedan fuera de git (`.gitignore`), igual que en v2.38W; solo se publican identidad/estado societario (sin cifras) y el informe de cobertura agregado (recuentos, sin cifras).
- Ninguna cuenta creada por este proyecto; la credencial es la misma ya creada y guardada por el usuario en v2.38V.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen

| | v2.38V (parcial, pre-corrección) | v2.38Y (esta ejecución) |
|---|---:|---:|
| Identidades de entrada | 40 (solo 4 resueltas, 2 erróneas) | 40 (40 resueltas, correctas vía ISIN) |
| Perfiles Companies House confirmados | 3 | **29** |
| Empresas con paquete iXBRL real | 1 (Softcat) | 1 (Kingfisher) — **2 en total entre ambos bloques** |
| Empresas con fundamentales IFRS extraídos y verificados contablemente | 1 (Softcat, 14/14) | 1 (Kingfisher, 13/14) |

**Estado del bloque: `COMPLETED_EUROPE_GB_FULL_EXPANSION_PARTIAL_IXBRL`.** Identidad y estado societario ampliamente resueltos (29/40, hasta el límite honesto que permite el fail-closed sin adivinar abreviaturas Xetra); iXBRL real sigue siendo escaso (2/70 activos totales de v2.38S entre Softcat y Kingfisher) porque la mayoría de grandes PLC británicos simplemente no depositan iXBRL en Companies House. No se ha reconstruido la matriz de candidatos de v2.38X en este bloque — eso queda para una decisión explícita posterior del usuario, igual que se dejó pendiente tras la corrección de identidad.
