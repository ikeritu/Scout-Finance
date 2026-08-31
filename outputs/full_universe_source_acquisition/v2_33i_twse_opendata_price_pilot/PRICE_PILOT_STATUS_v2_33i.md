# Scout Finance v2.33I — piloto real de precios TWSE (datos oficiales de Taiwán)

Estado: **`PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado exclusivamente a los 8 activos TWSE ya resueltos**. No es una promoción a producción, no autoriza scoring, rankings, recomendaciones de inversión, fundamentales, incorporación masiva de precios, contratación de planes de pago, conexión con brokers ni el inicio de la fase 5.

## Por qué se hizo

v2.33F identificó el endpoint oficial `STOCK_DAY` de la Bolsa de Taiwán (TWSE, `www.twse.com.tw`) como candidato para mejorar la profundidad histórica de los 8 activos TWSE ya resueltos en v2.33D (descargados vía EODHD con solo ~243 sesiones, ~1 año). Este piloto lo prueba en la práctica.

## Trabajo realizado

1. **Validación mínima** (3 llamadas de sondeo): confirmó que el endpoint es gratuito, oficial, sin cuenta ni clave, devuelve OHLCV real por mes/activo, y que el límite real de profundidad es **2010-01-04**, declarado explícitamente por el propio TWSE al pedir una fecha anterior (`"查詢日期小於99年1月4日，請重新查詢!"`).
2. **Incidencia técnica resuelta:** la primera llamada real falló por `SSLCertVerificationError` (certificado con "Subject Key Identifier" incompleto del lado de TWSE); se resolvió usando el almacén de certificados de `certifi` en vez del almacén por defecto de Windows — sin desactivar la verificación SSL.
3. **Descarga real completa** (`scripts/download_twse_opendata_price_pilot_v2_33i.py`), fail-closed, reanudable, con escritura atómica: **8/8 activos, ~200 meses cada uno desde 2010-01-04, 0 fallos** en la ejecución final (1 mes falló de forma transitoria en la primera pasada para un activo; se reintentó ese único activo completo y quedó limpio).
4. **Validación local** (`scripts/build_twse_opendata_collection_report_v2_33i.py` + `tests/qa_twse_opendata_price_pilot_v2_33i.py`): 8/8 válidos, 0 errores de esquema, 0 incoherencias OHLC, 0 volúmenes negativos.
5. **QA sin red** (`tests/qa_twse_opendata_downloader_v2_33i.py`): conversión de fecha ROC→gregoriana, parseo numérico con separadores de miles, bloqueo sin `--execute`, escritura atómica, omisión de archivos existentes sin llamar a la red, continuidad tras un error HTTP en un mes concreto. Todo con mocks, sin red.

## Cifras confirmadas (reproducidas localmente)

- Activos esperados: 8 · válidos: 8 · errores de esquema: 0.
- **Observaciones numéricas válidas: 29.472** — casi el doble de las 18.714 obtenidas con los 77 activos EODHD juntos, aquí con solo 8 activos.
- Sesiones por activo: **mínimo 1.378, máximo 4.082, mediana 4.076** — frente a la mediana de 250 de EODHD para estos mismos mercados: **más de 16 veces más profundidad**.
- 6/8 activos alcanzan la fecha mínima confirmada por el proveedor (2010-01-04); los otros 2 empiezan más tarde (2011-11-01 y 2020-12-24), coherente con cotizaciones más recientes.
- Fecha máxima observada: 2026-08-31 (prácticamente al día).
- 12 filas de calendario (de ~29.500) sin operación registrada (OHLC nulo), sin código explicativo — fracción marginal.

Detalle completo en `twse_opendata_collection_report_v2_33i.json` y `TWSE_OPENDATA_COLLECTION_REPORT_v2_33i.md`.

## Limitaciones conocidas

- **Sin ajuste por splits/dividendos:** el endpoint devuelve precios OHLC en bruto, sin un campo equivalente al `Adjusted_close` de EODHD o `AdjFactor`/`AdjClose` de J-Quants. Cualquier cálculo de rentabilidad a largo plazo que cruce un split o un dividendo grande necesitaría un ajuste que esta fuente no proporciona directamente.
- **Alcance limitado:** solo cubre los 8 activos TWSE ya resueltos. No aporta nada a Cboe Europe, ASX ni a los símbolos JPX ya cubiertos por J-Quants (v2.33G).
- **Sin límite de tasa publicado:** a diferencia de EODHD/J-Quants, este endpoint no tiene una política de límite documentada; se ha aplicado un ritmo propio prudente (0,8 s entre llamadas) para no sobrecargar un sitio público gubernamental. Un uso futuro más intensivo debería mantener esa cautela.
- **Licencia:** Open Government Data License v1.0 — licencia abierta, sin restricción de redistribución conocida (a diferencia de EODHD/J-Quants), aunque los JSON brutos se mantienen fuera de Git por consistencia con el resto del proyecto (solo se publican agregados).

## Evaluación frente al contrato de v2.33C (acotado a estos 8 activos TWSE)

| Criterio v2.33C | Umbral | Resultado real | Cumple |
|---|---|---|---|
| Cobertura histórica de precios | ≥ 90% | Profundidad multiplicada por >16 respecto a EODHD para el mismo activo; 6/8 alcanzan el límite real de la fuente (2010) | **Sí** |
| Emparejamiento correcto de símbolos | ≥ 90% | 8/8 (100%) — mismo ticker ya validado en v2.33D, sin ambigüedad | **Sí** |
| Cero emparejamientos falsos | 0 | 0 | **Sí** |
| Cobertura fundamental | ≥ 75% | No evaluada (fuera de alcance) | No evaluado |
| Licencia y retención documentadas | Documentado | Open Government Data License v1.0 — abierta, documentada | **Sí** |

## Decisión del gate

**`PASS_FOR_NEXT_CONTROLLED_PILOT`**, acotado a los 8 activos TWSE.

- Supera ampliamente los umbrales de v2.33C para estos activos concretos.
- **No** sustituye automáticamente la fuente TWSE de los 77 activos EODHD en producción: esta decisión no autoriza scoring, ranking, ni ningún uso productivo — solo confirma que la fuente es técnicamente superior y viable para un siguiente piloto controlado.
- No resuelve Cboe Europe, ASX ni amplía la cobertura de símbolos más allá de los 8 ya conocidos.

## Seguridad y alcance

- Sin credenciales de ningún tipo: fuente pública oficial del gobierno de Taiwán.
- Los JSON brutos permanecen fuera de Git (`outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_prices_collection_v2_33i/`, ignorado), por consistencia con el resto del proyecto.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de v2.33D1, v2.33E, v2.33F, v2.33G ni v2.33H.
- Progreso global: 3/8 fases cerradas, fase 4 en curso.
- Siguiente paso recomendado (no ejecutado, no autorizado por este cierre): decidir si se quiere plantear sustituir la fuente TWSE de EODHD por esta fuente oficial para los 8 activos correspondientes, y/o investigar si ASX tiene un endpoint oficial equivalente.
