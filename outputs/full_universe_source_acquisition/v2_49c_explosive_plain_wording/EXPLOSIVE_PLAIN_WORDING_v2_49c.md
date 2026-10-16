# v2.49C — redacción clara en los resultados explosivos y pestañas cortas

Estado: `EXPLOSIVE_PLAIN_WORDING_COMPLETED`. Solo textos y etiquetas (`app_v2_37.py`); no cambia el score ni los datos. Cierra los hallazgos UX-07, UX-08, UX-09 y UX-10 del informe de UX (UX-01, 02, 03, 04, 05 y 06 ya estaban en v2.49A y v2.49B).

## Qué cambia
| Hallazgo | Cambio |
|---|---|
| UX-07: «0 candidatos» conviviendo con «Dashboard de candidatos» y un podio | El resumen dice qué significan las cifras: «140 empresas con datos de mercado: 0 cumplen el umbral · 140 en vigilancia (con datos, sin llegar al umbral) · 1 sin datos suficientes.» Las cinco casillas pasan a Alto / Medio / Bajo / Vigilancia / Sin datos. La lista se llama «Empresas por revisar». |
| UX-07: «Ninguna señal crítica faltante» junto a «En vigilancia» | La tarjeta dice «Datos: completos, pero la puntuación no llega al umbral» (y «Faltan: …» solo cuando de verdad falta algo). |
| UX-08: fecha del cálculo fundamental frente a datos de mercado | Bajo el botón: «… Cálculo fundamental del 2026-10-16.» En el resumen: «Datos de mercado: Yahoo Finance, guardados el 2026-10-16 a las 21:34» (hora de guardado de la caché local). El texto «sin conexión de red» ya no aparece en esta pantalla. |
| UX-09: vocabulario interno | Fuera de pantalla: «Drivers» (ahora «Señales detectadas»), «contrato v2.45G», «fail-closed», `WATCH_ONLY`. El aviso de velas sin histórico ya no remite a «Actualizar datos reales» sino a «Buscar Unicornios explosivos». Los identificadores técnicos (`non_polygon_overlay`, contratos, proveedores) quedan solo en «Opciones avanzadas». |
| UX-10: pestañas largas en móvil | «Resumen» / «Datos» / «Gráfico» en lugar de «Por qué puntúa así» / «Ficha explosiva profesional» / «Precio y velas OHLCV». La ficha ya tenía su propia cabecera (empresa, ticker, score, estado) y el botón de volver arriba. |

## Verificado
- Navegador real con Yahoo (140 empresas): resumen, casillas, tarjeta y ficha con el texto nuevo; sin vocabulario interno en la página de resultados ni en la ficha; en móvil (375 px) la barra de pestañas ya no se desplaza, la página no desborda y el botón de volver queda arriba.
- `tests/qa_explosive_search_page_v2_49a.py` pasa a 15 casos: el resumen dice los tres grupos con palabras, la fecha de mercado y la fundamental aparecen por separado, no llegan nombres crudos de nivel, y ni los resultados ni la ficha contienen el vocabulario interno. Pruebas de v2.44B y v2.47B actualizadas a las etiquetas nuevas.

## Sin cambiar
«Desempate diversificado estable, no alfabético» sigue en el conteo (una prueba lo exige) aunque es lenguaje técnico; candidato a simplificar.
