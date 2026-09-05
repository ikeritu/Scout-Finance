# v2.38Z — Europe Ireland identity resolution + CRO registry lookup (real)

Fecha: 2026-09-05. Alcance: aplicar a los 17 activos de Euronext Dublin/Irlanda (v2.38T) la misma corrección de identidad que se probó real y correcta en los 40 activos GB (v2.38V), e investigar si Irlanda tiene un equivalente gratuito a UK Companies House.

## Parte 1 — Resolución de identidad vía fuente Xetra (real, sin red)

Los 17 activos comparten exactamente el mismo problema ya diagnosticado para GB: `company_name="UKI0"` (el código de segmento de mercado de Xetra, mal mapeado a `company_name` en una fase muy anterior) y un `ticker` que en realidad es el mnemonic interno de Xetra, no un ticker real de Euronext Dublin.

`scripts/resolve_europe_ireland_identity_xetra_source_v2_38z.py` — mismo método ya probado en v2.38V (resolver por Mnemonic → ISIN/Instrument contra el fichero fuente de Deutsche Börse Xetra ya local, sin red, fail-closed): 0 candidatos o >1 ISIN distinto para el mismo mnemonic → sin resolver.

**Resultado real: 17/17 resueltos, 0 ambiguos.** Lista completa: Smurfit Westrock, ICON plc, TE Connectivity, James Hardie Industries, Linde plc, Accenture, Jazz Pharmaceuticals, Alkermes, Eaton Corporation, Willis Towers Watson, Allegion, Trane Technologies, Seagate Technology, Aon, Medtronic, Johnson Controls International, Ryanair Holdings. Varias son multinacionales estadounidenses redomiciliadas en Irlanda (Medtronic, Eaton, Aon, Allegion, Trane, Johnson Controls, TE Connectivity, Seagate) — genuinamente incorporadas en Irlanda, no solo cotizadas allí.

## Investigación previa (desk research, antes de escribir ningún script de registro)

Antes de construir cualquier localizador de perfil, se investigó si Irlanda tiene un equivalente al API gratuito de UK Companies House:

- **No existe un API REST/SOAP documentado en el portal principal de la CRO (`core.cro.ie`)** — solo un buscador web gratuito (nombre/número), sin cuenta, pero es un portal web, no un API — usarlo automatizado sería scraping, prohibido por la política de este proyecto.
- **Sí existe un Open Data Portal oficial de la CRO** (`opendata.cro.ie`), publicado bajo licencia **CC BY 4.0** (dominio de datos abiertos de la UE, `Directive (EU) 2019/1024`), con dos datasets accesibles vía el **API estándar CKAN Datastore** (`/api/3/action/datastore_search`), **sin cuenta ni credencial de ningún tipo**:
  1. **Company Records** — 823.780 filas, actualizado a diario: número, nombre, estado, tipo, fecha de registro, dirección. El equivalente real a la búsqueda gratuita de Companies House.
  2. **Financial Statements** — índice de cuentas depositadas (2022-2024): nombre de fichero, número de empresa, fechas de presentación.

## Sondeo en vivo real (antes de construir el localizador)

Confirmado con llamadas reales, de solo lectura, al API público:
- `datastore_search_sql` con `GROUP BY` sobre el dataset "Financial Statements 2024" (230.410 filas): **100% de los ficheros son `.pdf`** — ninguno es iXBRL/XHTML. Verificado también específicamente para Ryanair Holdings (nº 249885): su única presentación de 2024 es `129811965.pdf`.
- **Consecuencia**: no existe ninguna cifra financiera estructurada ni ningún documento iXBRL disponible para NINGUNA empresa irlandesa a través de este dataset — no es una limitación de nuestras 17 empresas en particular, es el estado de todo el registro. Ningún script de descarga de cuentas ni de normalización iXBRL se construye para Irlanda: sería exactamente el mismo muro de "solo PDF, sin OCR" ya documentado para Rio Tinto/Rentokil/SSE en GB, pero confirmado aquí de forma total y definitiva, no parcial.
- El dataset "Company Records" sí es útil y se usó: consultas reales confirmaron coincidencias exactas y sin ambigüedad para varias empresas (p. ej. "RYANAIR HOLDINGS%" → una única fila activa, "AON PLC" → "AON PUBLIC LIMITED COMPANY" única).

## Parte 2 — Localizador de perfil CRO (ejecutado, sin credencial)

`scripts/run_europe_ireland_cro_lookup_v2_38z.py` — consulta el endpoint público `datastore_search` (con parámetro `q=`, nunca SQL crudo construido con texto de empresa, para evitar cualquier riesgo de inyección) y aplica la misma lógica de emparejamiento fail-closed ya probada en la corrección de v2.38Y (incluida la corrección de sufijos con puntos, "P.L.C." → "PLC"), con sufijos legales irlandeses añadidos (`PUBLIC LIMITED COMPANY`, `UNLIMITED COMPANY`, `ULC`).

