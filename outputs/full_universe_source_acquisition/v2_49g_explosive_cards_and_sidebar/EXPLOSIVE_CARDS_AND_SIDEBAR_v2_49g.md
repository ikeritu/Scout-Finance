# v2.49G — fichas como contenedor íntegro y barra lateral coherente

Estado: `EXPLOSIVE_CARDS_AND_SIDEBAR_COMPLETED`. Solo presentación: no cambia score, niveles, datos ni la navegación (los identificadores de pantalla son los mismos). Cierra los dos puntos que v2.49F dejó fuera del informe de diseño gráfico.

## DG-05 — la ficha como contenedor íntegro
- Cada ficha es ahora un contenedor con borde (`st.container(border=True, height="stretch")`) que lleva dentro el contenido y el botón «Ver ficha completa» como pie. Antes el botón era un elemento aparte bajo una caja de HTML.
- Los pies quedan alineados por fila sin imponer altura: las tarjetas de una fila se estiran hasta la más alta y el botón se ancla abajo con CSS (`margin-top: auto`). No hay `min-height` ni altura fija, así que un texto largo o el zoom no cortan nada. Se retira el `min-height: 270px` provisional de v2.49F.
- Se mantienen la puntuación «n/100», la etiqueta de nivel y el acento lateral del nivel (ahora aplicado al borde del contenedor).
- Comprobado en navegador con una búsqueda real sobre una copia de los datos: botones alineados en todas las filas con contenidos de distinta altura, y en móvil (375 px) las fichas se apilan sin problema.

## DG-07 — barra lateral
- Una sola familia de iconos funcionales (Material) para la navegación; el unicornio 🦄 queda como identidad de la sección.
- Etiqueta más corta: «Universo global (43.089)» pasa a «Universo global» (la cifra ya aparece en la propia pantalla). El resto del texto no cambia, incluidas las marcas de honestidad («Ranking global (experimental)», «Guía final y uso responsable»).
- «Datos: …» y «Fase 7: INSUFFICIENT_EVIDENCE» pasan a un desplegable discreto «Estado técnico»; «Sin conexión a broker» sigue siempre visible.

## Verificación
`tests/qa_explosive_cards_and_sidebar_v2_49g.py` (3 casos) más las pruebas de las secciones explosiva y de unicornios y las de la guía final y el ranking global, todas en verde.

## Límite
Esta comprobación visual es de Chrome embebido con una búsqueda real; no se ha probado con zoom del navegador del 200 %.
