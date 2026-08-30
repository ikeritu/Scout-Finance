# Scout Finance v2.33F — fuentes oficiales por bolsa como alternativa a EODHD/Twelve Data

Fecha: 2026-08-31. Alcance: **investigación documental pública únicamente**. No se ha creado ninguna cuenta (ni siquiera gratuita) en ningún proveedor mencionado, no se ha usado ninguna clave, no se ha llamado a ninguna API, no se ha descargado ningún dato y no se ha gastado dinero. No se ha resuelto ningún ticker nuevo: la resolución de identificadores (OpenFIGI u otra) sigue siendo un trabajo aparte, ya aprobado en v2.33C pero no ejecutado. Esta evaluación no autoriza scoring, rankings, recomendaciones de inversión, contratación de ningún servicio, ni el inicio de la fase 5.

## Por qué se evalúa

Tras descartar EODHD (v2.33D1, `COMPLETED_NO_PROMOTION` por profundidad histórica) y Twelve Data gratuito (v2.33E, descartado por cobertura de mercado), se pide explorar si la propia bolsa de cada mercado, o un organismo oficial equivalente, ofrece una fuente de precios gratuita que resuelva alguno de los dos problemas: los 162 símbolos aún bloqueados, o la escasa profundidad histórica de los 77 ya descargados.

## Primer hallazgo: "Cboe Europe" no es una bolsa de origen, es una plataforma de cruce paneuropea

Antes de buscar "la fuente oficial de Cboe Europe", se revisó la composición real de los 119 símbolos bloqueados bajo `exchange = CBOE_EUROPE` en `price_pilot_symbols_v2_33d.csv`. Sus nombres de empresa muestran que **no son una sola bolsa**: son acciones de docenas de emisores con sede y cotización primaria dispersas por el mundo, negociadas en Cboe Europe como plataforma de cruce secundaria. Ejemplos identificables directamente por el nombre de la empresa:

| Origen probable de la cotización primaria | Ejemplos en la muestra |
|---|---|
| Estados Unidos (NYSE/Nasdaq) | JD.com, CMS Energy, Boeing, Meta Platforms, 3M, McKesson, Stryker, Capital One, BlackRock, Twilio, Square, General Dynamics, Keurig Dr Pepper, Trimble, Deckers Outdoor, Huntington Ingalls, Hercules Capital, Photronics, Hain Celestial, Cousins Properties |
| Alemania (Xetra/Frankfurt) | Deutsche Boerse AG, Deutsche Lufthansa AG, Henkel, Siemens, Rational AG, IONOS Group, Gerresheimer, Wienerberger, OHB SE, Thyssenkrupp Nucera, Eckert & Ziegler |
| Suiza (SIX) | UBS Group AG, Swisscom, SIG Group, Ypsomed, Alpine Select, Bossard Holding, Schlatter Industries, Banque Cantonale de Genève |
| Francia (Euronext Paris) | Dassault Systèmes, Thales, Vallourec, Société française de Casinos, Hopium, Coheris |
| Países nórdicos (Nasdaq Stockholm/Copenhague/Helsinki, Oslo Børs) | Neste, Sampo, Sandvik, Ambu, Apetit, Orkla, Europris, VBG Group, Zinzino, North Energy |
| Reino Unido (LSE/AIM) | British American Tobacco, Morgan Advanced Materials, Morgan Sindall, Future PLC, Genel Energy, Cairn Homes |
| Polonia (GPW Varsovia) | Asseco South Eastern Europe, NEWAG, Mirbud, Krynica Vitamin, Vistal Gdynia |
| Hong Kong / China | China Gas Holdings, China Unicom Hong Kong, Dongjiang Environmental, Shanghai Jin Jiang |
| Otros (Canadá, Brasil, Italia, Bélgica, España, Irlanda, Austria, Eslovenia) | Celestica, Pembina Pipeline, Teck Resources, Centrais Eletricas Brasileiras, Ferrari NV, Lotus Bakeries, Recticel, Realia Business, Palfinger, Petrol DD Ljubljana |

**Consecuencia práctica:** no existe "una fuente oficial de Cboe Europe" que resolver. El camino correcto sería, primero, identificar la bolsa de cotización primaria real de cada una de las 119 empresas (trabajo de mapeo de identificadores vía OpenFIGI, ya aprobado en v2.33C, no ejecutado aquí para no introducir equivalencias dudosas), y solo después evaluar la fuente oficial de esa bolsa concreta. Esta evaluación se limita a comprobar, para las bolsas más representadas identificables a simple vista, si existe siquiera una fuente oficial gratuita a la que merezca la pena apuntar ese trabajo futuro.

