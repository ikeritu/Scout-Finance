# v2.46D — Entidades financieras fuera de la lista de Unicornios por defecto

Estado: `UNICORN_FINANCIALS_DEFAULT_COMPLETED`. Solo presentación (`app_v2_37.py`); no cambia datos, el flag v2.38BT ni ningún fichero de salida; sin red.

## Decisión
El criterio unicornio exige «caja libre positiva», que en bancos y aseguradoras no significa lo mismo que en una empresa industrial. 12 de los 153 unicornios son financieros (SIC 6000–6499 de la SEC o tier `REVIEW_REQUIRED_FINANCIAL_INSTITUTION`). Antes se marcaban «Requiere revisión» pero ocupaban sitio en la lista.

## Cambio
- Lista por defecto: **141 unicornios** (indicador superior, medianas, filtros y vistas usan esa población).
- Casilla «Incluir entidades financieras (12)» para verlas (153 en total) y filtro rápido «Revisión requerida», que siempre muestra las 12 aunque la casilla esté apagada.
- Aviso bajo los indicadores cuando hay financieras ocultas; los recuentos «X de N» usan la población base activa.
- La búsqueda también encuentra el ticker estadounidense real (`us_ticker`), p. ej. «PLTR» para filas solo-Cboe.

## Verificado en vivo
141 por defecto (Evidencia: 89 muy respaldado, 52 respaldado); «Revisión requerida»: 12; casilla marcada: 153; sin excepciones.

## Pruebas
`tests/qa_unicorn_financial_default_v2_46d.py`; resto de QA de unicornios sin cambios y en verde.

## Sin cambios (decisión pendiente)
El ranking global v2.38BV sigue contando dos veces las empresas con doble cotización.
