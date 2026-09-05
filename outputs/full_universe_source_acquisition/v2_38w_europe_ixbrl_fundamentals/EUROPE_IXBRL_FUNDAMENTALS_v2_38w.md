# v2.38W — normalización de fundamentales de Europa (iXBRL real)

Fecha: 2026-09-05. Alcance: lo deliberadamente aplazado en v2.38V — obtener el documento de cuentas real de cada empresa confirmada en Companies House y, cuando el formato lo permita, extraer cifras financieras reales de un iXBRL/ESEF real. Dos scripts, ambos ejecutados con la credencial real del usuario.

## Parte 1 — Descarga real de documentos (`fetch_europe_accounts_documents_v2_38w.py`)

Para cada una de las 3 empresas confirmadas en v2.38V, se consulta el historial de filings de Companies House (`/company/{number}/filing-history?category=accounts`) y se inspeccionan los formatos reales disponibles del documento más reciente antes de descargar nada.

**Resultado real:**

| Empresa | Filing más reciente | Formato real | Resultado |
|---|---|---|---|
| RIO TINTO PLC | 2026-04-16 (AA) | `application/pdf` (346 páginas) | **Bloqueado** — `accounts_format_not_parseable_pdf_only` |
| SOFTCAT PLC | 2026-01-06 (AA) | `application/zip` (paquete ESEF completo) | **Descargado** |
| RENTOKIL INITIAL PLC | 2026-05-24 (AA) | `application/pdf` (230 páginas, 11 MB) | **Bloqueado** — `accounts_format_not_parseable_pdf_only` |

Solo Softcat tiene un paquete iXBRL real disponible vía la API pública de Companies House — Rio Tinto y Rentokil solo depositan PDF. Esto no es un fallo del script: es el estado real de lo que cada empresa presentó. El paquete ZIP de Softcat contiene un informe ESEF completo real (`213800N42YZLR9GLVC42-2025-07-31-T01.xhtml`, 16 MB) con su propia taxonomía de extensión, identificado por LEI (`213800N42YZLR9GLVC42`) en el nombre — confirma que Softcat presenta bajo el régimen UK Single Electronic Format, no una casualidad.

El documento se guarda en local (`accounts_documents_raw_v2_38w/`, en `.gitignore` desde antes de crearse) — nunca comiteado, igual que el resto de cachés de proveedor de todo el proyecto.

## Parte 2 — Extracción real de iXBRL (`normalize_europe_ixbrl_fundamentals_v2_38w.py`)

Extractor **específico y acotado**, no un motor XBRL genérico: lee hechos `ix:nonFraction` por nombre de concepto contra una lista cerrada de 14 conceptos estándar `ifrs-full:*`, resuelve el `contextRef` de cada hecho contra las definiciones reales de contexto del propio documento, y solo acepta el contexto **no dimensional** (el total, no un desglose por componente) del periodo más reciente.

**Hallazgo y corrección real durante la construcción** (antes de aceptar ningún resultado): un primer intento del extractor eligió un único "contexto ganador" global por fecha más reciente entre TODOS los conceptos de tipo stock — pero el patrimonio (`Equity`) tiene un desglose por componente (capital social, prima de emisión, reservas...) con **contextos separados que comparten la misma fecha** que el contexto "total" simple. Al competir por un único ganador global, el contexto ganador podía terminar siendo uno de los componentes dimensionales de `Equity`, no el contexto simple — dejando `Assets`, `Liabilities`, etc. marcados como "no etiquetados" aunque sí estaban presentes en el documento real, simplemente bajo un contexto distinto de la misma fecha. Se corrigió exigiendo que cada concepto solo acepte contextos **sin `<xbrli:scenario>`** (confirmado en el documento real: el contexto simple de `Assets`/patrimonio total no tiene escenario; los componentes de patrimonio sí, vía `xbrldi:explicitMember` en el eje `ifrs-full:ComponentsOfEquityAxis`). Prueba de regresión dedicada añadida con un fixture sintético que reproduce exactamente esta forma.

**Otras dos cosas reales confirmadas durante el desarrollo, no asumidas:**
- El texto numérico visible dentro de una etiqueta puede llevar espacios intercalados dentro de los propios dígitos por motivos de maquetación (`"1 ,45 8,4 1 1"` para 1.458.411) — se limpia todo el espacio en blanco antes de quitar las comas de millar.
- `scale` (multiplicador de potencia de diez) y `sign="-"` (negación) son reales y se aplican siempre, dejando también el texto crudo y estos atributos en el registro de salida para trazabilidad.

