# v2.49F — sistema visual coherente en la pantalla de Unicornios explosivos

Estado: `EXPLOSIVE_VISUAL_SYSTEM_COMPLETED`. Solo presentación: **no cambia el score, los niveles, los datos ni ninguna búsqueda.** Responde al informe de diseño gráfico 2D (DG-01…DG-08) en lo que afecta a esta pantalla.

## Qué cambia
| Punto | Antes | Ahora |
|---|---|---|
| DG-01 contraste | texto secundario `#94a3b8` sobre blanco (2,56:1) y textos de 10–11 px | tokens `#0f172a` / `#334155` / `#475569` (≥ 7:1) y acento de texto `#b45309`; ningún texto por debajo de 12 px |
| DG-02 puntuación | número suelto en las fichas | siempre «n/100» |
| DG-03 ámbar | color de nivel y de identidad a la vez | el ámbar es solo la identidad de la sección; el nivel es una etiqueta de texto con fondo suave verde azulado/gris |
| DG-04 geometría | radios y pesos tipográficos variados | radios 8/12/18 px y pesos 600/700/800 definidos como constantes |
| DG-06 botón | el botón grande seguía ocupando la cabecera con resultados | botón compacto una vez hay resultados (la página se redibuja tras la búsqueda) |
| DG-08 gráfico | volumen superpuesto al precio y banda siempre visible | volumen en su propio panel con eje «Volumen»; recta de regresión y banda como capa opcional («Mostrar recta de regresión y banda») |
| Podio | «Top 3» sobre las fichas | eliminado: la lista ordenada ya empieza por las mismas empresas. La nota «Ninguna supera el umbral explosivo» pasa a la línea de resumen |

Fuera de alcance a propósito: DG-05 (la ficha como contenedor íntegro) y DG-07 (iconos del menú lateral).

## Verificación
- `tests/qa_explosive_visual_system_v2_49f.py` (9 casos): contraste AA calculado sobre cada color de texto del bloque y sobre cada etiqueta de nivel; radios/pesos/tamaños; el ámbar no se usa como nivel; «/100» y etiqueta en las 9 fichas y en la cabecera de la ficha; sin podio; botón grande antes y compacto después; panel de volumen separado, banda con una sola entrada de leyenda y capa opcional; el interruptor existe y se puede apagar.
- Pruebas fijadas al podio actualizadas (47A, 44B, 49A). El arnés de 49A tolera el interruptor de gráfico que AppTest conserva de una página que ya no se dibuja (la app real no lo dibuja).
- Sin red: proveedor simulado y carpeta de datos temporal; la caché real no se toca.
