# v2.38AD — France registry lookup (real)

Fecha: 2026-09-06. Alcance: investigar y, si es posible, ejecutar un localizador de perfil oficial para los 53 activos franceses (identidad ya resuelta al 100% en v2.38AB). Además, esta ejecución motivó una corrección real en el limpiador de nombres compartido (v2.38AB), útil para todos los países, no solo Francia.

## Corrección previa: limpieza de marcadores de tipo de acción (v2.38AB)

Al probar los nombres resueltos de Francia contra el registro real, se descubrió que Xetra añade, además del sufijo de denominación ya conocido, un **marcador de tipo de acción** (`INH.`/`INHABER` = acción al portador, `O.N.` = sin valor nominal, `NOM.`/`NAM.` = acción nominativa) — presente en casi todos los nombres franceses, alemanes, suizos y austriacos resueltos (`"NEXANS INH."`, `"SANOFI SA INHABER"`, `"HERMES INTERNATIONAL O.N."`, `"MICHELIN  NOM."`, `"NOVARTIS NAM.     SF 0,49"`). Corregido en `resolve_europe_full_identity_xetra_source_v2_38ab.py`: nuevo patrón `SHARE_TYPE_SUFFIX_RE`, aplicado iterativamente junto al ya existente `DENOMINATION_SUFFIX_RE` (ampliado para incluir el marcador de franco suizo "SF") hasta que el nombre queda estable. **La matriz canónica de 689 activos se regeneró** — sigue 689/689 resuelto por ISIN, solo mejora el nombre usado para la búsqueda en cada registro. Verificado sin ninguna discrepancia de ISIN contra los tres resultados ya publicados (GB/Irlanda/España); España muestra 7 nombres cosméticamente mejorados (esperado, documentado, no un error).

## Investigación real de vías oficiales francesas

- **API Entreprise, endpoint "actes et bilans" (INPI)**: real, gratuito, devuelve la lista de actos y **cuentas anuales en PDF** (más metadatos en XML) — pero está **restringido a administraciones públicas** vía autorización DataPass. No accesible para este proyecto.
- **`recherche-entreprises.api.gouv.fr`** ("API Recherche d'entreprises", construida por Etalab/data.gouv.fr sobre el RNE + Sirene): **totalmente pública, sin cuenta, sin clave, actualizada casi en tiempo real** (confirmado en vivo: un registro de ejemplo mostraba una actualización de la misma semana). Esta es la fuente usada en este bloque — pero **no ofrece ninguna cifra financiera**, solo identidad/estado.

## Resultado real (ejecutado sin credencial)

`scripts/run_europe_france_registry_lookup_v2_38ad.py` — mismo patrón fail-closed ya probado (nombre normalizado exacto + estado activo único), adaptado a los campos franceses (SIREN, `etat_administratif`, `nature_juridique`).

| | Cantidad |
|---|---|
| Activos de entrada | 53 |
| **Perfiles confirmados** | **18** |
| Sin resolver — sin coincidencia exacta | 23 |
| Sin resolver — **ambigüedad real: varias empresas activas con el mismo nombre exacto** | **12** |

**Hallazgo nuevo, real y distinto de los patrones ya vistos en GB/Irlanda**: 12 de los 53 activos (Crédit Agricole, Hermès International, Safran, Accor, LVMH, Vinci, Renault, Orange, Valneva, Amundi, Scor, Michelin) tienen **más de una empresa activa con el nombre exacto idéntico** en el registro francés — comprobado en vivo para Hermès International (dos SIREN activos, uno "gran empresa" de 1957, otro "PYME" de 1995) y TotalEnergies SE (dos SIREN activos, aunque uno de ellos incluye texto adicional entre paréntesis que evita que ambos coincidan exactamente, por lo que ese caso sí resuelve). El emparejador fail-closed **nunca elige uno basándose en el tamaño o la categoría de empresa** — eso sería exactamente el tipo de adivinanza que causó la colisión real SCT/BMT en GB — así que estas 12 quedan honestamente sin resolver, no forzadas.

**Nota de confianza sobre TotalEnergies SE (resuelto)**: la coincidencia única y activa que resolvió (SIREN 934082975) tiene un código de forma jurídica (`nature_juridique` 9220) distinto del que cabría esperar para la sociedad europea matriz cotizada (el otro candidato, con paréntesis, lleva el código 5800 = "Société européenne" y no coincide por el texto extra). Se registra como resuelto porque cumple estrictamente la regla fail-closed (único candidato activo con coincidencia exacta), pero se documenta esta incertidumbre con transparencia en vez de presentarla como una certeza absoluta.

## Fundamentales: confirmado fuera de alcance

Ninguna de las dos vías investigadas permite obtener cifras financieras reales: `recherche-entreprises.api.gouv.fr` no las tiene en absoluto, y el único endpoint que sí las tiene (API Entreprise "actes et bilans") está restringido a administraciones públicas. No se construye ningún script de descarga de cuentas para Francia.

## Pruebas offline

- `tests/qa_europe_full_identity_xetra_source_v2_38ab.py` — ampliado con 1 caso nuevo para la limpieza de marcadores de tipo de acción (5 casos en total).
- `tests/qa_europe_france_registry_lookup_v2_38ad.py` — 5 casos: dry-run sin red, confirmación de que no se requiere credencial, coincidencia exacta activa (caso real Nexans), **reproducción exacta del caso real de ambigüedad Hermès International**, normalización con puntos/apóstrofos y sufijo legal.

```
.venv/Scripts/python.exe tests/qa_europe_full_identity_xetra_source_v2_38ab.py
PASS: v2.38AB-europe-full-identity-xetra-source/no-jurisdiction-filter/regression-vs-gb/ambiguous-isin/no-network
.venv/Scripts/python.exe tests/qa_europe_france_registry_lookup_v2_38ad.py
PASS: v2.38AD-france-registry-lookup/dry-run-gate/no-credential-needed/fail-closed-name-match/real-duplicate-ambiguity
```

## Seguridad y alcance

- Red real usada: `recherche-entreprises.api.gouv.fr` (público, sin cuenta, sin credencial) — 53 llamadas de búsqueda, más un puñado de sondeos de investigación previos.
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Sin descarga de documentos, sin extracción de cifras financieras (confirmado fuera de alcance por restricción administrativa, no por falta de intento).
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | España | Alemania | **Francia** |
|---|---:|---:|---:|---:|---:|
| Activos | 40 | 17 | 15 | 413 | **53** |
| Identidad resuelta | 40/40 | 17/17 | 15/15 | 413/413 | **53/53** |
| Registro oficial gratuito accesible | Sí | Sí | No | No | **Sí (parcial)** |
| Perfiles confirmados | 29 | 8 | — | — | **18** |
| Fundamentales reales accesibles | Sí (2 empresas) | No (confirmado) | — | — | **No (confirmado, restricción administrativa)** |

**Estado del bloque: `COMPLETED_EUROPE_FRANCE_REGISTRY_LOOKUP_PARTIAL_NO_FINANCIALS_ACCESS`.** Registro: 18/53 confirmados, con un hallazgo real y nuevo (ambigüedad genuina por nombres duplicados activos) que se suma al ya conocido patrón de nombres abreviados. Fundamentales: confirmado sin vía de acceso para este proyecto.
