# Scout Finance v2.34D — arquitectura de adquisición de fundamentales (Bloque D, fase 5)

Fecha: 2026-08-31. Alcance: **solo código y pruebas offline en este cierre de bloque** — los dos adaptadores se construyen y se validan sin red real; la ejecución controlada contra los datos reales es el Bloque E, deliberadamente separado.

## Adaptadores construidos

Uno por fuente aprobada en v2.34B, cada uno independiente (sin lógica compartida de normalización — eso es el Bloque F) y con el mismo contrato de flags:

| Script | Fuente | Salida cruda |
|---|---|---|
| `scripts/download_jquants_fundamentals_v2_34d.py` | J-Quants `/v2/fins/summary` | `outputs/.../v2_34d_fundamentals_acquisition/jquants_fundamentals_raw_v2_34d/<pilot_id>.json` |
| `scripts/download_twse_mops_fundamentals_v2_34d.py` | MOPS opendata (4 CSV confirmados en v2.34B) | `outputs/.../v2_34d_fundamentals_acquisition/twse_mops_raw_v2_34d/{raw_snapshots/,<pilot_id>.json}` |

Ambas rutas están en `.gitignore` (añadido *antes* de que existiera ningún fichero, siguiendo la lección ya aplicada en las fases previas): son datos con licencia del proveedor, no trabajo derivado propio.

## Contrato de flags (idéntico en ambos adaptadores)

- `-h`/`--help`: descripción y opciones (autogenerado por `argparse`, probado manualmente).
- Bloqueado por defecto: sin `--execute`, el script imprime `BLOCKED: ...` y sale con código 2, sin tocar la red.
- `--execute`: única vía para autorizar una recolección real.
- `--resume`: documentado explícitamente en la ayuda; el comportamiento de reanudación (saltar lo ya descargado) es el comportamiento por defecto de ambos scripts, consistente con todos los downloaders previos del proyecto (v2.33G, v2.33I).
- Opcionales: `--limit`, `--asset-id` (repetible), `--output-dir`, `--request-delay`, `--max-retries`. `--from-date`/`--to-date` solo existen donde tienen sentido: **no se ofrecen** en el adaptador TWSE/MOPS porque la fuente no tiene consulta histórica (ver limitación de v2.34B) — ofrecerlos ahí habría sido una promesa falsa sobre lo que la fuente puede dar.

## Diferencia estructural entre las dos fuentes, y cómo el adaptador la refleja

- **J-Quants**: una llamada por activo (`code=<símbolo>`), igual que el patrón ya usado para precios en v2.33G. Reutiliza el mismo backoff de 429 (65s) y el mismo ritmo prudente (15s entre llamadas) porque el límite documentado de 5/min ya demostró ser más estricto en la práctica.
- **MOPS**: no existe una consulta por empresa — cada uno de los 4 ficheros CSV es una fotografía de **todas** las empresas cotizadas a la vez (confirmado en v2.34B y re-confirmado aquí con una llamada de sondeo real: `t187ap06_L_ci.csv`, 1.048 filas, codificación `utf-8-sig`, campos en chino tradicional citados literalmente). El adaptador descarga los 4 ficheros completos **una sola vez** (cacheados en `raw_snapshots/`, reutilizados en ejecuciones posteriores sin nueva llamada de red) y luego extrae solo las filas de nuestros 8 activos por `公司代號` (código de empresa) — nunca por coincidencia de nombre, para evitar el mismo riesgo de fuzzy-matching que el proyecto ya evita en todos los resolutores anteriores.

## Taxonomía de errores

`scripts/fundamental_adapters/errors.py` define el conjunto cerrado exigido por el encargo: `HTTP_ERROR`, `AUTH_ERROR`, `RATE_LIMIT`, `TIMEOUT`, `EMPTY_RESPONSE`, `IDENTITY_MISMATCH`, `SCHEMA_MISMATCH`, `PROVIDER_ERROR`, `LICENSE_BLOCK`, `UNKNOWN_ERROR`. `classify_http_error()` traduce un `HTTPError` real a uno de estos códigos por su status (429→`RATE_LIMIT`, 401/403→`AUTH_ERROR`, cualquier otro código→`HTTP_ERROR`). El adaptador J-Quants añade además `IDENTITY_MISMATCH` (el código devuelto por el proveedor no coincide con el solicitado) y `EMPTY_RESPONSE` (cero divulgaciones); el adaptador TWSE añade `SCHEMA_MISMATCH` (falta la columna `公司代號` esperada) y `EMPTY_RESPONSE` (ninguna fila de las 4 fotografías corresponde a ese código de empresa).

