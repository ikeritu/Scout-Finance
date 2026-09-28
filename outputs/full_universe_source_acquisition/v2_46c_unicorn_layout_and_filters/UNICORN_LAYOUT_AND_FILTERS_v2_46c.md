# v2.46C — Lista + ficha en dos columnas y filtros de crecimiento y sector

Estado: `UNICORN_LAYOUT_AND_FILTERS_COMPLETED`. Solo presentación y filtrado de lo ya calculado (`app_v2_37.py`); sin cambios de datos ni de criterios; sin red.

## Disposición en dos columnas
- Vista «Analítica visual»: lista compacta a la izquierda (contenedor con scroll propio de 760 px, 12 empresas por página, «← Anteriores / Siguientes →») y **ficha a la derecha** (`render_unicorn_ficha`), visible sin desplazarse hasta el final de la lista.
- Desaparecen el aviso emergente y el enlace «Ir a la ficha de …» de v2.46B: ya no hacen falta.
- En móvil las columnas se apilan (ancho de página 375 px, sin desbordamiento).

## Filtros nuevos (bajo País/Estado/Elegibilidad)
- **Crecimiento de ingresos interanual**: deslizador por tramos fijos (0, 10, 20, 30, 50, 100, 200, 500 %, «Sin tope»). Un deslizador lineal era inutilizable: un valor real de la SEC llega a +23.258 % (base de ingresos minúscula). Sin estrechar el rango no se oculta ninguna empresa; al estrecharlo se ocultan también las que no tienen cifra (lo indica la ayuda del control).
- **Sector (SIC de la SEC)**: multiselección con el recuento por sector; las empresas sin SIC aparecen como «Sin sector SEC».

## Medido en vivo
- Crecimiento ≥ 30 %: 23 de 153 unicornios. Combinado con «Pharmaceutical Preparations» (8): 5 empresas, todas con crecimiento ≥ 30 %.
- Selección en la lista cambia la ficha de la derecha; sin excepciones en escritorio ni móvil.

## Pruebas
`tests/qa_unicorn_layout_and_filters_v2_46c.py` (sector, semántica del rango, tramos, cableado de filtros y layout). Aserciones de `qa_unicorns_primary_screen_v2_44b.py` actualizadas al nuevo layout.

## Observación (sin cambios)
Arrowhead Pharmaceuticals figura con +23.258 % de ingresos: cifra real del dato SEC, pero con base minúscula; conviene leerla con cautela.
