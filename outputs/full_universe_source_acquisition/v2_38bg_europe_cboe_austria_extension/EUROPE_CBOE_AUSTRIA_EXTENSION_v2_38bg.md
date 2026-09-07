# v2.38BG — Ampliación de Austria: 40/40 identidad real, fundamentales bloqueados por cuota real de firmenakte.at

Fecha: 2026-09-07. Alcance: segundo paso de la decisión "decide qué hacer con las 3.766 empresas nuevas" — extender Austria con las 40 empresas nuevas que reveló `v2.38BC` bajo `country=AT`, prácticamente todo el índice ATX de la Bolsa de Viena (Erste Group Bank, Raiffeisen Bank International, Verbund, Vienna Insurance Group, Telekom Austria, Lenzing, FACC, entre otras).

## Identidad: 40/40 resueltas, generalizando el método de Luxemburgo

Reutilizado el script generalizado `scripts/resolve_europe_company_registry_gleif_v2_38bf.py` (nueva generalización del método de Luxemburgo `v2.38AW` con las dos correcciones adicionales de `v2.38BB` — consulta con la primera palabra sin normalizar puntuación, reintento con dos palabras), esta vez con filtro de país `AT` en vez de `LU`, ya que estas filas de Cboe Europe tampoco tienen ISIN. **Resultado: 40/40 resueltas, 0 ambiguas, 0 sin resolver** — el mejor resultado de cualquier búsqueda GLEIF sin ISIN de todo este esfuerzo. Los números de Firmenbuch reales confirman el formato ya conocido de Austria (dígitos + letra de control, p. ej. `350921k` para Addiko Bank AG), consistente con `v2.38AF`.

## Fundamentales: bloqueados por un límite real de cuota, no un problema de conectividad

A diferencia de la degradación de conexión ya documentada en `v2.38AS` (fallos de conexión TCP/TLS), esta vez la API respondió con **HTTP 429 ("Too Many Requests")** de forma consistente en una prueba real de 3 empresas — confirmando que la cuota gratuita mensual de firmenakte.at (100 llamadas/mes, documentada desde `v2.38AI`) está agotada por el uso ya acumulado de este proyecto (20 empresas originales + reintentos de `v2.38AS` en tres ejecuciones reales). Es un hallazgo real y distinto, no una repetición del problema anterior. **No se insiste** — seguir llamando a una cuota ya agotada no serviría de nada y podría retrasar más su restablecimiento.

## Qué NO hace este bloque

No extrae ningún fundamental financiero de las 40 empresas nuevas — queda pendiente hasta que la cuota mensual de firmenakte.at se restablezca. No reconstruye `v2.38AL` ni `v2.38AM`.

## Pruebas offline

Reutiliza sin cambios las pruebas ya existentes del motor de emparejamiento (`v2.38BB`); no se han necesitado pruebas nuevas específicas para este bloque, dado que reutiliza `v2.38BF` (ya probado offline junto con Luxemburgo) sin modificaciones.

## Seguridad y alcance

Red real usada solo para las 40 consultas de identidad a GLEIF (gratis, sin cuenta) y 3 consultas de prueba a firmenakte.at (confirmando el 429 sin insistir más). Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `PARTIAL_EUROPE_CBOE_AUSTRIA_EXTENSION_FUNDAMENTALS_BLOCKED_QUOTA_EXHAUSTED`.** Identidad completa (40/40), fundamentales explícitamente pendientes del restablecimiento de la cuota mensual — el script ya existente (`run_europe_austria_fundamentals_v2_38ai.py`) es directamente reutilizable en cuanto la cuota se recupere, sin ningún cambio.