## Hallazgos por mercado

### Japón / JPX (42 símbolos bloqueados) — candidata prometedora

**J-Quants API** es un servicio oficial de **Japan Exchange Group (JPX)**, el operador de la Bolsa de Tokio, distribuido directamente desde `jpx-jquants.com`.

- Plan gratuito confirmado: **2 años de histórico diario (OHLC), excluyendo las 12 semanas más recientes** (es decir, los datos llegan con ~3 meses de retraso, pero el histórico disponible una vez llega es de 2 años, no de 1 como en EODHD gratuito).
- Términos de uso: permite análisis personal y publicar los resultados propios del análisis; **prohíbe expresamente redistribuir o compartir los datos en bruto** y **prohíbe proveer de forma repetida resultados de análisis derivados a terceros**.
- Requiere crear una cuenta gratuita para obtener credenciales — **no se ha creado ninguna cuenta en esta evaluación**; requeriría autorización explícita del usuario antes de dar ese paso.
- Sigue existiendo el mismo tipo de trabajo pendiente que con EODHD: resolver el código de catálogo J-Quants para cada uno de los 42 tickers JPX (equivalente al motivo `requires_eodhd_exchange_catalog_confirmation` ya registrado), aunque el catálogo y las reglas de mapeo serían distintos.

Fuentes: [J-Quants API | JPX](https://www.jpx.co.jp/english/markets/other-data-services/j-quants-api/index.html), [J-Quants](https://jpx-jquants.com/en).

### Taiwán / TWSE (8 símbolos ya resueltos, profundidad limitada por EODHD) — candidata a mejorar la profundidad ya existente

- El **OpenAPI oficial de TWSE** (`openapi.twse.com.tw`) es gratuito y sin registro, pero **solo devuelve el último día de cotización**; no sirve para histórico multianual directamente.
- El **portal de datos abiertos del gobierno de Taiwán** (`data.gov.tw`), con el dataset "Individual stock daily closing prices and monthly average prices" de la Comisión de Valores y Futuros (Securities and Futures Bureau), es **oficial, gratuito, se actualiza a diario** (última actualización observada: 2026-08-19) y ofrece **API y descarga CSV**, bajo licencia de datos abiertos gubernamentales (Open Government Data License v1.0).
- **No confirmado:** la fecha de inicio real de la serie histórica del dataset (el portal muestra "publicado por primera vez: 2017-05-23", que es la fecha de alta del dataset en el catálogo, no necesariamente el primer dato de precio disponible). Requeriría inspección directa del propio dataset para confirmar profundidad real.

Esta vía no resuelve ningún símbolo nuevo, pero podría mejorar la profundidad histórica de los 8 activos TWSE ya descargados sin depender de EODHD para ellos.

Fuentes: [TWSE OpenAPI](https://openapi.twse.com.tw/v1/swagger.json), [data.gov.tw — Individual stock daily closing prices](https://data.gov.tw/en/datasets/11548).

### Alemania / Xetra (parte de los 119 de Cboe Europe) — sin alternativa gratuita viable

- Deutsche Börse Market Data + Services vende su histórico oficial (Xetra, Eurex, índices DAX/STOXX) como producto de pago; no se encontró una API gratuita equivalente vigente.
- Existe un "Deutsche Börse Public Dataset" en el catálogo de datos abiertos de AWS, pero está **marcado como obsoleto y sin mantenimiento** ("the provider of this dataset will no longer maintain this dataset"), solo contiene barras de 1 minuto (no EOD directo) y su licencia es explícitamente **no comercial**. No es una alternativa viable ni actual.

Fuentes: [Deutsche Börse Public Dataset — AWS Open Data Registry](https://registry.opendata.aws/deutsche-boerse-pds/).

### Australia / ASX (13 símbolos ya resueltos, profundidad limitada por EODHD) — sin alternativa gratuita encontrada

No se encontró ninguna fuente oficial gratuita de ASX; toda la oferta identificada es de pago (LSEG Datastream, EODHD comercial desde 399 €/mes, ICE Data Services). ASX no distribuye directamente un canal gratuito equivalente al de Taiwán o Japón.

### Colombia / BVC (1 símbolo bloqueado) — sin alternativa gratuita encontrada

No se encontró ninguna API oficial gratuita de BVC. Solo agregadores comerciales (Investing.com, ICE, Yahoo Finance) y el sistema regulatorio SIMEV de la Superintendencia Financiera, que no parece exponer una API pública de precios. Dado que afecta a un único símbolo, es de bajo impacto para el piloto.

## Clasificación de la evidencia

**Hechos observados** (de páginas oficiales o fuentes primarias citadas):
- J-Quants (JPX) es un servicio oficial, gratuito, con 2 años de histórico diario excluyendo las últimas 12 semanas, y términos que prohíben la redistribución de datos en bruto.
- El OpenAPI oficial de TWSE solo devuelve el último día; el portal de datos abiertos del gobierno de Taiwán sí ofrece un dataset de precios diarios actualizado a diario, gratuito y con API.
- El Deutsche Börse Public Dataset en AWS está descatalogado, es de 1 minuto y de licencia no comercial.
- No se encontró ninguna fuente oficial gratuita para ASX ni para BVC en esta pasada de investigación.

**Inferencias:**
- Los 119 símbolos de "Cboe Europe" no comparten una única bolsa de origen; resolverlos exige primero un mapeo de identificadores por empresa, no una única fuente de datos.
- Las bolsas europeas principales (Alemania, Reino Unido, Francia, Suiza, países nórdicos) monetizan su dato de mercado oficial casi universalmente; no parece existir, en general, un patrón de "datos abiertos gubernamentales" para bolsas europeas equivalente al de Taiwán.

**Limitaciones no confirmadas:**
- Profundidad histórica real (fecha de inicio) del dataset de Taiwán en `data.gov.tw` — solo se confirmó la fecha de alta del dataset en el catálogo, no la fecha del primer precio disponible.
- Alcance exacto de la restricción de J-Quants sobre "no proveer de forma repetida resultados de análisis derivados a terceros" frente al uso interno y privado que le daría Scout Finance — no se ha confirmado por escrito con JPX.
- Cobertura completa de bolsas europeas: esta evaluación solo comprobó Alemania (Xetra) en profundidad; Reino Unido, Francia, Suiza y los mercados nórdicos no se investigaron uno a uno con el mismo detalle, así que no se descarta que exista alguna excepción puntual no encontrada aquí.

**Requisitos para profundizar (no ejecutados aquí):**
- Crear una cuenta gratuita en J-Quants para confirmar en la práctica la profundidad de 2 años, el retraso de 12 semanas y el formato real de los datos — requiere autorización explícita del usuario antes de proceder (creación de cuenta).
- Descargar o inspeccionar directamente el dataset de `data.gov.tw` para confirmar su fecha de inicio real.
- Ejecutar el mapeo de identificadores (OpenFIGI) de los 119 símbolos de Cboe Europe antes de poder evaluar fuente por fuente cada bolsa de origen real.

## Decisión

No hay una fuente oficial gratuita única que resuelva el problema completo. Hay dos candidatas concretas que merecen una evaluación más profunda si el usuario lo autoriza:

1. **J-Quants (JPX/Japón):** la más prometedora encontrada — oficial, gratuita, 2 años de histórico (mejor que el ~1 año de EODHD), pero con retraso de 12 semanas y trabajo de resolución de tickers pendiente.
2. **Datos abiertos del gobierno de Taiwán (`data.gov.tw`):** oficial, gratuita, actualizada a diario; podría mejorar la profundidad de los 8 activos TWSE ya resueltos sin resolver símbolos nuevos.

Para Cboe Europe (el bloque más grande, 119 símbolos), ASX y BVC, **no se ha encontrado ninguna fuente oficial gratuita viable** en esta pasada de investigación.

Esta evaluación **no** autoriza crear cuentas, ejecutar descargas, ni iniciar ningún piloto real con J-Quants o con el portal de Taiwán — eso requeriría una decisión explícita y acotada del usuario, igual que se hizo con EODHD en v2.33D.

## Estado del roadmap

- No cambia el estado de v2.33D1 (`COMPLETED_NO_PROMOTION` para EODHD, definitivo) ni el de v2.33E (Twelve Data gratuito descartado).
- Progreso global: 3/8 fases cerradas, fase 4 sigue en curso.
- Siguiente paso abierto (no ejecutado): decidir si se autoriza (a) crear una cuenta gratuita en J-Quants para un piloto acotado sobre los 42 símbolos JPX, y/o (b) inspeccionar el dataset de Taiwán para confirmar su profundidad real antes de plantear sustituir la fuente de los 8 activos TWSE.
