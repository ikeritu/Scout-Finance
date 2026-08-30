# v2.33G — piloto real de precios J-Quants (JPX / Japón)

Estado: **`PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado a JPX/Japón**. No es una promoción a producción ni resuelve el problema global de precios de Scout Finance.

## Resultado

- 42/42 símbolos JPX resueltos por coincidencia exacta de nombre de empresa (0 emparejamientos dudosos).
- 42/42 activos descargados, 0 fallos.
- 20.228 observaciones numéricas válidas.
- Ventana confirmada por el proveedor: 2024-06-08 → 2026-06-08 (2 años, 12 semanas de retraso).
- Cobertura de la mediana de sesiones frente a la ventana confirmada: **99.18%** (supera el 90% de v2.33C).
- Limitación de licencia sin confirmar por escrito: prohíbe redistribuir datos en bruto y proveer resultados repetidos a terceros.
- No resuelve Cboe Europe (119 bloqueados), ni mejora ASX/TWSE/BVC.

## Archivos

- `scripts/resolve_jquants_price_pilot_v2_33g.py`: resolución determinista por coincidencia exacta de nombre, fail-closed, con reintento automático ante error 429.
- `scripts/download_jquants_price_pilot_v2_33g.py`: descarga real fail-closed, reanudable, atómica.
- `scripts/build_jquants_collection_report_v2_33g.py`: validador local + generador del informe agregado.
- `tests/qa_jquants_price_pilot_collection_v2_33g.py`: QA local de los 42 históricos reales (requiere los JSON locales; no falla CI si no están presentes).
- `tests/qa_jquants_price_pilot_downloader_v2_33g.py`: QA sin red del pipeline completo (mocks, sin credenciales reales).
- `jquants_symbol_resolution_v2_33g.csv` / `jquants_symbol_resolution_report_v2_33g.json`: resultado de la resolución.
- `jquants_collection_report_v2_33g.json` / `JQUANTS_COLLECTION_REPORT_v2_33g.md`: informe agregado (sin precios fila a fila).
- `PRICE_PILOT_STATUS_v2_33g.md`: decisión del gate, evidencia e incidentes operativos.
- `jquants_prices_collection_v2_33g/`: JSON brutos por activo — **local, licenciado, no versionado** (ignorado en `.gitignore`).