## Escritura atómica y sin fugas

Ambos escriben siempre a `<destino>.json.tmp` y hacen `Path.replace()` — nunca `open(path, "w")` directo, ni siquiera en el fichero de caché de MOPS. Ningún registro de fallo ni el informe final contiene la clave de J-Quants ni una URL completa: el sondeo real de este bloque (una llamada manual a `/v2/fins/summary`, fuera de los scripts) se hizo por separado para confirmar el esquema de respuesta, y su salida nunca se ha impreso ni guardado con la clave visible.

## Pruebas offline (Bloque D, parte de lo exigido también en el Bloque I)

`tests/qa_fundamental_acquisition_v2_34d.py` — 9 casos, sin red real (mock de `urllib.request.urlopen`), sin credencial real:

1. J-Quants bloqueado sin `--execute`, luego sin credencial.
2. Reanudación (activo ya descargado no genera llamada), escritura atómica, sin fuga de la clave fixture ni de URLs.
3. Continúa tras un error HTTP 500 en un activo y clasifica `HTTP_ERROR` con el status real.
4. Clasifica `IDENTITY_MISMATCH` (código devuelto no coincide) y `EMPTY_RESPONSE` (cero divulgaciones) por separado.
5. `--limit`/`--asset-id` filtran correctamente antes de la descarga.
6. TWSE bloqueado sin `--execute`.
7. Descarga + extracción de 2 activos reales de fixture, escritura atómica, ninguna URL en el informe.
8. La caché de instantáneas crudas evita una segunda llamada de red en una ejecución posterior.
9. Una columna esperada ausente en el CSV se clasifica `SCHEMA_MISMATCH` y bloquea toda la extracción sin generar ficheros parciales.

```
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/errors.py scripts/download_jquants_fundamentals_v2_34d.py scripts/download_twse_mops_fundamentals_v2_34d.py tests/qa_fundamental_acquisition_v2_34d.py
.venv/Scripts/python.exe tests/qa_fundamental_acquisition_v2_34d.py
PASS: v2.34D-fundamentals-acquisition/fail-closed/resumable/atomic-write/error-taxonomy/no-network/no-real-key
```

## Sondeo real mínimo (antes de fijar el diseño, sin credencial nueva)

- **MOPS**: 4 llamadas HTTP públicas sin credencial a `mopsfin.twse.com.tw/opendata/{t187ap03_L,t187ap06_L_ci,t187ap07_L_ci,t187ap17_L}.csv`, confirmando codificación (`utf-8-sig`, BOM presente), nombres de columna reales y escala (`t187ap06_L_ci` en miles de NTD, confirmado cruzando contra `t187ap17_L` que expresa ingresos en millones — la razón entre ambos es ~1000).
- **J-Quants**: 1 llamada real a `/v2/fins/summary?code=13010` reutilizando la cuenta ya existente (sin gasto, sin cuenta nueva), confirmando la forma real de la respuesta (`{"data": [...]}`, campos vacíos como cadena `""` cuando el proveedor no reporta esa línea para ese trimestre concreto — no `null` ni ausente).

## Seguridad y alcance

- Ninguna credencial nueva creada. La única credencial usada (J-Quants) ya existía de la fase 4 y solo se usó en el sondeo manual puntual descrito arriba, nunca impresa ni commiteada.
- Cero commits de datos crudos: las dos carpetas de salida cruda están en `.gitignore` desde antes de crearse.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED`.** Los adaptadores están listos para el Bloque E (piloto controlado real); ninguna descarga real de los 50 activos se ha ejecutado todavía en este bloque.
