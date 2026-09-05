# v2.38AC — Germany registry/financials research (real, no scripts built)

Fecha: 2026-09-05. Alcance: investigar si Alemania (413 activos, el país más grande del universo europeo tras v2.38AB) tiene un registro oficial gratuito equivalente a UK Companies House o la CRO irlandesa. **La identidad de los 413 activos alemanes ya está resuelta al 100%** (parte de los 689/689 de v2.38AB) — este bloque es puramente investigación de registro/financials, sin script de resolución de identidad nuevo.

## Tres vías reales investigadas, con evidencia concreta

### 1. Handelsregister (registro mercantil oficial, `handelsregister.de`)

Confirmado por múltiples fuentes independientes: **no existe un API oficial documentado** para consultar el registro mercantil alemán. El portal de justicia (`handelsregister.de`) y el portal de anuncios (`handelsregisterbekanntmachungen.de`) están pensados para consulta humana, no para acceso programático — ninguna documentación técnica de acceso automatizado existe.

### 2. Bundesanzeiger (publicación legal de cuentas anuales, `bundesanzeiger.de`)

Alemania exige por ley que las empresas depositen y publiquen sus cuentas anuales (`Jahresabschluss`) en el Bundesanzeiger — la publicación en sí es gratuita de consultar (a diferencia de los extractos del registro mercantil, que sí tienen coste). Pero **no existe ningún API ni dataset estructurado** — es un portal de búsqueda interactivo diseñado solo para consulta manual; extraer datos de forma automatizada exigiría scraping, prohibido por la política de este proyecto.

### 3. OffeneRegister.de (iniciativa cívica sin ánimo de lucro, comprobada en vivo)

La alternativa más prometedora en teoría: un proyecto de la **Open Knowledge Foundation Deutschland** (ONG cívica reputada) en colaboración con OpenCorporates, que republica datos ya públicos de anuncios oficiales del registro mercantil (`handelsregisterbekanntmachungen.de`) bajo licencia **CC BY 4.0**, con un API SQL real y documentado (`db.offeneregister.de`, basado en Datasette).

**Comprobado en vivo, dos veces, con resultado negativo real**:
- El API interactivo (`db.offeneregister.de`) devuelve **HTTP 502 Bad Gateway** de forma consistente (comprobado dos veces con `curl` simple) — el servicio backend está caído, no es un bloqueo de acceso ni un artefacto de la herramienta usada.
- Los ficheros de descarga masiva (`daten.offeneregister.de/*.jsonl.bz2`, `*.db.gz`) sí responden `200 OK`, pero su cabecera `Last-Modified` confirma que **los datos son de febrero de 2019** — más de 7 años obsoletos a fecha de esta investigación. Usar un snapshot de 2019 para confirmar identidad/estado de empresas activas hoy no cumpliría el estándar de evidencia real que este proyecto exige (el mismo motivo por el que los localizadores de GB/Irlanda siempre exigen `company_status == "active"/"Normal"`, no solo una coincidencia de nombre).

**Conclusión: esta vía existe, es gratuita y de origen legítimo, pero está técnicamente muerta hoy** — ni el servicio interactivo funciona, ni los datos masivos están actualizados.

## Conclusión general

**Ninguna de las tres vías ofrece hoy un acceso gratuito, actualizado y sin scraping** al registro mercantil o a las cuentas anuales alemanas. No se construye ningún script de localización de perfil ni de extracción de cuentas para Alemania. Esto no descarta que en el futuro alguna de estas vías vuelva a estar operativa (especialmente OffeneRegister.de, que podría revivir su servicio) — pero a fecha de esta investigación, el resultado real y verificado es negativo.

## Seguridad y alcance

- Red real usada: únicamente peticiones de solo lectura durante la investigación (páginas públicas de documentación, y dos comprobaciones `curl` simples contra `db.offeneregister.de` que confirmaron el error 502).
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Ningún scraping, ningún rodeo de medidas de acceso.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | España | **Alemania** |
|---|---:|---:|---:|---:|
| Activos | 40 | 17 | 15 | **413** |
| Identidad resuelta | 40/40 | 17/17 | 15/15 | **413/413** (vía v2.38AB) |
| Registro oficial gratuito accesible | Sí | Sí | No | **No** (la única vía prometedora está técnicamente caída y con datos de 2019) |

**Estado del bloque: `COMPLETED_EUROPE_GERMANY_REGISTRY_RESEARCH_NO_VIABLE_FREE_SOURCE`.** Identidad: ya resuelta (413/413, v2.38AB). Registro y fundamentales: sin vía oficial gratuita, actualizada y accesible sin scraping — documentado con evidencia real de las tres alternativas comprobadas.