**Resultado real (ejecutado 2026-09-05, sin credencial):**

| | Cantidad |
|---|---|
| Activos de entrada | 17 |
| **Perfiles confirmados** | **8** (Smurfit Westrock, ICON, TE Connectivity, Linde, Alkermes, Willis Towers Watson, Allegion, Medtronic) |
| Sin resolver | 9 — `no_exact_normalized_name_match` |

Los 9 sin resolver comparten el mismo patrón ya documentado en GB: el campo `Instrument` de Xetra abrevia el nombre real (`"JAMES HARDIE IND."`, `"JAZZ PHARMACEUT."`, `"EATON CORP.PLC"`, `"TRANE TECHNOLOG. PLC"`, `"SEAGATE TEC.HLD."`, `"JOHNSON CONTR.INTL."`, `"RYANAIR HLDGS PLC"`, `"ACCENTURE A"`, `"AON PLC A"`) de una forma que no coincide exactamente con la razón social real registrada en la CRO. **No se ha intentado ninguna heurística de expansión de abreviaturas ni de eliminación de sufijos de clase de acción** (p. ej. la "A" final en "ACCENTURE A"/"AON PLC A") — aunque una comprobación manual confirma que ambas SÍ tienen una coincidencia real y exacta en la CRO, construir una regla específica para este caso sería ajustar el emparejador a la respuesta ya conocida, exactamente el tipo de sobreajuste que causó el error real de v2.38V (SCT/BMT). Se documenta como limitación honesta, no se corrige.

## Pruebas offline

- `tests/qa_europe_ireland_identity_xetra_source_v2_38z.py` — 5 casos: resolución exacta, filtrado defensivo por jurisdicción (una fila GB en la entrada nunca se resuelve por este script), mnemonic ausente, ISIN ambiguo, limpieza de sufijo de denominación.
- `tests/qa_europe_ireland_cro_lookup_v2_38z.py` — 4 casos: dry-run sin red, **confirmación explícita de que no se requiere credencial** (diseño deliberadamente distinto de UK Companies House), coincidencia exacta vs. nombre abreviado que se queda sin resolver (reproduce el caso real Ryanair), normalización con sufijos con puntos e irlandeses.

```
.venv/Scripts/python.exe tests/qa_europe_ireland_identity_xetra_source_v2_38z.py
PASS: v2.38Z-ireland-identity-xetra-source/jurisdiction-filter/ambiguous-isin/no-network
.venv/Scripts/python.exe tests/qa_europe_ireland_cro_lookup_v2_38z.py
PASS: v2.38Z-ireland-cro-lookup/dry-run-gate/no-credential-needed/fail-closed-name-match/no-guessing
```

## Seguridad y alcance

- Red real usada: CRO Open Data Portal (público, sin cuenta, sin credencial de ningún tipo) — 17 llamadas de búsqueda de perfil, más el sondeo previo de investigación (unas pocas llamadas de solo lectura, sin escribir nada, para confirmar el formato del dataset de cuentas antes de decidir no construir el pipeline de extracción).
- Ninguna cuenta creada por este proyecto (no hace falta ninguna para este dataset).
- Sin descarga de documentos de cuentas, sin extracción iXBRL (confirmado imposible para toda Irlanda, no solo para estas 17 empresas).
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen frente a GB (v2.38V/Y)

| | GB (v2.38V/Y) | Irlanda (v2.38Z) |
|---|---:|---:|
| Identidades de entrada | 40 | 17 |
| Identidades resueltas vía Xetra/ISIN | 40/40 | 17/17 |
| Perfiles de registro oficial confirmados | 29/40 | 8/17 |
| Credencial requerida para el registro | Sí (Companies House, gratuita) | **No** (CRO Open Data, público) |
| Empresas con datos financieros reales extraíbles (iXBRL) | 2 (Softcat, Kingfisher) | **0 (confirmado imposible para toda Irlanda)** |

**Estado del bloque: `COMPLETED_EUROPE_IRELAND_IDENTITY_RESOLVED_REGISTRY_PARTIAL_NO_FINANCIALS_POSSIBLE`.** Identidad: éxito completo (17/17). Registro: éxito parcial honesto (8/17, fail-closed). Fundamentales reales: confirmado, con evidencia real y no por inferencia, que no existe ninguna vía posible a través de la CRO — a diferencia de GB, donde al menos 2 empresas sí tenían iXBRL real disponible.