## Resultado real (Softcat, ejercicio cerrado a 2025-07-31)

**14/14 conceptos extraídos, 0 sin etiquetar.**

| Concepto | Valor (GBP) |
|---|---:|
| Revenue | 1.458.411.000 |
| ProfitLossFromOperatingActivities | 172.900.000 |
| ProfitLossBeforeTax | 178.202.000 |
| ProfitLoss (neto) | 133.008.000 |
| ProfitLossAttributableToOwnersOfParent | 133.008.000 |
| Assets | 1.191.927.000 |
| CurrentAssets | 1.121.714.000 |
| NoncurrentAssets | 70.213.000 |
| CashAndCashEquivalents | 182.282.000 |
| Liabilities | 853.145.000 |
| CurrentLiabilities | 808.950.000 |
| NoncurrentLiabilities | 44.195.000 |
| Equity | 338.782.000 |
| NetAssetsLiabilities | 338.782.000 |

**Verificación cruzada real, no solo esperada:**
- Activos = Pasivos + Patrimonio → 1.191.927.000 = 853.145.000 + 338.782.000 ✓ **exacto**.
- Activo corriente + Activo no corriente = Activo total → 1.121.714.000 + 70.213.000 = 1.191.927.000 ✓ **exacto**.
- Pasivo corriente + Pasivo no corriente = Pasivo total → 808.950.000 + 44.195.000 = 853.145.000 ✓ **exacto**.
- NetAssetsLiabilities = Equity → 338.782.000 = 338.782.000 ✓ **exacto**.

Estas cuatro identidades contables cuadran de forma exacta con datos reales extraídos — la evidencia más fuerte posible de que el extractor funciona correctamente, no solo de que "no lanzó ningún error".

## Rio Tinto y Rentokil — bloqueados, no forzados

Sin iXBRL real disponible, no se ha intentado ningún OCR ni extracción desde PDF — sería exactamente el tipo de código frágil y no verificable que este proyecto evita. Quedan documentados como `accounts_format_not_parseable_pdf_only`, con la ruta real de reintento abierta (Rio Tinto y Rentokil sí presentan iXBRL a HMRC junto con su declaración de impuestos — Companies House simplemente no expone esa copia vía su API pública de documentos).

## Pruebas offline

- `tests/qa_europe_accounts_document_fetch_v2_38w.py` — 3 casos: dry-run sin red, bloqueo real sin credencial, clasificación PDF-bloqueado vs. ZIP-descargado con escritura atómica y sin fuga de credencial. Detectó y motivó la corrección de un bug real (`relative_to(ROOT)` fallaba si `--raw-cache` apunta fuera del repo).
- `tests/qa_europe_ixbrl_fundamentals_v2_38w.py` — 4 casos: limpieza de números con espacios intercalados y comas de millar; **prueba de regresión dedicada** para el bug de contexto dimensional ya descrito; concepto ausente registrado como no etiquetado, nunca inventado; solo se extrae el periodo más reciente, nunca el comparativo del año anterior.

```
.venv/Scripts/python.exe tests/qa_europe_accounts_document_fetch_v2_38w.py
PASS: v2.38W-accounts-document-fetch/dry-run-gate/pdf-vs-zip-classification/atomic-write/no-credential-leak
.venv/Scripts/python.exe tests/qa_europe_ixbrl_fundamentals_v2_38w.py
PASS: v2.38W-ixbrl-normalizer/dimensional-context-regression/number-cleaning/latest-period-only/no-guessing
```

## Seguridad y alcance

- Red real usada: Companies House (con la credencial del usuario, nunca vista ni registrada) — 3 llamadas de historial de filings + 3 de metadatos de documento + 1 descarga real de ZIP.
- El documento real y el JSONL de valores extraídos quedan fuera de git (`.gitignore`, añadido antes de crearse); solo el informe de cobertura agregado (recuentos, sin cifras) se publica.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: parcial, con evidencia real verificada.** 1/3 empresas con fundamentales reales completos y contablemente consistentes (Softcat); 2/3 bloqueadas por formato de documento (PDF sin iXBRL disponible vía la API pública), documentado, no forzado.
