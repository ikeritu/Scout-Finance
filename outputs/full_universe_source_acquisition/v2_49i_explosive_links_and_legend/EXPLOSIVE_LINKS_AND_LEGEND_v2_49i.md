# v2.49I — enlaces a Yahoo Finance y Google Finance, y leyenda del gráfico bajo el gráfico

Estado: `EXPLOSIVE_LINKS_AND_LEGEND_COMPLETED`. Solo presentación: no cambia score, niveles ni datos.

## Enlaces a Yahoo Finance y Google Finance
- Cada ficha y la cabecera de la página de candidato llevan dos enlaces: «Yahoo Finance ↗» y «Google Finance ↗» (nueva pestaña, `rel="noopener noreferrer"`).
- **Solo con ticker verificado.** Se usa la misma regla que la búsqueda de mercado (`yfinance_symbol`): ticker de EE. UU. real (para las empresas de Cboe Europe, su ticker SEC, nunca el símbolo local). Sin ticker verificado no hay enlace: una dirección inventada podría abrir otra empresa. Las clases con punto se escriben como Yahoo las espera (`BRK-B`) y Google recibe el ticker tal cual.
- **Hecho observado (probado en navegador):** `google.com/finance/quote/PLTR` sin código de bolsa da «Página no encontrada»; `google.com/finance/?q=PLTR` resuelve a `PLTR:NASDAQ` (Palantir); `finance.yahoo.com/quote/PLTR` abre Palantir. Con el enlace de ARRY desde una ficha se abrió Array Technologies en Google Finance.
- **Por qué búsqueda por ticker en Google:** el código de bolsa que la app tiene para 90 de las 141 empresas es «Cboe Europe», que no dice si cotizan en Nasdaq o NYSE (v2.33H: no es una señal fiable de mercado principal). Como el enlace es una búsqueda, la lista lo avisa: «comprueba que el nombre de la empresa que se abre coincide con el de la ficha».
- Los hrefs se escapan y el ticker se codifica; la prueba usa un ticker hostil.
- Color del enlace `#0f5f6b`, con contraste ≥ 4,5:1 sobre blanco y sobre el fondo ámbar.

## Leyenda del gráfico
- **Hecho observado:** con la leyenda dentro de la figura, el margen superior reservado para que no pisara el título dejaba un hueco de unos 60 px en pantalla ancha.
- La clave del gráfico pasa a ser una línea de texto bajo el gráfico («Velas verdes: el cierre sube sobre la apertura · rojas: baja · línea naranja … · barras azules: volumen»), que se parte sola a cualquier ancho. Se omiten las partes de las capas que no se muestran. El título queda arriba con margen mínimo.

## Verificación
`tests/qa_explosive_links_and_legend_v2_49i.py` (5 casos): reglas de enlace con fallo cerrado (Cboe local sin ticker, no-EE. UU., sin ticker), escape y apertura segura, contraste, nueve fichas y cabecera con ambos enlaces, y la clave bajo el gráfico en el panel destacado y en la ficha. Comprobado también en navegador con una búsqueda real sobre una copia de los datos.

## Límite
Google Finance y Yahoo Finance son sitios de terceros: su disponibilidad y su formato de dirección pueden cambiar; el enlace de Google por ticker no garantiza la bolsa que se abre.
