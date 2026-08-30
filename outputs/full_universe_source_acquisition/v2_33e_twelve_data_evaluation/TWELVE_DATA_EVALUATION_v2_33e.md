# Scout Finance v2.33E — evaluación de Twelve Data como alternativa gratuita a EODHD

Fecha: 2026-08-31. Alcance: **investigación documental pública únicamente**. No se ha creado ninguna cuenta en Twelve Data, no se ha generado ni usado ninguna clave, no se ha ejecutado ninguna llamada a su API, no se ha descargado ningún dato y no se ha gastado dinero. Esta evaluación no autoriza scoring, rankings, recomendaciones de inversión, contratación de ningún plan, ni el inicio de la fase 5.

## Por qué se evalúa

Tras el cierre de v2.33D1 (`COMPLETED_NO_PROMOTION`), EODHD queda descartado en su plan gratuito por profundidad histórica insuficiente (~1 año). El usuario ha descartado explícitamente contratar un plan de pago de EODHD. v2.33C ya había señalado Twelve Data como "alternativa de contraste o contingencia, no primaria inicialmente". Esta evaluación decide, con evidencia pública verificable, si el **plan gratuito** de Twelve Data podría servir como fuente de precios mundiales.

## Fuentes consultadas

- [Individual Pricing](https://twelvedata.com/pricing)
- [API Documentation](https://twelvedata.com/docs)
- [Trial | Twelve Data Support](https://support.twelvedata.com/en/articles/5335783-trial)
- [Twelve Data | Exchanges](https://twelvedata.com/exchanges)
- [Twelve Data | Australian Securities Exchange (XASX)](https://twelvedata.com/exchanges/XASX)
- [Twelve Data | Taiwan Stock Exchange (XTAI)](https://twelvedata.com/exchanges/XTAI)
- [Twelve Data | Cboe Europe Equities (BCXE)](https://twelvedata.com/exchanges/bcxe)
- [Twelve Data | Tokyo Stock Exchange (XJPX)](https://twelvedata.com/exchanges/XJPX)
- [Terms of use](https://twelvedata.com/terms)

## Hallazgo central: el plan gratuito es solo de EE. UU.

El plan Basic (gratuito) de Twelve Data da acceso a **"real-time data for all US markets, forex, and cryptocurrencies"**. Los mercados internacionales de renta variable están excluidos del plan gratuito por completo, no solo limitados en profundidad. Verificado exchange por exchange, con el badge de nivel mínimo requerido mostrado literalmente en cada página:

| Mercado | Presencia en el piloto v2.33D1 | Nivel mínimo requerido en Twelve Data |
|---|---:|---|
| Estados Unidos (NASDAQ, NYSE, NYSE American, Cboe BZX) | 56/77 resueltos | **Basic** (incluido en el plan gratuito) |
| ASX (Australia) | 13/77 resueltos | **Pro+ / Venture+** |
| TWSE (Taiwán) | 8/77 resueltos | **Pro+ / Venture+** |
| Cboe Europe | 119/162 bloqueados | **Pro+ / Venture+** (o add-on de pago) |
| JPX (Japón) | 42/162 bloqueados | **Pro+ / Venture+** |
| BVC (Colombia) | 1/162 bloqueado | No verificado directamente; mismo patrón esperado (no Basic) |

Pro+/Venture+ empiezan en 29 USD/mes (nivel Grow) y suben según el mercado; algunos mercados exigen niveles superiores (Ultra/Enterprise).

## Consecuencia directa para nuestro caso de uso

- **0 de los 162 símbolos actualmente bloqueados** (Cboe Europe, Japón, Colombia) serían accesibles con el plan gratuito de Twelve Data. Resolver su ambigüedad de ticker no cambiaría esto: el bloqueo pasaría de "símbolo no resuelto" a "mercado no incluido en el plan gratuito".
- Solo los **56/77 símbolos ya resueltos y ya cubiertos por EODHD** (los estadounidenses) serían consultables en el plan gratuito de Twelve Data. Los 21 restantes ya resueltos (ASX 13 + TWSE 8) tampoco estarían disponibles.
- Twelve Data gratuito, por tanto, **no amplía la cobertura mundial** que motivó esta evaluación. En el mejor de los casos, duplicaría — con condiciones y profundidad histórica distintas y no confirmadas — una parte de lo que EODHD ya entrega para EE. UU.

## Otros datos relevantes (limitados a la parte estadounidense)

- Límite de tasa: 8 créditos/minuto, 800 créditos/día; una llamada `time_series` cuesta 1 crédito por símbolo, independiente del `outputsize`. Para 56 símbolos, el cupo diario sobraría ampliamente.
- Profundidad histórica en plan Basic: **no confirmada de forma fiable**. La documentación pública de Twelve Data no especifica un límite de años para el plan gratuito; una fuente secundaria (no una cita directa de Twelve Data) menciona una posible restricción de aproximadamente 2 años en el plan Basic, pero no se ha podido verificar contra la documentación oficial ni contra una llamada real (no se ha creado cuenta). Esto queda como **limitación no confirmada**, no como hecho.
- Licencia: los términos de uso conceden una licencia limitada para "Internal Use" (acceder, procesar y almacenar los datos). Es compatible en principio con un uso de investigación personal, pero no se ha revisado el documento completo de términos ni se ha confirmado por escrito que cubra el caso de uso exacto de Scout Finance (almacenamiento en caché, generación de resultados derivados). Igual que con EODHD, esto requeriría confirmación explícita antes de cualquier piloto real.

## Clasificación de la evidencia

**Hechos observados** (citas directas de páginas oficiales de Twelve Data):
- El plan Basic da "real-time data for all US markets, forex, and cryptocurrencies" únicamente.
- ASX, TWSE, Cboe Europe y JPX muestran el badge "Pro+ / Venture+" como nivel mínimo, no "Basic".
- El plan Basic tiene 8 créditos/minuto y 800/día; `time_series` cuesta 1 crédito por símbolo.

**Inferencias:**
- Ningún símbolo de los 162 actualmente bloqueados en el piloto v2.33D1 podría resolverse ni descargarse con el plan gratuito de Twelve Data, porque el bloqueo pasaría de "ambigüedad de ticker" a "mercado fuera del plan gratuito".

**Limitaciones no confirmadas:**
- Profundidad histórica exacta del plan Basic para símbolos estadounidenses (posible límite de ~2 años, sin confirmar en fuente oficial).
- Alcance exacto de la licencia "Internal Use" para un caso de investigación personal con caché local y resultados derivados.
- Cobertura exacta de BVC (Colombia) — no se encontró una página de exchange específica verificada en esta pasada.

**Requisitos para profundizar (no ejecutados aquí):**
- Cualquier verificación adicional (profundidad histórica real, alcance exacto de licencia) requeriría crear una cuenta gratuita y/o consultar el texto completo de términos — no autorizado por esta evaluación sin decisión explícita del usuario, y en cualquier caso limitado a la parte estadounidense, que ya está cubierta por EODHD.

## Comparación frente al contrato de v2.33C

| Criterio v2.33C | Umbral | Twelve Data (plan gratuito) | Cumple |
|---|---|---|---|
| Cobertura histórica de precios | ≥ 90% | No aplicable de forma global: 0% para mercados no estadounidenses (excluidos por plan); no confirmada para EE. UU. | **No** |
| Emparejamiento correcto de símbolos | ≥ 90% | No aplicable: el plan gratuito no permite siquiera consultar el 100% de los mercados donde tenemos símbolos por resolver | **No** |
| Cobertura fundamental | ≥ 75% | No evaluada (fuera de alcance de esta evaluación) | No evaluado |
| Licencia y retención documentadas | Documentado | Licencia "Internal Use" genérica, sin confirmación específica por escrito | **No** |

## Decisión

**Twelve Data, en su plan gratuito, no es una alternativa viable como fuente mundial de precios para Scout Finance.** No es un fallo de profundidad histórica (como EODHD) sino un fallo de **cobertura de mercado**: el plan gratuito excluye por completo todos los mercados no estadounidenses que representan el problema real (162 símbolos bloqueados + 21 ya resueltos en ASX/TWSE). No se recomienda invertir más tiempo en Twelve Data gratuito para este objetivo.

Esta decisión no descarta Twelve Data como fuente de pago en una eventual y futura decisión explícita del usuario — pero el usuario ya ha descartado planes de pago de EODHD, y no se ha planteado uno para Twelve Data en esta conversación, así que **no se recomienda ni se evalúa ninguna vía de pago aquí**.

## Estado del roadmap

- No cambia el estado de v2.33D1 (`COMPLETED_NO_PROMOTION` para EODHD, definitivo).
- Progreso global: 3/8 fases cerradas, fase 4 sigue en curso.
- Esta evaluación no autoriza ninguna fase nueva, scoring, ranking, ni la contratación de ningún plan.
- Siguiente paso abierto (no ejecutado): si se quiere una fuente mundial gratuita real, habría que evaluar otros candidatos no considerados todavía en v2.33C (por ejemplo, fuentes oficiales por bolsa, u otros agregadores), o aceptar que ninguna fuente gratuita actual cubre el universo mundial del piloto y decidir cómo proceder con la fase 4 en esas condiciones.
