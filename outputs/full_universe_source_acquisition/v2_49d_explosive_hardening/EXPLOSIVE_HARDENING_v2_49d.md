# v2.49D — robustez de la caché de mercado, leyenda honesta y botones con nombre propio

Estado: `EXPLOSIVE_HARDENING_COMPLETED`. Responde a los hallazgos FE-10, FE-04 y FE-09 de una revisión de frontend; el resto de hallazgos se evaluó y no se tocó (ver abajo).

## Qué se corrigió
| Hallazgo | Problema (reproducido) | Cambio |
|---|---|---|
| FE-10 | Un fichero de caché de mercado vacío o con bytes que no son UTF-8 hacía caer la página al buscar (`No columns to parse from file`, `utf-8 codec can't decode`): la lectura solo capturaba errores de disco y de formato. Además el guardado no era atómico, así que un corte a mitad dejaba justo ese fichero roto y la búsqueda fallaba cada vez. | La lectura trata cualquier `ValueError` como caché irrecuperable: la aparta como `…csv.corrupt-<fecha>` (nunca la sobrescribe en silencio) y la búsqueda la reconstruye. El guardado escribe un `.tmp` junto al destino y lo renombra, y lo borra si falla. |
| FE-04 | La leyenda del gráfico decía «Banda 95%», pero el cálculo es la recta ±1,96 desviaciones típicas de los residuos: no es un intervalo de confianza ni de predicción y no garantiza ese 95 % (los cierres están autocorrelacionados). | Las líneas se llaman «Recta ±1,96 desv. residuales» y bajo el gráfico se explica que son descriptivas y no un intervalo. |
| FE-09 | Nueve botones con el mismo nombre «Ver ficha completa». | «Ver ficha completa · TICKER»: nombre único por candidato (y más claro a la vista). La clave del botón no cambia. |

## Evaluado y no tocado
- **FE-01**: ya resuelto en v2.49B (paginación; no queda tope de 24).
- **FE-03**: el Top 3 ya declara su población desde v2.49C.
- **FE-02**: la población explosiva son los 141 unicornios de calidad, explícito en pantalla desde v2.49B. Ampliarla es decisión de producto.
- **FE-05** (eje de volumen), **FE-06** (tokens de estilo), **FE-07** (`use_container_width` obsoleto, 59 usos; mientras no se elimine, migrarlo es riesgo sin beneficio) y **FE-08** (rendimiento: la propia revisión no lo midió; no se añade caché sin medir).

## Pruebas
`tests/qa_explosive_hardening_v2_49d.py` (6 casos): caché vacía, caché con bytes corruptos (fichero apartado intacto y caché reconstruida), caché con solo cabecera (no se aparta), guardado interrumpido (el fichero anterior intacto y sin `.tmp`), leyenda sin «95» y con la explicación, y nombres de botón distintos. Comprobado que falla sobre el código anterior.
