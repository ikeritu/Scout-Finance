# v2.46B — Mejoras rápidas de UI/UX en Unicornios

Estado: `UNICORN_UI_QUICK_WINS_COMPLETED`. Solo presentación (`app_v2_37.py`); no cambia datos, criterios ni cálculos. Sin red.

## Qué se cambió y por qué

| Problema (auditoría UI/UX) | Cambio |
|---|---|
| Tarjetas con el mismo «96 %» en casi todas; el dato útil (crecimiento) en letra pequeña | El número protagonista es el **crecimiento de ingresos interanual** real (p. ej. +69,2 %), con beneficio y margen neto debajo; la confianza queda como etiqueta. Altura de tarjeta homogénea. |
| Símbolos locales de Cboe (`0SE0d`, `1PLTRm`) y `CBOE_EUROPE` en pantalla | `unicorn_ticker()` muestra el ticker estadounidense real (`SEZL`, `PLTR`, `MU`); `friendly_exchange()` muestra «Cboe Europe», «Xetra», «Nasdaq». El símbolo local sigue visible en la ficha. |
| Banner «Motor local analizando…», ticker en vivo, nodos, indicador, flujo y barras de señal (movimiento sin actividad real) | Eliminados. Nada se calcula en segundo plano, así que nada lo simula. |
| «Radar local» (suma de 5 constantes) y «Timeline de señal» (línea sobre categorías) | Eliminados; sustituidos por **cifras reales frente a la mediana de la lista** (`render_unicorn_key_figures`). |
| Bloque de código recortado con la fórmula | Lista con texto que se ajusta al ancho. |
| Pantalla inicial con 8 contadores casi siempre a 0, KPIs duplicados y textos largos | 4 KPIs con ayuda, explicación en el desplegable «Cómo leer esta pantalla», una línea de recuento de evidencia y revisión, tablas Top países/bolsas y selector de watchlist en desplegables. |
| «Ver ficha» abría la ficha fuera de pantalla sin aviso | Aviso emergente al pulsar y enlace «Ir a la ficha de …». |
| Cuatro nombres para lo mismo (Posibilidad / Confianza local / Evidencia / Calidad de evidencia); acentos y jerga interna | Un solo nombre: **Confianza de clasificación**; «Requiere revisión», «Próximo recálculo»; sin «dropdown borroso» ni «Cambio v2.44Z». |
| Vista explosiva: «Radar de mercado activo», «Top 3 candidatos calientes» con scores 33/32/31 mientras el cockpit dice «0 evaluables» | «Datos de mercado cargados», «Top 3 por score explosivo (sobre 100)», scores mostrados como `/100`, etiquetas de tier en español («En vigilancia»), sin animaciones infinitas. |
| Selector «Choose options» en inglés | «Elige 2 o 3 empresas». |

## Medido en vivo (Streamlit, escritorio 1400 px)

- Altura de la vista por defecto: 8.243 px → 5.568 px; primera tarjeta a 1.698 px (antes ~2.300).
- Vista explosiva: sin excepciones, 3.913 px.
- Móvil 375 px: sin desbordamiento horizontal de la página (`scrollWidth` = 375); las tablas anchas se desplazan dentro de su contenedor.

## Pruebas

- Nuevo `tests/qa_unicorn_ui_quick_wins_v2_46b.py` (ticker, bolsa, cifra protagonista, medianas, etiquetas de tier, elementos falsos eliminados, vocabulario).
- `tests/qa_unicorns_primary_screen_v2_44b.py`: las aserciones que fijaban el diseño decorativo se reescribieron para exigir el nuevo diseño.
- `pytest`: mismas 3 fallas previas de `test_expanded_universe_post_closure_v2_14j.py`, ninguna nueva.

## Pendiente (no incluido en «rápido»)

Disposición en dos columnas (lista + ficha), pestañas de modo, filtros por rango de crecimiento y sector, y unificar el lenguaje visual de la vista explosiva (hero oscuro «trading desk» frente al resto).
