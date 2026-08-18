# Scout Finance v2.33C — fuentes para precios y fundamentales

Fecha de revisión: **18 de agosto de 2026**.

## Conclusión ejecutiva

No existe una fuente gratuita única que permita mantener datos financieros mundiales fiables para los 23.888 candidatos. Se adopta una arquitectura híbrida y se prohíbe contratar o activar proveedores automáticamente.

| Fuente | Función propuesta | Decisión |
|---|---|---|
| SEC/EDGAR | Fundamentales XBRL de emisores que presentan ante la SEC | Aprobada |
| OpenFIGI | Cruce de ticker, mercado e identificadores | Aprobada para piloto |
| EODHD | Precios mundiales y fundamentales no estadounidenses | Candidato preferente condicionado |
| Twelve Data | Muestra de contraste y contingencia | Condicionada, no primaria inicialmente |
| Alpha Vantage | Pruebas puntuales | Descartada como fuente gratuita principal |

## Fundamentales estadounidenses

La SEC ofrece las APIs `submissions`, `companyfacts`, `companyconcept` y archivos masivos nocturnos sin clave. Los datos XBRL se actualizan durante el día y la propia SEC recomienda los ZIP masivos para grandes volúmenes. Su política de acceso limita el tráfico automatizado a 10 solicitudes por segundo y exige identificar el agente de usuario.

Fuentes oficiales: [APIs de EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) y [recursos para desarrolladores de la SEC](https://www.sec.gov/about/developer-resources).

Decisión: usar el ZIP nocturno para la carga base y peticiones incrementales moderadas para cambios. Los hechos conservarán taxonomía, unidad, periodo, formulario, fecha de presentación y accession number.

## Identificadores

OpenFIGI es gratuito y no impone límites diarios o mensuales. Con clave admite 25 solicitudes cada seis segundos y hasta 100 trabajos por petición; sin clave, 25 solicitudes por minuto y 10 trabajos por petición.

Fuentes oficiales: [visión general](https://www.openfigi.com/api/overview) y [documentación/rate limits](https://www.openfigi.com/api/documentation).

Decisión: usarlo para enriquecer y validar identificadores, nunca para decidir automáticamente que dos cotizaciones son la misma empresa. Cero coincidencias falsas es requisito obligatorio del piloto.

## Proveedor global preferente

EODHD anuncia más de 70 bolsas, más de 150.000 tickers, históricos EOD y fundamentales mundiales. Su catálogo encaja mejor con la dispersión real de Scout Finance: Europa, Japón, Estados Unidos, Australia, Taiwán y Singapur.

Fuentes oficiales: [precios y planes](https://eodhd.com/pricing), [fundamentales](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds) y [bolsas compatibles](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours).

Decisión: no contratar todavía. Primero se debe verificar por escrito que el plan elegido permite análisis personal local, almacenamiento en caché y generación de resultados derivados. Después se probarán 240 activos estratificados.

## Alternativas de validación

Twelve Data documenta cobertura mundial de precios y fundamentales mediante créditos. Su plan gratuito anuncia 8 créditos por minuto y 800 diarios; los mercados y fundamentales más amplios dependen del nivel contratado. Se reserva como contraste o contingencia para evitar pagar dos universos completos desde el inicio.

Fuentes oficiales: [documentación](https://twelvedata.com/docs), [fundamentales](https://twelvedata.com/fundamentals), [planes de prueba](https://support.twelvedata.com/en/articles/5335783-trial) y [precios](https://twelvedata.com/pricing).

Alpha Vantage ofrece 25 solicitudes diarias en el nivel gratuito. Recorrer una sola vez 23.888 activos, suponiendo una petición por activo, requeriría aproximadamente 956 días; obtener precios y varios estados financieros multiplicaría ese plazo. Su modalidad premium publicada comienza en 75 solicitudes por minuto sin límite diario.

Fuentes oficiales: [límites](https://www.alphavantage.co/support/), [premium](https://www.alphavantage.co/premium/) y [documentación](https://www.alphavantage.co/documentation/).

Decisión: útil para muestras pequeñas, no como fuente gratuita principal.

## Piloto obligatorio antes de comprar

La muestra será de 240 activos, estratificada por proveedor, bolsa, región y calidad de identificadores. Debe superar:

- al menos 90 % de emparejamiento correcto;
- al menos 90 % de cobertura histórica de precios;
- al menos 75 % de cobertura fundamental;
- cero emparejamientos falsos;
- licencia y retención documentadas.

Si falla cualquiera de estos criterios, el proveedor no se promociona.

## Frecuencia operativa prevista

- precios ajustados: diariamente tras el cierre;
- fundamentales: detección semanal de cambios y actualización tras nuevas cuentas;
- identidad: actualización incremental semanal;
- sector y referencia: mensual;
- reconciliación completa: trimestral.

## Estado de seguridad

No se ha comprado ningún plan, introducido claves ni ejecutado adquisición. Scoring, rankings y recomendaciones siguen bloqueados.
