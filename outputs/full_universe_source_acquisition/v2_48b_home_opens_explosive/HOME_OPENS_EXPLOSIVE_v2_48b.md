# v2.48B — el botón «Unicornios en bolsa» abre directamente Unicornio explosivo

Estado: `HOME_OPENS_EXPLOSIVE_COMPLETED`. Solo comportamiento de navegación del inicio (`app_v2_37.py`); no cambia datos, criterios ni pantallas.

## Qué cambia
Antes el botón abría Unicornios en «Calidad fundamental» (la opción por defecto del selector). Ahora, al pulsarlo, se fija el selector «Tipo de descubrimiento» en «Unicornio explosivo» antes de navegar, así que se llega directamente a esa vista. El texto bajo el botón pasa a «Empresas cotizadas: candidatos explosivos y calidad fundamental».

## Lo que no cambia
- «Calidad fundamental» sigue a un clic en el mismo selector de esa pantalla, y entrar por la barra lateral mantiene el comportamiento de siempre.
- Cada vez que se entra desde el inicio con el botón se vuelve a abrir en «Unicornio explosivo», aunque en la visita anterior se hubiera cambiado a calidad.
- El modo simple por enlace (`?modo=unicornios`) ya abría en explosivo y no se toca.

## Pruebas
`tests/qa_home_two_buttons_v2_48a.py` ampliada, ejecutando la app de verdad con `AppTest`: tras el clic el selector vale «Unicornio explosivo» y ofrece «Calidad fundamental»; se puede cambiar a calidad sin excepciones; una segunda entrada desde el inicio vuelve a explosivo. Comprobado que falla sobre el código anterior y pasa ahora.
