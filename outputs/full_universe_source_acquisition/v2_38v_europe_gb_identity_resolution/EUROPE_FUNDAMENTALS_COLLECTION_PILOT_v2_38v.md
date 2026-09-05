# v2.38V — Europe fundamentals collection pilot (real)

> **⚠️ CORRECCIÓN POSTERIOR (2026-09-05, mismo día)**: la Parte 1 de este documento (resolución de identidad vía OpenFIGI) contenía **2 identificaciones erróneas** (`SCT`→"Softcat PLC" debería ser SSE PLC; `BMT`→"Braime" debería ser British American Tobacco), causadas por confundir un mnemonic interno de Xetra con un ticker real de LSE. Corregido con una resolución basada en el fichero fuente oficial de Xetra (40/40 resueltas, 0 ambiguas). Ver `CORRECTION_XETRA_SOURCE_IDENTITY_v2_38v.md` para el detalle completo — **léelo antes de confiar en los nombres de empresa de este documento**.

Fecha: 2026-09-05. Alcance: intentar, de verdad, la primera recolección real de fundamentales de Europa, respetando el gate de v2.38U (ninguna de las tres rutas estaba `READY`). Dos partes, ambas con evidencia real, ninguna simulada.

## Contexto: por qué no se tocó el piloto de proveedor (EODHD, 617 activos)

Antes de escribir código se investigó el precio real de EODHD Fundamentals: plan mínimo €59,99/mes; el plan gratuito da 20 llamadas/día y cada consulta de fundamentales cuesta 10, es decir máx. 2 consultas/día — inviable para 617 activos, y choca directamente con la postura ya establecida del usuario de no usar fuentes de pago (ver memoria del proyecto). **Decisión: no se construye ningún runner para esta ruta.** Queda como limitación de política, no de credencial, hasta que el usuario decida lo contrario.

## Parte 1 — Resolución real de identidad GB vía OpenFIGI (ejecutada)

Los 40 activos GB de v2.38S comparten el mismo `company_name` placeholder (`"UKI0"`) que ya se documentó para Irlanda en v2.38T — sin nombre real, ninguna búsqueda en Companies House es posible. Se resolvió vía OpenFIGI `/v3/mapping` (gratuito, sin cuenta, ya aprobado y usado en v2.33C/H/P), fail-closed: solo cuenta como resuelto si OpenFIGI devuelve datos y todos los registros coinciden en el mismo nombre.

**Dos hallazgos reales, confirmados con sondeos en vivo antes de construir el resolutor final:**
1. El parámetro correcto es `exchCode="LN"` (Bloomberg), no `micCode="XLON"` — un sondeo con `micCode` devolvió una empresa francesa no relacionada (Guillemot Corporation) para el ticker "GUI", sin ningún filtrado real de bolsa aplicado.
2. Varios tickers llevan un sufijo numérico espurio heredado del mismo feed roto de Deutsche Börse Xetra (p. ej. "RIO1", "RTO1") que no coincide con ningún ticker real de LSE — pero al quitar el sufijo, resuelven a empresas reales y conocidas ("RIO"→RIO TINTO PLC, "RTO"→RENTOKIL INITIAL PLC). Esta normalización se aplica **solo como reintento**, después de que el ticker original falle, y cada registro indica explícitamente qué forma (`raw` o `stripped_trailing_digits`) produjo la coincidencia — nunca se sustituye en silencio.

**Resultado real (4 llamadas de red, sin credencial):**

| | Cantidad |
|---|---|
| Activos de entrada | 40 |
| **Resueltos** | **4** (BRAIME (TF & JH)-A NON VOTG, RIO TINTO PLC, SOFTCAT PLC, RENTOKIL INITIAL PLC) |
| Sin resolver | 36 — `no_openfigi_record_for_ticker_on_lse` |

**Decisión: `COMPLETED_EUROPE_GB_IDENTITY_RESOLUTION_PARTIAL`.** Una tasa de resolución del 10% es honesta, no decepcionante por sí misma: refleja que el ticker es, en muchos casos, el único campo superviviente utilizable de un feed con datos ya confirmados como corruptos en múltiples columnas (nombre, y ahora también parcialmente el propio ticker). No se ha intentado ninguna heurística adicional de normalización más allá de las dos confirmadas con evidencia real, para no sobreajustar a suposiciones no verificadas.

## Parte 2 — Localizador de perfil en UK Companies House (ejecutado con credencial real del usuario)

Companies House confirma ser una API REST **gratuita** (verificado contra la documentación oficial antes de escribir código: sin coste por llamada, límite de uso justo de 600 peticiones/5 min). El usuario creó su propia cuenta gratuita en `developer.company-information.service.gov.uk` y guardó la clave como `SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY` — este proyecto no creó la cuenta ni ha visto el valor de la clave en ningún momento.

