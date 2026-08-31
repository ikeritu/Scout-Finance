# v2.33P — reparación de metadatos SGX y Xetra (Bloque E, fase 4)

Estado: **reparación de identidad completada; sin fuente de precios evaluada todavía**.

## Resultado

- **SGX (358 filas):** columnas ticker/nombre intercambiadas, confirmado al 100 %. Ticker real recuperado en 358/358 (100 %); nombre de empresa genuinamente ausente en la fuente, marcado como tal, no inventado.
- **Xetra (1.424 filas):** `company_name` contenía códigos de clasificación de segmento, no nombres. Reparado vía OpenFIGI por ISIN (fail-closed, exige coincidencia exacta entre todos los registros devueltos): **1.256/1.424 (88,2 %)** reparados con nombre real recuperado; 168 (11,8 %) siguen bloqueados (163 por discrepancia real entre fuentes, 5 sin registro).
- El censo canónico no se ha modificado; toda reparación vive en archivos delta separados.
- No se ha investigado ninguna fuente de precios para SGX ni Xetra en este bloque.

## Archivos

- `scripts/repair_sgx_schema_v2_33p.py`: reparación local determinista (sin red).
- `scripts/repair_xetra_schema_v2_33p.py`: reparación vía OpenFIGI (fail-closed, sin cuenta).
- `tests/qa_sgx_xetra_metadata_repair_v2_33p.py`: QA offline de ambos scripts.
- `sgx_repair_delta_v2_33p.csv`, `xetra_repair_delta_v2_33p.csv`, `xetra_repair_unresolved_v2_33p.csv`: resultados.
- `SGX_XETRA_METADATA_REPAIR_v2_33p.md`: detalle completo E1–E4.
