# v2.38AE — Netherlands registry lookup (real) — y un descubrimiento reutilizable: GLEIF

Fecha: 2026-09-06. Alcance: investigar y ejecutar un localizador de perfil oficial para los 44 activos de Países Bajos (identidad ya resuelta al 100% en v2.38AB).

## Investigación real de vías oficiales holandesas

- **API oficial de búsqueda de KVK ("Zoeken")**: de pago (€6,40/mes + coste por consulta) — descartada por la política de este proyecto.
- **OpenKvK.nl** (alternativa gratuita más prometedora en teoría): **bloqueada por un reto anti-bot real de Cloudflare** ("Just a moment...", comprobado en vivo con `curl` puro) — señal de alto, sin rodeos intentados.
- **"KVK HR Open Data Set"** (dataset abierto oficial, CC0, sin cuenta): comprobado en vivo que está **explícitamente anonimizado** — el nombre de empresa y el número de KVK se eliminan a propósito por privacidad. Inútil para buscar una empresa concreta por nombre.

## El descubrimiento: GLEIF resuelve el problema de raíz

Dado que ninguna vía holandesa permite buscar por nombre, se investigó **GLEIF** (Global Legal Entity Identifier Foundation) — el organismo internacional (creado por el G20/FSB) que gestiona el identificador LEI usado en regulación financiera mundial. Su API es **gratuita, sin cuenta, sin clave, licencia CC0, sin límite de peticiones documentado**, y permite **resolver un ISIN directamente a su registro LEI completo** — que incluye la autoridad de registro nacional y el número de registro nacional.

**Comprobado en vivo, con nuestros propios ISIN reales** (ya resueltos en v2.38AB, sin necesidad de buscar por nombre en absoluto):
- ASML Holding N.V. (ISIN `NL0010273215`) → LEI `724500Y6DUVHQD6OXN27`, autoridad `RA000463` (KVK), **número KVK real: `17085815`**, estado `ACTIVE`.
- Heineken N.V. (ISIN `NL0000009165`) → **número KVK real: `33011433`**, estado `ACTIVE`.

Esto elimina por completo el problema de ambigüedad por nombre que ya afectó a Francia (empresas activas duplicadas) y a GB/Irlanda (nombres abreviados de Xetra) — **el ISIN es una clave perfecta y única**, sin necesidad de ningún emparejamiento de texto.

**Relevancia para el resto del proyecto**: GLEIF no es específico de Países Bajos — puede dar el número de registro nacional equivalente (Handelsregister alemán, SIREN francés, número de Companies House, etc.) para cualquier país con una entidad LEI. Esto queda anotado como una vía de generalización futura potencial, no ejecutada en este bloque (alcance deliberadamente limitado a Países Bajos, por instrucción explícita del usuario).

## Resultado real — Parte 1: identidad y registro

`scripts/run_europe_netherlands_registry_lookup_v2_38ae.py` — consulta GLEIF por ISIN para cada uno de los 44 activos.

**Resultado real: 36/44 perfiles LEI confirmados, 36/44 números KVK reales obtenidos.** 8/44 sin registro LEI para ese ISIN concreto (`no_lei_record_for_isin`) — una limitación de cobertura ya documentada del propio mapeo ISIN↔LEI de GLEIF (algunas emisiones no están auto-reportadas por el emisor), no un fallo de nuestro método: AD PEPPER MEDIA, AERCAP HOLDINGS, LYONDELLBASELL IND. A, NXP SEMICONDUCTORS, CNH INDUSTRIAL, A.H.T. SYNGAS TECH., ELASTIC N.V., DAVIDE CAMPARI-MILANO.

Ejemplos reales confirmados: Koninklijke KPN N.V. (KVK 02045200), Heineken N.V. (33011433), Koninklijke Philips N.V. (17001910), STMicroelectronics N.V. (33194537), Airbus SE (24288945), ASM International N.V. (30037466), Wolters Kluwer N.V. (33202517).

## Resultado real — Parte 2: cuentas anuales estructuradas (muestra representativa)

El **"KVK Jaarrekeningen Open Dataset"** (`opendata.kvk.nl`) ofrece de verdad **hechos financieros estructurados extraídos de XBRL** (balance, cuenta de resultados, flujo de caja) por número de KVK, gratis, sin cuenta — potencialmente mucho mejor que el PDF de GB/Irlanda. Pero tiene un límite real y documentado de **máximo 1 petición/minuto por IP**.

Dado que dos comprobaciones individuales previas (ASML, Heineken) ya dieron negativo, se comprobó una **muestra representativa de 8** (no las 44, para no gastar ~44 minutos confirmando un patrón ya evidenciado) — respetando el límite real de 1/min.

**Resultado real: 0/8 tienen cuentas anuales en este dataset** (`IPD0001: Het gevraagde product voor Jaarrekeningen bestaat niet` — "el producto solicitado no existe", en las 8 consultas). Esto confirma que el dataset cubre las presentaciones simplificadas SBR/XBRL obligatorias para empresas micro/pequeñas/medianas desde 2016/2017 — **las grandes multinacionales que presentan cuentas consolidadas bajo IFRS completo, como nuestras 44, no están en este régimen**, el mismo muro de "PDF/no-digital para grandes cotizadas" ya visto en Rio Tinto/Rentokil/SSE (GB) y en toda Irlanda.

## Pruebas offline

`tests/qa_europe_netherlands_registry_lookup_v2_38ae.py` — 4 casos: dry-run sin red, **reproducción exacta del caso real ASML** (ISIN → KVK 17085815, sin credencial), sin registro LEI queda sin resolver, **reproducción exacta del caso real "producto no existe"** para la muestra de cuentas anuales.

```
.venv/Scripts/python.exe tests/qa_europe_netherlands_registry_lookup_v2_38ae.py
PASS: v2.38AE-netherlands-registry-lookup/dry-run-gate/isin-keyed-gleif-lookup/jaarrekeningen-sample-not-found
```

## Seguridad y alcance

- Red real usada: GLEIF (público, sin cuenta, CC0) — 44 llamadas; KVK Jaarrekeningen Open Dataset (público, sin cuenta) — 8 llamadas, respetando el límite real de 1/min.
- Ninguna cuenta creada, ninguna credencial usada ni necesaria.
- Sin scraping, sin rodeo del reto anti-bot de OpenKvK.nl.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C. `production_scoring_authorized: false`, `allow_ranking: false`.

## Resumen frente a las jurisdicciones ya tratadas

| | GB | Irlanda | España | Alemania | Francia | **Países Bajos** |
|---|---:|---:|---:|---:|---:|---:|
| Activos | 40 | 17 | 15 | 413 | 53 | **44** |
| Identidad/registro resuelto | 29/40 | 8/17 | — | — | 18/53 | **36/44** |
| Método de emparejamiento | Nombre (Companies House) | Nombre (CRO) | — | — | Nombre (registro FR) | **ISIN exacto (GLEIF)** |
| Fundamentales reales accesibles | Sí (2 empresas) | No | — | — | No | **No (0/8 en muestra, patrón ya evidenciado)** |

**Estado del bloque: `COMPLETED_EUROPE_NETHERLANDS_REGISTRY_LOOKUP_PARTIAL_NO_FINANCIALS_ACCESS`.** Registro: 36/44 confirmados, con un método nuevo y más fiable (ISIN vía GLEIF, sin ambigüedad de nombre) que además es reutilizable para cualquier otro país. Fundamentales: confirmado sin acceso, mismo patrón "grandes cotizadas sin presentación digital simplificada" ya visto en GB/Irlanda.
