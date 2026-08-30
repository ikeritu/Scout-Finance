# v2.33D / v2.33D1 — piloto real de precios EODHD

Estado: **v2.33D1 cerrado — `COMPLETED_NO_PROMOTION`**. Descarga real ejecutada y validada; EODHD (plan gratuito) no se promociona a producción. Ver `PRICE_PILOT_STATUS_v2_33d.md` para la decisión completa y su justificación.

## Resultado

- población corregida: 21.165 candidatos;
- piloto: 240 activos únicos;
- símbolos resueltos de forma determinista: **77/240**;
- excluido como producto no empresarial: **1/240** (`P014` / `ZSP.AX`);
- símbolos ambiguos bloqueados: **162/240**;
- descarga real autorizada: **77/77 activos, 0 fallos, 0 omitidos**;
- observaciones numéricas válidas: **18.714** (18.791 filas en bruto incluyendo una fila de aviso del proveedor por activo);
- profundidad histórica real: mediana de 250 sesiones por activo, máximo 253, ningún activo alcanza 2021;
- decisión del gate: **`COMPLETED_NO_PROMOTION`** (no supera el umbral de cobertura histórica de v2.33C);
- claves almacenadas: ninguna;
- scoring/ranking productivo: no autorizado.

## Archivos

- `price_pilot_sample_v2_33d.csv`: muestra determinista (240 activos).
- `price_pilot_manifest_v2_33d.json`: estado reproducible de la preparación.
- `price_pilot_symbols_v2_33d.csv`: símbolos resueltos y motivos de bloqueo.
- `symbol_resolution_report_v2_33d.json`: resumen de resolución (77 resueltos, 1 excluido, 162 bloqueados).
- `price_pilot_collection_77_v2_33d.csv`: manifiesto canónico de los 77 activos descargados.
- `price_pilot_collection_report_v2_33d1.json` / `PRICE_PILOT_COLLECTION_REPORT_v2_33d1.md`: informe agregado reproducible de los 77 históricos (sin precios fila a fila).
- `PRICE_PILOT_STATUS_v2_33d.md`: decisión del gate, evidencia y siguiente paso.
- `eodhd_prices_collection_77_v2_33d/`: JSON brutos por activo — **local, licenciado, no versionado** (ignorado en `.gitignore`).

El script `scripts/download_eodhd_price_pilot_v2_33d.py` solo acepta la clave mediante `SCOUT_FINANCE_EODHD_API_TOKEN`, exige `--execute`, se bloquea si queda cualquier símbolo sin resolver, es reanudable, omite archivos existentes, continúa tras errores HTTP o de esquema, y escribe cada JSON de forma atómica. QA sin red en `tests/qa_price_pilot_downloader_v2_33d.py`; validación local de los 77 históricos en `tests/qa_price_pilot_collection_v2_33d.py` (requiere los JSON locales; no falla CI si no están presentes).
