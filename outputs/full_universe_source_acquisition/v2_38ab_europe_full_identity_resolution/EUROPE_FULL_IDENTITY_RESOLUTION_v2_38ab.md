# v2.38AB — Generalización: resolución de identidad real para las 689 empresas europeas (real)

Fecha: 2026-09-05. Alcance: generalizar el método de identidad Xetra/ISIN ya probado tres veces (GB 40/40, Irlanda 17/17, España 15/15) a la totalidad de los **689 activos europeos** dentro del alcance de recolección de fundamentales (v2.38Q), en vez de seguir tratando un país a la vez.

## Por qué generalizar ahora

Al revisar la matriz de resolución de casa de cotización (v2.38N, 22.578 filas), se confirmó que el mismo placeholder (`company_name` = código de segmento de mercado de Xetra, p. ej. "GER0", "FRA0", "UKI0") afecta a **1.420 activos en total**, de los cuales 707 son "NAM0" — correctamente `OUT_OF_SCOPE_NON_EUROPE` (no son activos europeos, no se tocan) — y los **689 restantes son exactamente el universo europeo dentro de alcance de v2.38Q** (`HOME_EXCHANGE_RESOLVED`). De esos 689, **solo 72 habían sido tratados** hasta hoy (GB 40, Irlanda 17, España 15) — los otros **617 nunca habían tenido su identidad resuelta**, porque estaban enrutados únicamente al piloto de proveedor de pago EODHD (bloqueado por política) y la resolución de identidad se trató, por error de alcance, como si dependiera de esa ruta de fundamentales. No depende: resolver quién es realmente cada empresa es gratis y útil por sí mismo, sin importar si sus fundamentales resultan alcanzables gratis o no.

## Resultado real

`scripts/resolve_europe_full_identity_xetra_source_v2_38ab.py` — mismo método ya probado (Mnemonic → ISIN/Instrument contra el fichero fuente de Deutsche Börse Xetra ya local, sin red, fail-closed), aplicado sin filtro de jurisdicción sobre las 689 filas de `europe_fundamentals_asset_routes_v2_38q.csv`.

**689/689 resueltos, 0 ambiguos, 0 sin resolver.** Desglose real por país:

| País | Resueltos | Ruta de fundamentales original |
|---|---:|---|
| Alemania (DE) | **413** | eodhd_fundamentals (bloqueado por política) |
| Francia (FR) | 53 | eodhd_fundamentals |
| Países Bajos (NL) | 44 | eodhd_fundamentals |
| Reino Unido (GB) | 40 | uk_companies_house_filings (ya tratado, v2.38V/Y) |
| Suiza (CH) | 29 | eodhd_fundamentals |
| Italia (IT) | 22 | eodhd_fundamentals |
| Dinamarca (DK) | 21 | eodhd_fundamentals |
| Austria (AT) | 20 | eodhd_fundamentals |
| Irlanda (IE) | 17 | issuer_filings_manual_review (ya tratado, v2.38Z) |
| España (ES) | 15 | cnmv_issuer_filings (ya tratado, v2.38AA) |
| Bélgica (BE) | 6 | eodhd_fundamentals |
| Finlandia (FI) | 5 | eodhd_fundamentals |
| Suecia (SE) | 4 | eodhd_fundamentals |

Ejemplos reales confirmados entre las 617 empresas nunca antes identificadas: United Internet, Baader Bank, Nexans, Crédit Agricole, Teleperformance, Hermès International, KPN, Heineken, Koninklijke Philips, STMicroelectronics, Zurich Insurance Group, Novartis, Roche Holding, Generali, Mediobanca, BPER Banca, FinecoBank, Carlsberg, A.P. Møller-Mærsk, Genmab, Strabag, Raiffeisen Bank International, Porr, Erste Group Bank — todas empresas reales, verificables, grandes cotizadas europeas.

## Verificación de consistencia con el trabajo ya publicado

Antes de aceptar el resultado, se comparó fila por fila contra los tres resultados ya publicados y comiteados (GB v2.38V, Irlanda v2.38Z, España v2.38AA): **0 discrepancias en las 72 filas compartidas** — mismo ISIN, mismo nombre resuelto, en las tres. Esto confirma que la generalización es exactamente el mismo algoritmo aplicado a más datos, no una reimplementación divergente. Prueba de regresión dedicada (`test_regression_reproduces_already_published_gb_result_exactly`) reproduce este mismo caso de forma determinista en el conjunto de pruebas offline.

## Qué NO hace este bloque (alcance deliberadamente limitado)

- **No investiga ningún registro oficial nuevo.** Alemania, Francia, Países Bajos, Suiza, Italia, Dinamarca, Austria, Bélgica, Finlandia y Suecia tienen ahora identidad real, pero **ningún registro mercantil ni fuente de fundamentales se ha investigado todavía** para ninguno de estos 10 países. Eso queda para bloques futuros, país a país, con la misma disciplina de investigación previa ya aplicada a GB/Irlanda/España (comprobar si existe un API oficial gratuito antes de escribir ningún script, nunca scraping, nunca pago).
- **No cambia el bloqueo de política sobre los 617 activos EODHD.** Su ruta de fundamentales sigue bloqueada por la postura ya establecida de no usar fuentes de pago — esto solo resuelve quiénes son, no cómo conseguir sus cifras.
- **No reconstruye la matriz de candidatos (v2.38X).** Esa matriz sigue dependiendo de fundamentales reales extraídos (hoy solo Kingfisher), no de identidad por sí sola.

## Pruebas offline

`tests/qa_europe_full_identity_xetra_source_v2_38ab.py` — 4 casos: resolución sin filtro de jurisdicción en una sola pasada (DE/NL/DK simultáneos), **regresión exacta contra el resultado ya publicado de GB**, mnemonic ausente, ISIN ambiguo.

```
.venv/Scripts/python.exe tests/qa_europe_full_identity_xetra_source_v2_38ab.py
PASS: v2.38AB-europe-full-identity-xetra-source/no-jurisdiction-filter/regression-vs-gb/ambiguous-isin/no-network
```

## Seguridad y alcance

- Sin red: la resolución usa exclusivamente el fichero fuente ya local y ya versionado en git desde una fase anterior (v2.14c).
- Sin credenciales.
- Sin scoring, ranking, recomendaciones, fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED_EUROPE_FULL_IDENTITY_RESOLUTION`.** 689/689 activos europeos con identidad real confirmada (frente a 72/689 antes de este bloque) — el mayor salto de cobertura de identidad de todo el proyecto en una sola ejecución, sin ningún coste ni riesgo (offline, sin credenciales, mismo método ya verificado tres veces). El siguiente paso natural es decidir con qué país seguir para investigar registros/financials (Alemania, con 413 activos, es el más grande con diferencia).