`scripts/run_europe_companies_house_lookup_v2_38v.py`: bloqueado por defecto, exige `--execute` + la credencial; busca por nombre normalizado (quita sufijos legales "PLC"/"LIMITED"/"LTD"), fail-closed (solo acepta una única empresa activa con coincidencia exacta de nombre normalizado, nunca ambigua). Autenticación HTTP Basic con la clave como usuario — la clave real nunca se lee más allá de esa cabecera, nunca se registra ni se escribe en ningún fichero de salida (verificado en la prueba offline y re-confirmado tras la ejecución real: escaneo de secretos sobre los ficheros de salida sin coincidencias).

**Deliberadamente fuera de alcance de este bloque**: la descarga y el parseo de los documentos de cuentas (PDF/iXBRL) — ver v2.38W.

**Resultado real (ejecutado 2026-09-05, con la credencial del usuario):**

| Ticker | Nombre resuelto (OpenFIGI) | Resultado en Companies House |
|---|---|---|
| RIO1 | RIO TINTO PLC | **Confirmado** — nº 00719885, activa, constituida 1962-03-30 |
| SCT | SOFTCAT PLC | **Confirmado** — nº 02174990, activa, constituida 1987-10-07 |
| RTO1 | RENTOKIL INITIAL PLC | **Confirmado** — nº 05393279, activa, constituida 2005-03-15 |
| BMT | BRAIME (TF & JH)-A NON VOTG | Sin resolver — `no_exact_normalized_name_match` |

**3/4 perfiles reales confirmados.** El caso sin resolver es honesto, no un fallo: el nombre que da OpenFIGI para BMT es una descripción de clase de acción ("-A NON VOTG" = acciones A sin voto), no la razón social exacta registrada en Companies House — el emparejamiento fail-closed rechazó correctamente forzar una coincidencia en vez de adivinar. `sic_codes` queda vacío en los tres confirmados porque el endpoint `/search/companies` no lo devuelve (solo lo daría una llamada adicional a `/company/{number}`, no implementada en este bloque).

Estos son los **primeros datos reales de fundamentales-adyacentes de Europa** de todo el proyecto (identidad corporativa confirmada contra un registro oficial) — todavía no son cifras financieras (eso exige el parser iXBRL de v2.38W).

## Pruebas offline

- `tests/qa_europe_gb_identity_resolution_v2_38v.py` — 5 casos: gate dry-run sin red, coincidencia exacta vs. desacuerdo, reintento de sufijo numérico correctamente etiquetado (nunca silencioso), sin llamada de reintento cuando no hay forma alternativa, escritura atómica sin ficheros `.tmp` residuales.
- `tests/qa_europe_companies_house_lookup_v2_38v.py` — 4 casos: dry-run sin red, bloqueo real sin credencial, coincidencia exacta activa vs. ambigua, continuación tras error HTTP + verificación de que la cabecera de autenticación nunca expone la clave en texto plano.

```
.venv/Scripts/python.exe tests/qa_europe_gb_identity_resolution_v2_38v.py
PASS: v2.38V-gb-identity-resolution/dry-run-gate/fail-closed-exact-match/trailing-digit-fallback-not-silent/no-network
.venv/Scripts/python.exe tests/qa_europe_companies_house_lookup_v2_38v.py
PASS: v2.38V-companies-house-lookup/blocked-by-default/fail-closed-name-match/atomic-write/no-credential-leak
```

## Próximo paso real: v2.38W

Con identidad y número de empresa confirmados para 3 activos, el siguiente paso natural es obtener el historial de filings (`/company/{number}/filing-history`) y descargar el documento de cuentas más reciente para intentar el parseo de iXBRL — la pieza deliberadamente diferida de este bloque. Requiere probarse contra un documento real antes de darse por fiable.

## Seguridad y alcance

- Red real usada: OpenFIGI (sin cuenta, sin credencial, 4 llamadas) + Companies House (con la credencial del usuario, nunca vista ni registrada por este proyecto, 4 llamadas).
- Ninguna cuenta creada por este proyecto en ningún momento; la cuenta y la clave de Companies House las creó y guardó el usuario.
- Sin descarga de documentos de cuentas, sin fundamentales reales, sin normalización, sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: parcial, con evidencia real en ambas partes.** Identidad GB: 4/40 resuelta vía OpenFIGI. Companies House: **3/4 perfiles reales confirmados** con la credencial del usuario — los primeros datos reales de identidad corporativa de Europa de todo el proyecto.
