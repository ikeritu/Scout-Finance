# v2.38AJ — Europa: investigación de precios reales, hallazgo negativo confirmado (real, sin script nuevo)

Fecha: 2026-09-06. Alcance: investigar si existe hoy alguna vía oficial o genuinamente gratuita, con suficiente profundidad histórica y accesible sin scraping ni pago, para obtener precios reales de los 689 activos europeos (v2.38O/P siguen en 0/689 desde el inicio del proyecto).

## Antecedentes de este proyecto (fases anteriores, ya cerradas)

- **v2.33H (Cboe Europe / OpenFIGI)**: `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE` — se identificaron 89/119 empresas, pero el código de bolsa compuesto de OpenFIGI no es una señal fiable de mercado principal; ninguna fuente de precios accionable desbloqueada.
- **v2.33D1 (EODHD)**: `COMPLETED_NO_PROMOTION` — el plan gratuito limita el historial a ~1 año, insuficiente para el umbral de cobertura histórica de este proyecto (≥90%).
- **v2.33E (Twelve Data)**: descartado — su nivel gratuito solo cubre EE. UU./forex/cripto, ninguna bolsa europea.
- **v2.38O/P**: plan de adquisición de precios construido pero nunca ejecutado (`READY_FOR_COLLECTION`), bloqueado explícitamente por falta de una fuente accionable confirmada.

## Investigación real de hoy — cinco vías comprobadas, todas con resultado negativo real

### 1. Stooq.com

Fuente ampliamente conocida en la comunidad de análisis cuantitativo por su descarga CSV gratuita e histórica. **Comprobado en vivo con una petición HTTP simple**: el endpoint de descarga (`stooq.com/q/d/l/`) devuelve ahora un **reto real de "proof-of-work" en JavaScript** (cálculo de hash SHA-256 iterativo antes de conceder acceso) — una medida anti-automatización activa y deliberada, no un artefacto de la herramienta usada. Siguiendo la política ya establecida de este proyecto ante medidas anti-automatización reales, **no se ha intentado ningún rodeo** (no se ha implementado el cálculo de proof-of-work, que sería precisamente el tipo de evasión de detección que este proyecto rechaza).

### 2. Alpha Vantage

Nivel gratuito real, pero limitado a **25 peticiones/día** — con 689 activos, cubrir una sola vuelta del universo llevaría más de 27 días de ejecución continua sin margen para reintentos, ampliaciones futuras ni verificación. Descartado por impracticable a la escala de este proyecto, independientemente de su cobertura real de bolsas europeas (no confirmada).

### 3. London Stock Exchange (fuente oficial)

La LSE sí ofrece datos gratuitos oficiales, pero **solo cotizaciones con retraso de 15 minutos** — no hay ninguna oferta oficial de descarga masiva de historial de precios gratuita; el histórico completo es un producto de pago de LSEG (London Stock Exchange Group).

### 4. EODData.com (distinto de EODHD, ya descartado en v2.33D1)

Registro gratuito confirmado, pero **el histórico profundo ("hasta 30 años") está detrás de un muro de pago** ("Up to 30 years of historical data can be purchased") — el mismo patrón exacto ya descartado para EODHD en v2.33D1: nivel gratuito con profundidad histórica insuficiente, historial completo de pago.

### 5. Fuentes ya descartadas previamente, reconfirmadas sin cambios

Twelve Data (solo EE. UU. en gratuito) y Cboe Europe/OpenFIGI (sin señal fiable de mercado principal) siguen en el mismo estado ya documentado en v2.33E y v2.33H — no se ha encontrado ningún cambio que altere esas conclusiones.

## Conclusión

**Se confirma, con evidencia real y convergente de cinco fuentes distintas investigadas hoy, que no existe actualmente ninguna vía gratuita, con profundidad histórica suficiente y accesible sin scraping ni pago, para obtener precios reales del universo europeo.** Esto no es una limitación nueva de este bloque — es la reconfirmación directa, con evidencia fresca, de la misma conclusión ya alcanzada en v2.33H (fase 4) hace tiempo: **el precio de mercado europeo es, estructuralmente, un producto comercial en toda la industria**, sin una vía gratuita real y suficientemente profunda conocida hasta la fecha.

No se construye ningún script de recolección de precios en este bloque — hacerlo exigiría o bien pagar (contra la política ya establecida), o bien automatizar un reto anti-bot activo (scraping/evasión, contra la política ya establecida).

## Qué SÍ ha cambiado desde v2.33H, y qué no

Lo que ha cambiado desde la investigación original de Cboe Europe (v2.33H) es que **ahora sí tenemos identidad real y verificada** (ISIN, ticker real, home exchange) para 689/689 activos europeos (v2.38AB) — mucho mejor que la identificación parcial (89/119) de entonces. Pero esto no cambia el hallazgo de fondo: **conocer con precisión QUÉ empresa es cada activo no resuelve el problema de DÓNDE conseguir su precio histórico gratis** — son dos problemas independientes, y el segundo sigue sin una solución real conocida.

## Seguridad y alcance

- Red real usada: solo consultas de solo lectura durante la investigación (páginas públicas, y una comprobación HTTP real contra Stooq que confirmó el reto anti-bot).
- Ninguna cuenta creada, ninguna credencial solicitada ni usada.
- Sin scraping, sin resolución de retos anti-bot, sin pago.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_PRICE_DATA_RESEARCH_NO_VIABLE_FREE_SOURCE_CONFIRMED`.** Hallazgo negativo real, reforzado con evidencia nueva de cinco fuentes adicionales investigadas hoy — la conclusión de fases anteriores de este proyecto (no existe una fuente de precios europea gratuita y accionable) queda confirmada, no refutada.
