# v2.47B — pestañas en la ficha del candidato explosivo

Estado: `EXPLOSIVE_CANDIDATE_TABS_COMPLETED`. Solo presentación (`app_v2_37.py`); no cambia el score, los datos de mercado ni ningún fichero de salida. Se apoya en v2.47A (PR #7).

## El problema
Cada tarjeta de candidato escondía los mismos tres bloques en tres desplegables («Por qué puntúa así», «Ficha explosiva profesional», «Precio y velas OHLCV») **y además** tenía el botón «Ver a pantalla completa», cuya página repetía esos tres bloques apilados. Con 9 tarjetas eran 27 desplegables y 9 gráficos de velas ocultos en una pantalla donde la ficha de «Calidad fundamental» ya usaba pestañas. Y la página completa mostraba encima el panel resumen, el aviso de umbral y las velas del candidato destacado, que no aportan nada ahí.

## El cambio
- **Ficha del candidato** (`render_explosive_candidate_fullpage`): los tres bloques son ahora pestañas con las mismas etiquetas que tenían los desplegables. «Por qué puntúa así» reúne drivers, señales que faltan y qué revisar; «Ficha explosiva profesional» el informe, el checklist y la tabla; «Precio y velas OHLCV» el gráfico.
- **Tarjetas**: sin desplegables. El botón pasa a llamarse «Ver ficha completa» y es la única entrada al detalle.
- **Página abierta = solo la ficha**: no se pintan el panel resumen, el aviso de «ningún candidato alcanza el umbral», el título del dashboard, los filtros ni las velas del destacado. El control del motor (actualizar datos) se mantiene arriba.
- **Los filtros no se pierden**: Streamlit descarta el estado de un widget que no se dibuja, así que mientras la ficha está abierta se reasigna el valor de los tres filtros (`EXPLOSIVE_FILTER_KEYS`). Verificado: con «Empresas a mostrar» en 3, abrir una ficha y volver deja 3 tarjetas.
- La ficha se busca entre **todas** las filas puntuadas (antes, entre las filtradas): cambiar un filtro ya no expulsa a nadie de la ficha que está leyendo. Si el id ya no existe, vuelve al dashboard sin error.

## Medido en vivo (escritorio 1400 px, datos reales, 9 tarjetas)
- Desplegables en el dashboard: 4 medidos tras el cambio (filtros, metodología y contrato técnico); antes eran esos 4 más 3 por tarjeta, 31 en total (cálculo por el código, no medido).
- Gráficos Plotly en el dashboard: 1 medido (el del candidato destacado); antes 1 más uno por tarjeta, 10 (cálculo por el código). El de cada candidato solo se dibuja en su pestaña.
- Ficha: 3 pestañas, sin excepciones; el gráfico mide 930×360 dentro de su pestaña (sin el ancho cero que a veces tienen los gráficos en pestañas ocultas).
- Móvil (375 px): sin desbordamiento de la página, gráfico a 349 px; la barra de pestañas se desplaza dentro de su contenedor.
- No hay medida de altura «antes» comparable: el servidor de referencia ya no estaba disponible, así que las cifras de arriba son recuentos, no píxeles.

## Pruebas
`tests/qa_explosive_candidate_tabs_v2_47b.py` (tres pestañas con las etiquetas previas, tarjetas sin desplegables, búsqueda de la ficha y ids desconocidos, filtros vivos y panel oculto). `tests/qa_unicorns_primary_screen_v2_44b.py`: las aserciones de «desplegable» ahora exigen pestañas y «Señales presentes/faltantes» (solo existían en el desplegable de la tarjeta) pasan a «Drivers principales»/«Qué señales faltan», que son los mismos datos en la primera pestaña.

## Pendiente
Nada de esta lista. Los listados y la ficha de «Calidad fundamental» y la de «Unicornio explosivo» ya comparten estructura (lista o tarjetas → ficha con pestañas).
