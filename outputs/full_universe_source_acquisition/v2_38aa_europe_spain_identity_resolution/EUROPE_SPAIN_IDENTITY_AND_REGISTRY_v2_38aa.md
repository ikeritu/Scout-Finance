# v2.38AA — Europe Spain identity resolution + registry/financials research (real)

Fecha: 2026-09-05. Alcance: aplicar a los 15 activos de Bolsa de Madrid (v2.38S, jurisdicción ES) el mismo método ya probado real en GB (40/40, v2.38V) e Irlanda (17/17, v2.38Z), e investigar si España tiene un registro oficial gratuito con datos estructurados o financials reales.

**Nota de nomenclatura**: el alfabeto de bloques llegó a la letra Z con Irlanda. Este bloque continúa la secuencia como "AA", igual que las hojas de cálculo cuando se acaban las letras (…, Y, Z, AA, AB, …).

## Parte 1 — Resolución de identidad vía fuente Xetra (real, sin red)

Los 15 activos comparten el mismo problema ya diagnosticado para GB e Irlanda: `company_name="ESP0"` (código de segmento de mercado de Xetra para España, mal mapeado a `company_name`) y un `ticker` que en realidad es el mnemonic interno de Xetra, no un ticker real de la Bolsa de Madrid.

`scripts/resolve_europe_spain_identity_xetra_source_v2_38aa.py` — mismo método ya probado (Mnemonic → ISIN/Instrument contra el fichero fuente de Deutsche Börse Xetra ya local, sin red, fail-closed).

**Resultado real: 15/15 resueltos, 0 ambiguos.** Lista completa, todas empresas reales y muy conocidas del IBEX 35: AENA, Cellnex Telecom, Amadeus IT Group, Banco Bilbao Vizcaya Argentaria, Banco de Sabadell, Banco Santander, Indra Sistemas, Endesa, CaixaBank, Iberdrola, Inditex, Redeia Corporación, Repsol, International Consolidated Airlines Group (IAG), Telefónica.

## Investigación del registro oficial español (desk research real, antes de escribir ningún script de registro)

Se investigaron **tres vías oficiales reales**, con evidencia concreta para cada una, antes de decidir no construir ningún script de registro/financials para España:

### 1. Colegio de Registradores — Open Data (`opendata.registradores.org`)

Anunciado como plataforma oficial de datos públicos y gratuitos del Registro Mercantil y de la Propiedad. **Comprobado en vivo con una petición HTTP simple, sin cabeceras especiales**: el servidor devuelve un bloqueo WAF explícito —

```
HTTP/1.1 200 OK (con cuerpo de error)
<html><head><title>Request Rejected</title></head>
<body>The requested URL was rejected. Please consult with your administrator...</body></html>
```

Esto no es un artefacto de la herramienta de scraping usada — se confirmó con `curl` puro, sin ningún user-agent ni cabecera especial. Es una medida anti-automatización real del propio servidor. Siguiendo la política ya establecida de este proyecto ("si un proveedor tiene medidas anti-automatización, es una señal de alto, no un rompecabezas que resolver"), **no se ha intentado ningún rodeo** (sin user-agent falso, sin navegador headless, sin reintentos con otra IP). Confirmado como vía bloqueada, no como vía inexistente.

### 2. BORME vía la sede electrónica del BOE (`boe.es/datosabiertos`)

El Boletín Oficial del Registro Mercantil sí tiene un **API REST real y documentado** (`boe.es/datosabiertos/api/api.php`, método GET, HTTPS, sin credencial), que devuelve sumarios diarios del boletín en XML. **Pero no es lo que necesitamos**: es un boletín cronológico de actos legales (constituciones, cambios de capital, ceses de administradores, disoluciones...), no una base de datos de empresas consultable por nombre ni un repositorio de cuentas anuales. Usarlo para "confirmar el perfil de Iberdrola" exigiría rastrear años de sumarios diarios buscando menciones — una tarea de complejidad y fiabilidad muy distintas a una consulta de perfil como la de UK Companies House o la CRO irlandesa, y fuera de alcance de este bloque.

