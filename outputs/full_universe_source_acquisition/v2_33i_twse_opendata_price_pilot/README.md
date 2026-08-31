# v2.33I — piloto real de precios TWSE (datos oficiales de Taiwán)

Estado: **`PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado a los 8 activos TWSE ya resueltos**.

## Resultado

- 8/8 activos descargados, 0 fallos, sin credenciales (fuente pública oficial `www.twse.com.tw`).
- 29.472 observaciones válidas, mediana 4.076 sesiones/activo (>16 veces más que EODHD para estos mismos 8 activos).
- Fecha mínima real de la fuente confirmada por el propio proveedor: 2010-01-04.
- Sin ajuste por splits/dividendos (limitación conocida, a diferencia de EODHD/J-Quants).
- No resuelve Cboe Europe ni amplía símbolos ASX/TWSE más allá de los 8 ya conocidos.

## Archivos

- `scripts/download_twse_opendata_price_pilot_v2_33i.py`: descarga fail-closed, reanudable, atómica, sin credenciales.
- `scripts/build_twse_opendata_collection_report_v2_33i.py`: validador local + generador del informe agregado.
- `tests/qa_twse_opendata_price_pilot_v2_33i.py`: QA local de los 8 históricos reales (requiere los JSON locales; no falla CI si no están presentes).
- `tests/qa_twse_opendata_downloader_v2_33i.py`: QA sin red del descargador (mocks, conversión de fecha ROC, parseo numérico).
- `twse_opendata_collection_report_v2_33i.json` / `TWSE_OPENDATA_COLLECTION_REPORT_v2_33i.md`: informe agregado (sin precios fila a fila).
- `PRICE_PILOT_STATUS_v2_33i.md`: decisión del gate, evidencia e incidentes técnicos (certificado SSL).
- `twse_opendata_prices_collection_v2_33i/`: JSON brutos por activo — local, no versionado (ignorado en `.gitignore`, por consistencia con el resto del proyecto aunque la licencia es abierta).
