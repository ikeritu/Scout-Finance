# v2.48A — inicio con dos botones grandes

Estado: `HOME_TWO_BUTTONS_COMPLETED`. Solo presentación (`app_v2_37.py`); no cambia datos, criterios ni el resto de pantallas.

## Qué se pidió
En el inicio, dos botones grandes para hacer clic únicamente: «Unicornios en bolsa» y «Unicornios Crypto» (aún no implementado).

## Qué hace ahora el inicio
- Título «Scout Finance», una línea («Elige qué quieres explorar») y dos botones grandes lado a lado (apilados en móvil):
  - **🦄 Unicornios en bolsa** (relleno teal, el color de la app): abre la pantalla Unicornios.
  - **🪙 Unicornios Crypto**: visible pero desactivado (borde discontinuo y gris), con «Próximamente: todavía no está implementado».
- Una línea pequeña con el aviso de que es una herramienta experimental y no asesoramiento financiero (el mismo texto que ya usaba el inicio): se conserva por la regla del proyecto de no presentar nada como recomendación.
- El aviso de «Modo demo seguro», si está activo, se sigue mostrando.

## Qué se quitó del inicio, y dónde sigue
El inicio ya no muestra la fila de indicadores de los 50 activos (activos, ranking principal, comparabilidad parcial, revisión requerida), el estado de los datos ni los textos «Qué puedes hacer» / «Qué no hace Scout Finance». El estado de los datos sigue visible en la barra lateral («Datos: …», «Fase 7: …»), y los textos de uso responsable están en «Guía final y uso responsable» y «Metodología y ayuda». El antiguo inicio se conserva como `render_home_status`, que sigue usándose cuando la app queda bloqueada por falta de datos (para explicar el motivo).

## Verificado
- En vivo: el botón de bolsa abre Unicornios sin excepciones (ficha y gráficos); el de Crypto está desactivado y no hace nada; en móvil (375 px) los botones miden 349×150 px, sin desbordar la página.
- `tests/qa_home_two_buttons_v2_48a.py` ejecuta la app de verdad con `AppTest`: el inicio ofrece exactamente los dos botones y ninguna métrica, Crypto está desactivado y dice «Próximamente», el botón de bolsa lleva a Unicornios, y la ruta de datos bloqueados sigue usando la vista de estado.

## Incluye
Esta rama lleva también el commit de v2.47C (dos fallos que hacían caer Unicornios en «Calidad fundamental»), porque el botón de bolsa lleva justo a esa pantalla; se publica además en su propio PR, así que el contenido idéntico no genera conflicto al mergear.
