# v2.33H — mapeo de identificadores de Cboe Europe (OpenFIGI)

Estado: **`PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`**. Identifica la empresa real detrás de 89/119 símbolos bloqueados de Cboe Europe, pero no habilita ninguna descarga de precios nueva: no hay forma fiable de determinar la bolsa primaria de la mayoría de ellas con los datos gratuitos disponibles.

## Resultado

- 89/119 (74.8%) empresas identificadas de forma inequívoca (coincidencia exacta de nombre contra un único `shareClassFIGI` de OpenFIGI).
- 30/119 sin identificar (29 sin coincidencia exacta, 1 ambiguo: BlackRock Inc).
- De las 89 identificadas, solo 13 tienen un único código de mercado candidato en OpenFIGI — y se ha comprobado que **ese código no corresponde de forma fiable al país/bolsa real** (el mismo código aparece en empresas de países distintos).
- Sin cuenta creada, sin clave usada, sin descarga de precios, sin gasto.

## Archivos

- `scripts/resolve_cboe_europe_identifiers_v2_33h.py`: resolución fail-closed vía búsqueda pública de OpenFIGI (sin cuenta ni clave), exige coincidencia exacta de nombre normalizado.
- `cboe_europe_identifier_mapping_v2_33h.csv`: resultado por símbolo (119 filas).
- `cboe_europe_identifier_mapping_report_v2_33h.json`: resumen agregado.
- `CBOE_EUROPE_IDENTIFIER_MAPPING_v2_33h.md`: hallazgos, evidencia y decisión completa.

Detalle completo en `CBOE_EUROPE_IDENTIFIER_MAPPING_v2_33h.md`.
