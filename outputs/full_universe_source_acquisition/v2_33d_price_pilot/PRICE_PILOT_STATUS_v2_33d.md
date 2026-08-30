# Scout Finance v2.33D1 — cierre del piloto real de precios EODHD

Estado: **COMPLETED_NO_PROMOTION**. Piloto técnico cerrado y validado; EODHD **no se promociona** a producción en su plan gratuito. Scoring, rankings, recomendaciones y fase 5 siguen bloqueados.

## Qué se hizo en v2.33D1

Sobre la preparación de v2.33D (muestra de 240 activos, elegibilidad reforzada):

1. **Resolución determinista de símbolos** (`scripts/resolve_price_symbols_v2_33d.py`): 77/240 símbolos resueltos sin red ni ambigüedad, 1 excluido por no ser una empresa (`P014` / `ZSP.AX` / STANDARD & POORS INDICES AUSTRALIA → `excluded_non_company_index`), 162/240 siguen bloqueados por ambigüedad real (Cboe Europe, Japón, Colombia). `P230` (`MOG.B`) se resuelve correctamente como `MOG-B.US`.
2. **Descarga real autorizada** (`scripts/download_eodhd_price_pilot_v2_33d.py`), reanudable, fail-closed, con escritura atómica por activo y sin registrar nunca la URL completa ni el token en errores o informes: **77/77 activos descargados, 0 fallos, 0 omitidos** (`download_report_v2_33d.json`, no versionado).
3. **Validación local de los 77 históricos** (`scripts/build_price_pilot_collection_report_v2_33d.py` + `tests/qa_price_pilot_collection_v2_33d.py`): 77/77 archivos válidos, 0 errores de esquema, `P014` ausente de la colección, `P230` presente con `MOG-B.US`, coherencia OHLC y volumen no negativo verificados en todas las filas numéricas.
4. **QA sin red del descargador** (`tests/qa_price_pilot_downloader_v2_33d.py`): bloqueo sin `--execute`, bloqueo sin token, bloqueo ante símbolos ambiguos, aceptación de `resolved`/`resolved_deterministic`, omisión de archivos existentes sin llamar a la red, continuidad tras HTTP 404 simulado y tras esquema inválido simulado, informe reproducible, ausencia de URL/token en errores, escritura atómica, códigos de salida correctos. Todo con mocks, sin red y sin credenciales reales.

## Cifras confirmadas (reproducidas localmente)

- Activos esperados: 77 · válidos: 77 · errores de esquema: 0.
- Filas en bruto (incluyendo una fila de aviso del proveedor por activo): **18.791**.
- Observaciones numéricas válidas (excluyendo esa fila de aviso): **18.714**.
- Sesiones por activo: mínimo 102, máximo 253, mediana 250, media 243.04.
- Activos con menos de 200 sesiones: 5/77 (`P001`, `P005`, `P215`, `P217`, `P230`).
- Fecha mínima observada en toda la colección: 2025-09-01. Fecha máxima observada: 2026-08-28.
- Ningún activo alcanza 2021 o antes: **0/77**.
- Ventana solicitada en la descarga (`--from-date 2021-01-01`): 2.065 días naturales (~1.425 sesiones bursátiles estimadas).
- Cobertura de la mediana de sesiones frente a la ventana solicitada: **17.54%**.

> Corrección respecto a validaciones previas: la cifra de "18.791 observaciones totales" corresponde a filas en bruto e incluye una fila de aviso del proveedor por activo (77 filas), no datos de precio. El total de observaciones numéricas reales es 18.714. Ambas cifras están documentadas y son reproducibles ejecutando `tests/qa_price_pilot_collection_v2_33d.py` sobre la carpeta local (no versionada) de JSON.

Detalle completo, distribución por mercado y clasificación de la evidencia en `price_pilot_collection_report_v2_33d1.json` y `PRICE_PILOT_COLLECTION_REPORT_v2_33d1.md`.

## Por qué la profundidad histórica es la limitación central

Los 77/77 archivos descargados contienen, literalmente, como última fila de la respuesta EOD, el texto del propio proveedor:

> "Data is limited by one year as you have free subscription"

Esto es un **hecho observado** directamente en la respuesta de EODHD, no una suposición. Combinado con que ningún activo alcanza 2021 pese a solicitarse `from=2021-01-01`, y con que las fechas mínimas se agrupan en una ventana de aproximadamente un año antes de la fecha de ejecución, la **inferencia razonable** es que el plan gratuito de EODHD aplica una ventana móvil de ~1 año sobre el endpoint EOD, independientemente del parámetro `from` solicitado.

Lo que **no** está confirmado con esta evidencia:

