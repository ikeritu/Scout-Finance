# v2.49A — página limpia de «Buscar Unicornios explosivos»

Estado: `EXPLOSIVE_SEARCH_PAGE_COMPLETED`. Solo la vista explosiva (`app_v2_37.py`); no cambia el score explosivo, los criterios ni la vista de calidad fundamental.

## Qué se pidió
En esa pantalla, una página limpia con título, una descripción breve y un botón grande «Buscar Unicornios explosivos»; al terminar la búsqueda, las fichas de los encontrados con el resto de la información como hasta ahora.

## Qué hace ahora
- **Antes de buscar**: título «Unicornios explosivos», descripción de dos líneas (con el aviso de que es investigación y no una recomendación) y el botón (940×150 px en escritorio, 349×110 en móvil). Sin indicadores, sin selector de modo, sin tarjetas.
- **Al pulsar**: barra de progreso («Analizando TICKER · n de N») y, al terminar, un resumen de la búsqueda, el panel de candidatos (cifras, categorías y Top 3) y las tarjetas con «Ver ficha completa», como hasta ahora. El botón sigue disponible para repetir la búsqueda.
- **Los resultados se conservan** al abrir y cerrar una ficha y al cambiar a calidad y volver; cada entrada desde el inicio vuelve a empezar en limpio. Una ficha abierta muestra solo la ficha.
- **Calidad fundamental** queda a un clic con «Ver unicornios de calidad fundamental» (al final de la página); entrar por la barra lateral sigue igual.
- **Opciones avanzadas** (proveedor, caché, CSV manual, contrato técnico) detrás de un interruptor al final. Es un interruptor y no un desplegable porque Streamlit no permite desplegables dentro de desplegables y ese panel los usa.
- El modo simple `?modo=unicornios` usa la misma página; su texto de ayuda explica el nuevo flujo.

## Cambio de comportamiento que conviene conocer
La búsqueda consulta **todos** los unicornios con ticker (140 de 141), no la muestra fija de 40 que usaba «Actualizar datos reales». Esa muestra era determinista, así que repetirla nunca exploraba el resto: la caché se había quedado en 62 filas y la pantalla mostraba 51 empresas con datos. Con la búsqueda completa hay 140.

## Verificado
- En vivo, con Yahoo real: 140 de 140 con datos de mercado, 0 sin respuesta, 1 sin ticker consultable; unos 90 segundos; sin excepciones. Resultado: 0 candidatos explosivos, 140 en vigilancia, Top 3 de 44, 38 y 33 sobre 100.
- En el navegador real, una ficha abierta oculta cabecera, botón y panel resumen, y «Volver al dashboard» devuelve los resultados sin buscar de nuevo.
- `tests/qa_explosive_search_page_v2_49a.py` (7 casos, motor de pruebas de Streamlit con un proveedor simulado y la carpeta de datos redirigida): página limpia, búsqueda sobre todos los buscables, supervivencia de resultados, calidad y vuelta, fallo del proveedor sin caída, reinicio desde el inicio y modo simple. Comprueba además que la caché real del usuario no se toca.
- Para esa redirección se añadió la variable de entorno `SCOUT_FINANCE_DATA_DIR` (sin definir, todo sigue en `data/`).

## Pruebas existentes actualizadas
Las de v2.44B, v2.46D, v2.47B y v2.48A fijaban el diseño anterior (selector y panel en la misma pantalla, código dentro de `render_unicorn_semantic_split`); ahora comprueban la nueva página.

## Pendiente
Un informe de UX posterior propone paginación y búsqueda por nombre o ticker en los resultados, aclarar el alcance (141 unicornios de calidad), que el Top 3 respete los filtros y separar fechas de cálculo y de mercado. No incluido aquí.
