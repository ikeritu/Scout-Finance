# Scout Finance v2.34B — evaluación de fuentes de fundamentales (Bloque B, fase 5)

Fecha: 2026-08-31. Alcance: **investigación documental + comprobación técnica directa (peticiones de sondeo sin credenciales para MOPS; ninguna llamada nueva a J-Quants en este bloque, se reutiliza la cuenta y las condiciones ya confirmadas en v2.33G/N)**. No se ha creado ninguna cuenta nueva, no se ha gastado dinero.

## B.1 — Japón (JPX)

### Fuente evaluada: J-Quants `/v2/fins/summary`

| Campo | Detalle |
|---|---|
| Propietario | Japan Exchange Group (JPX) |
| URL oficial | `jpx-jquants.com` |
| Método de acceso | REST, cabecera `x-api-key` (misma cuenta ya creada por el usuario en v2.33G) |
| Endpoint | `GET /v2/fins/summary?code=<código>` |
| Necesidad de cuenta | Sí, ya existe (v2.33G) |
| Necesidad de token | Sí, `SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN` ya configurado |
| Límites | 5 solicitudes/minuto documentadas, más estrictas en la práctica (confirmado empíricamente en v2.33G); mismo backoff ya implementado se reutilizará |
| Profundidad histórica (plan gratuito) | **2 años**, confirmado en la tabla oficial de disponibilidad por plan |
| Retraso | **12 semanas**, igual que los precios |
| Campos disponibles (confirmados, cita textual de la documentación oficial) | `Sales`, `OP` (beneficio operativo), `OdP` (beneficio ordinario, específico JGAAP), `NP` (beneficio neto), `EPS`, `DEPS` (diluido), `TA` (activos totales), `Eq` (patrimonio), `EqAR` (ratio de patrimonio), `BPS`, `CFO`, `CFI`, `CFF`, `CashEq`, `ShEq`, `ROE`, dividendos por periodo (`Div1Q`–`DivAnn`, `PayoutRatioAnn`), previsiones de la propia empresa, cifras no consolidadas (prefijo `NC`), acciones en circulación (`ShOutFY`, `AvgSh`) |
| **Campos NO disponibles en el plan gratuito** | **Desglose detallado de balance y deuda** (`/v2/fins/details`, exclusivo del plan Premium de pago, confirmado en la tabla oficial de disponibilidad) — sin líneas de deuda financiera corriente/no corriente, sin desglose de activo/pasivo corriente más allá de los totales agregados en `/fins/summary`. `/fins/dividend` (dividendos detallados) también exclusivo de Premium — pero los dividendos básicos por periodo sí están en `/fins/summary`. |
| Idiomas | Nombres de campo en inglés/abreviado; criterios contables japoneses (JGAAP) |
| Monedas | JPY |
| Identificadores | Código JPX oficial (mismo usado para precios) |
| Consolidado/individual | Ambos disponibles simultáneamente (columnas con y sin prefijo `NC`) |
| Restatements | El propio endpoint documenta campos de cambios contables (`ChgByASRev`, `ChgNoASRev`, `ChgAcEst`, `RetroRst`) — el proveedor sí distingue restatements |
| Licencia | La misma ya confirmada en v2.33N: uso personal permitido, prohíbe redistribuir datos en bruto y proveer análisis a terceros de forma recurrente |
| Condiciones de almacenamiento | Mismas de v2.33N: debe poder borrarse todo dato y derivado si se cancela la suscripción |
| Publicación de agregados | Permitida (gráficos, informes) según los mismos términos ya citados en v2.33N |
| Riesgos | Ninguno nuevo respecto a v2.33N; el retraso de 12 semanas es más relevante aquí que en precios, porque un balance de "hace 3 meses" para una empresa con ejercicio fiscal trimestral podría corresponder ya al trimestre anterior en vez del más reciente publicado. |

**Decisión JPX: `APPROVED_SCOPED`.** Aprobado para el conjunto de campos de `/fins/summary` (cuenta de resultados resumida, balance agregado, flujo de caja de alto nivel, dividendos, dos años de historia). **No aprobado ni disponible** el desglose detallado de deuda/balance (`/fins/details`), porque exige el plan Premium de pago, ya descartado por decisión general del usuario.

## B.2 — Taiwán (TWSE)

### Fuente evaluada: MOPS (Market Observation Post System) — descargas abiertas de `mopsfin.twse.com.tw/opendata/`

Confirmado en vivo, sin credenciales, tres archivos reales:

