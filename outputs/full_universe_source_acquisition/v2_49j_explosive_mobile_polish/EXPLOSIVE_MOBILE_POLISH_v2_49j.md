# v2.49J — pulido a 375 px: título del gráfico y separación del pie de la ficha

Estado: `EXPLOSIVE_MOBILE_POLISH_COMPLETED`. Solo presentación: no cambia score, niveles ni datos. Sale de la comprobación a 375 px de v2.49I.

## Hechos observados (a 375 px, búsqueda real sobre una copia de los datos)
- Los enlaces a Yahoo Finance y Google Finance de las fichas y de la cabecera de la ficha caben en una línea y se leen bien; la clave del gráfico en texto se parte sola; el panel de volumen y la página no tienen scroll horizontal.
- La barra de herramientas del gráfico (cámara, zoom) se dibuja sobre el título «ARRY · velas locales» y lo tapa en parte.
- En las fichas el texto de «Datos: …» quedaba casi pegado al botón «Ver ficha completa».

## Qué cambia
- El título del gráfico deja de ir dentro de la figura: es una línea de texto encima del gráfico (escapada con `escape`) y la figura conserva solo una franja de 36 px arriba para la barra de herramientas. El nombre sigue en la figura como metadato.
- El pie de la ficha (el botón) lleva un relleno superior de 12 px: la separación mínima es la misma a cualquier ancho y el botón sigue anclado abajo en cada fila.

## Verificación
`tests/qa_explosive_mobile_polish_v2_49j.py` (4 casos): figura sin título interno y con franja de barra de herramientas; título como línea de texto en el panel destacado y en la ficha; el título pasa por `escape` antes de ser HTML; separación mínima del pie. Comprobado de nuevo en navegador a 375 px y a ancho de escritorio con una búsqueda real.

## Límite
La comprobación es en el navegador integrado con la emulación de móvil (375 px), no en un teléfono físico.
