# v2.33D — preparación del piloto de precios

Estado: **preparación completada · adquisición bloqueada hasta resolver símbolos y disponer de una clave autorizada**.

## Resultado

- población corregida: 21.165 candidatos;
- piloto: 240 activos únicos;
- muestreo proporcional de los 7 proveedores elegibles;
- símbolos del proveedor: pendientes de resolución;
- preflight de elegibilidad: 240/240 pasan;
- símbolos EODHD resueltos sin red: 78;
- símbolos ambiguos bloqueados: 162;
- claves almacenadas: ninguna;
- llamadas de adquisición: cero;
- filas de precios descargadas: cero.

## Archivos

- `price_pilot_sample_v2_33d.csv`: muestra determinista.
- `price_pilot_manifest_v2_33d.json`: estado reproducible.
- `price_pilot_symbols_v2_33d.csv`: símbolos resueltos y motivos de bloqueo.
- `symbol_resolution_report_v2_33d.json`: resumen de resolución.
- `PRICE_PILOT_STATUS_v2_33d.md`: bloqueos y siguiente acción.

El script `download_eodhd_price_pilot_v2_33d.py` solo acepta la clave mediante `SCOUT_FINANCE_EODHD_API_TOKEN`, exige `--execute` y se bloquea si queda cualquier símbolo sin resolver.