| Archivo | Contenido confirmado | Método de acceso |
|---|---|---|
| `t187ap03_L.csv` | Información básica de la empresa (identidad, fecha de constitución, fecha de cotización, capital) | Descarga CSV pública, sin cuenta |
| `t187ap06_L_ci.csv` | **Cuenta de resultados consolidada**: ingresos, coste de ventas, beneficio bruto, gastos operativos, beneficio operativo, resultado antes de impuestos, gasto por impuestos, beneficio neto | Descarga CSV pública, sin cuenta |
| `t187ap07_L_ci.csv` | **Balance consolidado**: activo corriente, activo no corriente, activo total, pasivo corriente, pasivo no corriente, pasivo total, capital social, prima de emisión, reservas, patrimonio total | Descarga CSV pública, sin cuenta |
| `t187ap17_L.csv` | Ratios de rentabilidad ya calculados por el propio MOPS (márgenes bruto/operativo/antes de impuestos/neto) — útil como verificación cruzada de nuestros propios cálculos (Bloque H) | Descarga CSV pública, sin cuenta |

**No se ha encontrado ni confirmado** un archivo equivalente para el estado de flujos de efectivo en esta pasada de investigación. Queda como limitación no confirmada, no como ausencia definitiva.

**Hallazgo crítico, confirmado empíricamente, no asumido:** estos archivos son una **fotografía del último periodo divulgado para todas las empresas cotizadas a la vez** (verificado descargando `t187ap06_L_ci.csv`: 1.036 filas, con año/trimestre únicos — `115` / `Q2` — en todas ellas), **no un archivo histórico por empresa**. A diferencia de J-Quants (que sí entrega hasta 2 años de histórico por consulta), MOPS open-data solo da el periodo más reciente. La consulta histórica por empresa existe como herramienta web (`mops.twse.com.tw/mops/web/t05st34`), pero no está confirmada como una API documentada y estable — usarla exigiría una interacción con un formulario web, lo cual se acerca al tipo de scraping dudoso que este proyecto evita (regla 8.2 del encargo). **No se ha investigado ni utilizado esa vía en este bloque.**

| Campo | Detalle |
|---|---|
| Propietario | Taiwan Stock Exchange / Market Observation Post System (regulador oficial) |
| Necesidad de cuenta | No |
| Necesidad de token | No |
| Límites | No documentados; se aplicará el mismo ritmo prudente ya usado con TWSE en v2.33I |
| Profundidad histórica | **Una sola fotografía del periodo más reciente por empresa** (no un histórico) |
| Frecuencia de actualización | Trimestral (según el ciclo de divulgación regulatoria) |
| Consolidado/individual | Los archivos con sufijo `_ci` son consolidados; existen variantes para otros segmentos de mercado no investigadas aquí (fuera de alcance, nuestros 8 activos son todos `L`, listados) |
| Licencia | 政府資料開放授權條款第1版 (Government Open Data License v1.0) — **misma familia de licencia ya confirmada compatible** en el cierre de precios TWSE (v2.33I) |
| Restricciones de redistribución | Ninguna conocida bajo esta licencia abierta |
| Riesgos | La ausencia de histórico por empresa vía este mecanismo es la limitación principal: solo se puede construir una serie temporal real acumulando esta fotografía trimestral hacia adelante en el tiempo, de la misma forma que se documentó para SGX en v2.33F (limitación estructural, no un fallo de implementación). |

**Decisión TWSE: `APPROVED_SCOPED`.** Aprobado el acceso a los archivos abiertos de MOPS para el periodo más reciente disponible por empresa. **No aprobado** ampliar a consulta histórica por empresa vía el portal web (no confirmado como API documentada).

## Resumen de decisiones

| Mercado | Decisión | Alcance real |
|---|---|---|
| JPX (J-Quants `/fins/summary`) | `APPROVED_SCOPED` | Cuenta de resultados resumida + balance agregado + CF de alto nivel + dividendos, 2 años de historia, sin desglose de deuda |
| TWSE (MOPS opendata) | `APPROVED_SCOPED` | Cuenta de resultados + balance detallados, **un único periodo (el más reciente divulgado) por empresa**, sin flujo de caja confirmado |

Ninguna fuente requiere `REQUIRES_USER_ACCOUNT`, `REQUIRES_PAID_PLAN` ni queda `LICENSE_UNCLEAR`/`TECHNICALLY_BLOCKED`/`REJECTED` — ambas están aprobadas de forma acotada, con sus límites documentados explícitamente para no confundirlos con cobertura completa.

## Seguridad y alcance

- No se ha creado ninguna cuenta nueva.
- No se ha usado la clave de J-Quants en este bloque (solo documentación oficial ya citada).
- Las 4 peticiones a MOPS fueron descargas públicas sin autenticación, sin coste.
- `production_scoring_authorized: false`, `allow_ranking: false`.