- la regla exacta de corte (días naturales, sesiones bursátiles o fecha de aniversario fija);
- si un plan de pago de EODHD elimina o relaja este límite (no se ha probado; no está autorizado por este piloto);
- si los 5 activos con menos de 200 sesiones reflejan cotizaciones recientes, baja liquidez u otra causa — no se ha consultado ninguna fuente externa de fecha de salida a bolsa.

## Evaluación frente al contrato de v2.33C

v2.33C (`outputs/full_universe_source_acquisition/v2_33c_data_source_design/DATA_SOURCE_REPORT_v2_33c.md`) exige, para promocionar un proveedor a producción:

| Criterio v2.33C | Umbral | Resultado real (plan gratuito) | Cumple |
|---|---|---|---|
| Cobertura histórica de precios | ≥ 90% | ~17.5% (mediana de sesiones frente a la ventana solicitada) | **No** |
| Emparejamiento correcto de símbolos | ≥ 90% | 77/240 (32%) resueltos de forma determinista sobre la muestra completa; 162/240 siguen bloqueados | **No** |
| Cobertura fundamental | ≥ 75% | 0% (fundamentales fuera de alcance de este piloto, no se han solicitado) | No evaluado / **No cumplido** |
| Cero emparejamientos falsos | 0 | 0 confirmados entre los 77 símbolos resueltos | Sí |
| Licencia y retención documentadas | Documentado | Plan gratuito, sin confirmación escrita de términos de uso derivado/caché a largo plazo | **No** |

La ejecución técnica del piloto es limpia (0 fallos, 0 errores de esquema, cero emparejamientos falsos), pero **el proveedor, en su plan gratuito, no supera el piloto** frente a los umbrales que el propio proyecto se impuso en v2.33C.

## Decisión del gate

**`COMPLETED_NO_PROMOTION`**

- El piloto v2.33D1 se declara **completado**: se ejecutó la descarga real autorizada, se validaron los 77 históricos y se documentaron sus limitaciones con evidencia reproducible.
- **No se promociona** EODHD (plan gratuito) a producción: falla el umbral de cobertura histórica (17.5% vs 90% requerido) y el umbral de emparejamiento sobre la muestra completa (32% vs 90% requerido); fundamentales no se han evaluado.
- Esta decisión **no** autoriza scoring productivo, rankings reales, recomendaciones de inversión, incorporación masiva de precios, contratación de planes, conexión con brokers ni el inicio de la fase 5.
- **Descartado explícitamente por el usuario (2026-08-30): no se contratará ningún plan de pago de EODHD.** Queda descartada la vía de "confirmar el límite de ~1 año con un plan de pago". EODHD queda cerrado como fuente de precios mundiales en su plan gratuito, sin previsión de reevaluación con un plan superior.

## Símbolos aún bloqueados (162/240)

- 119 Cboe Europe: requieren recuperar la bolsa principal de cotización.
- 42 Japón (JPX): requieren confirmar el código exacto del catálogo EODHD.
- 1 Colombia (BVC): requiere búsqueda por identificador.

Ninguno se ha resuelto por aproximación; siguen bloqueados de forma fail-closed.

## Seguridad y alcance

- `SCOUT_FINANCE_EODHD_API_TOKEN` nunca se ha impreso, registrado ni versionado.
- Los 77 JSON brutos permanecen fuera de Git (`outputs/full_universe_source_acquisition/v2_33d_price_pilot/eodhd_prices_collection_77_v2_33d/`, ignorado).
- Este documento y los informes agregados no reproducen precios fila a fila ni contenido licenciado.
- `production_scoring_authorized: false`, `allow_ranking: false` en todos los informes generados.

## Estado del roadmap

- Interfaz estable: `v2.32F` (sin cambios en este cierre).
- Pipeline de datos: `v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation` (este cierre).
- Progreso global: **3/8 fases cerradas, fase 4 en curso**. La fase 4 (adquisición de fuente de datos completa) sigue abierta: quedan símbolos por resolver (162/240), mercados sin cubrir (SGX, Xetra) y EODHD gratuito descartado por profundidad histórica insuficiente.
- **Decisión del usuario (2026-08-30): sin plan de pago.** Se descarta contratar cualquier plan de pago de EODHD para reintentar este piloto. EODHD queda cerrado en `COMPLETED_NO_PROMOTION` de forma definitiva salvo que el usuario reabra la cuestión explícitamente.
- Siguiente paso recomendado (no ejecutado, no autorizado por este cierre): evaluar, dentro de fuentes gratuitas, una alternativa distinta a EODHD para precios mundiales (p. ej. Twelve Data, ya contemplado como contraste en v2.33C), o continuar resolviendo los 162 símbolos ambiguos restantes sin asumir que resolverlos resolvería también la profundidad histórica del proveedor.
