# v2.49H — un archivo de velas dañado ya no tumba la pantalla explosiva

Estado: `EXPLOSIVE_OHLCV_HARDENING_COMPLETED`. Responde al caso «CSV vacío, corrupto» de la matriz de pruebas del informe de QA del 16-oct. No cambia score, niveles ni datos.

## Hecho observado (antes del cambio)
`load_explosive_candidate_ohlcv` leía el CSV de velas sin protección. Probado con archivos dañados en la caché de velas:

| Archivo | Resultado antes |
|---|---|
| Vacío | `EmptyDataError`: se caía la página (gráfico destacado y ficha) |
| Bytes que no son UTF-8 | `UnicodeDecodeError`: se caía |
| Comillas sin cerrar | `ParserError`: se caía |
| Solo cabecera | funcionaba (sin filas) |

El endurecimiento de v2.49D cubría la caché de mercado, no estos archivos.

## Qué cambia
- Un archivo ilegible **de la caché propia de la app** se aparta como `<id>.csv.corrupt-<fecha>` (con los bytes tal cual, nunca se borra ni se sobrescribe en silencio) y se sigue con la siguiente fuente. La pantalla dice que no hay histórico local, y la siguiente búsqueda reconstruye el archivo.
- Un archivo ilegible de las carpetas de adquisición (`v2_38i`, `v2_38o`) **no se renombra**: se salta y queda donde estaba.
- Las fechas duplicadas se colapsan (gana la última barra de cada fecha).
- Un archivo sin ninguna fila utilizable pasa a la siguiente fuente en vez de devolver un gráfico vacío.

## Verificación
`tests/qa_explosive_ohlcv_hardening_v2_49h.py` (5 casos): los tres daños, apartado sin pérdida de bytes, paso a la siguiente fuente, carpetas de adquisición intactas, fechas duplicadas, y la app real con todos los archivos de velas dañados (el panel destacado y la ficha abren sin excepción). Se comprobó que la prueba falla sin el cambio.

## Fuera de alcance (anotado)
- Identificadores duplicados: hoy no hay ninguno entre las 141 empresas; si dos filas compartieran identificador, Streamlit fallaría por claves de botón repetidas.
- Accesibilidad con teclado/lector de pantalla, zoom 200 %, Firefox/Safari y rendimiento: requieren pruebas manuales.