### 3. CNMV — informes XBRL de empresas cotizadas (`cnmv.es/ipps/`, `cnmv.es/portal/consultas/em_inffinanual`)

La vía más prometedora en teoría: la CNMV (regulador de valores español, equivalente a la SEC) exige a las empresas cotizadas presentar sus cuentas anuales y semestrales en **XBRL/iXBRL bajo ESEF desde 2020** (Reglamento Delegado (UE) 2019/815) — exactamente el tipo de dato estructurado que sí funcionó para Softcat y Kingfisher en GB. **Comprobado**: tanto la herramienta de visualización/descarga de XBRL (`cnmv.es/ipps/`) como el buscador de información financiera anual (`em_inffinanual`) son **formularios web interactivos (ASPX), sin ningún API REST documentado ni patrón de URL estable para descarga programática**. Automatizarlos exigiría rellenar y raspar un formulario web — scraping, prohibido por la política de este proyecto. El dataset de datos.gob.es que cataloga esta información lo confirma explícitamente: "el dataset carece de un endpoint de API estructurado — el acceso ocurre a través de la interfaz de búsqueda interactiva de la CNMV, no mediante parámetros de consulta programáticos."

## Conclusión

**Ninguna de las tres vías oficiales españolas ofrece hoy un acceso gratuito, no bloqueado y sin scraping** a un registro de empresas consultable por nombre ni a financials reales — a diferencia de UK (Companies House, API REST real con credencial gratuita) e Irlanda (CRO Open Data, API CKAN real y sin credencial). No se construye ningún script de localización de perfil ni de extracción de cuentas para España. Esto no es una limitación de estas 15 empresas en particular: es el estado real del acceso programático a estas tres fuentes españolas en la fecha de esta investigación.

## Pruebas offline

`tests/qa_europe_spain_identity_xetra_source_v2_38aa.py` — 5 casos: resolución exacta, filtrado defensivo por jurisdicción (una fila GB en la entrada nunca se resuelve por este script), mnemonic ausente, ISIN ambiguo, limpieza de sufijo de denominación.

```
.venv/Scripts/python.exe tests/qa_europe_spain_identity_xetra_source_v2_38aa.py
PASS: v2.38AA-spain-identity-xetra-source/jurisdiction-filter/ambiguous-isin/no-network
```

## Seguridad y alcance

- Red real usada: ninguna llamada de escritura ni de negocio — solo consultas de solo lectura durante la investigación (páginas públicas, y una comprobación HTTP simple contra `opendata.registradores.org` que confirmó el bloqueo WAF).
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Ningún scraping, ningún rodeo de medidas anti-automatización.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen frente a GB e Irlanda

| | GB (v2.38V/Y) | Irlanda (v2.38Z) | España (v2.38AA) |
|---|---:|---:|---:|
| Identidades de entrada | 40 | 17 | 15 |
| Identidades resueltas vía Xetra/ISIN | 40/40 | 17/17 | **15/15** |
| Registro oficial gratuito accesible | Sí (Companies House, credencial gratuita) | Sí (CRO Open Data, sin credencial) | **No** (las 3 vías reales comprobadas están bloqueadas, no son buscables, o exigen scraping) |
| Empresas con fundamentales reales extraíbles | 2 (Softcat, Kingfisher) | 0 (confirmado imposible) | **0 (sin vía de acceso, no evaluado)** |

**Estado del bloque: `COMPLETED_EUROPE_SPAIN_IDENTITY_RESOLVED_NO_FREE_REGISTRY_ACCESS`.** Identidad: éxito completo (15/15). Registro y fundamentales: ninguna vía oficial gratuita y accesible sin scraping — documentado con evidencia real de las tres alternativas comprobadas, no una suposición.
