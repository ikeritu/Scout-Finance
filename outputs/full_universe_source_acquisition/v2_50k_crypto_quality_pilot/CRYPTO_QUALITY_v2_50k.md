# v2.50K — Fase 7: eje de calidad cripto con DefiLlama (información, sin puntos)

Estado: `CRYPTO_QUALITY_AXIS_COMPLETED`. Decisiones aprobadas el 2026-10-20 ("si a todo"): (1) solo información, sin puntos; (2) cobertura pequeña aceptada (≈ 13 %), con «sin datos» dicho como neutro; (3) sin vista separada «Calidad cripto» por ahora. Uso personal; heurística local de investigación: no es una recomendación financiera ni predice rentabilidad. Diseño y sondas en `CRYPTO_QUALITY_PILOT_v2_50k.md`.

## Qué hay
- **Módulo `src/crypto_v2_50/quality.py`** (puro, sin clave, sin Streamlit, sin disco, transporte inyectable): descarga `/protocols` (identidad exacta por `gecko_id` de CoinGecko) y `/overview/fees` con `dataType=dailyFees` y `dailyRevenue` (se cruzan por `defillamaId` = `id` del protocolo). El índice resultante, por id de CoinGecko, se guarda **solo en memoria durante 1 hora**; una búsqueda cuesta tres descargas (≈ 18 MB) y las siguientes en esa hora, ninguna.
- **Búsqueda** (`search.py`): cada moneda lleva su registro `quality` (o `None`); el resumen añade `quality_status` (`ok` / `unavailable`), `with_quality` (TVL > 0 o comisiones 30 d > 0) y `protocol_matches`. **Si DefiLlama falla, la búsqueda no se detiene**: solo dice que no hay datos de protocolo.
- **Listado**: nuevo filtro «Protocolo DeFi» («Todas» / «Con datos de protocolo»), que se conserva al volver de una ficha y se restablece al ir a Inicio. Las tarjetas muestran, cuando hay datos, las etiquetas informativas «Protocolo · TVL …» y «Comisiones 30 d …». El resumen explica: «Para las demás no hay datos, y eso no es una señal negativa».
- **Ficha**: pestaña **«Calidad»** (la sexta) con TVL y su variación a 1 d / 7 d / 1 mes, comisiones 24 h / 30 d / 1 año, ingresos del protocolo 30 d / 1 año, y los cocientes capitalización / TVL, / comisiones y / ingresos del último año (N/D si falta el dato o es cero), con el enlace a DefiLlama. Tres estados sin tabla, cada uno con su texto: servicio no disponible, moneda que no es protocolo («sin datos de calidad, y eso no es una señal negativa ni positiva») y protocolo seguido sin TVL ni comisiones.
- **Sin efecto en la puntuación**: ni puntos, ni topes, ni cambio de nivel (lo prueba un test que compara la puntuación con y sin datos de calidad).
- **Sin disco**: nada de DefiLlama se escribe a disco.

## Hechos observados
**En la app real**, con la clave del usuario (búsqueda de 2.000 monedas, 74 llamadas a CoinGecko con la caché de 24 h caliente): «230 monedas tienen datos de protocolo», ≈ 12,6 % de las 1.822 monedas conservadas, en línea con el 13 % del piloto. El filtro «Con datos de protocolo» redujo el listado de 843 a 124 monedas; las tarjetas muestran las etiquetas (p. ej. Gains: «Protocolo · TVL 8,2 M$», «Comisiones 30 d 637 k$»; Collector Crypt: solo comisiones) y la pestaña «Calidad» de Gains muestra TVL 8,2 M$, comisiones 24 h 22 k$, 30 d 637 k$, 1 año 8,0 M$, con el enlace a DefiLlama. Un cambio de TVL a 1 mes que DefiLlama no informa aparece como N/D. Sin errores de consola.

**Pruebas** (`tests/qa_crypto_quality_v2_50k.py`, 11 casos, sin red: DefiLlama simulado y **siempre parcheado** —el código tolera errores de red—, clave de mentira): análisis de protocolos y de comisiones (entradas basura, sin `gecko_id`, ids que no casan), construcción del índice, caché de una hora con reloj inyectado, errores de transporte (HTTP 500/429, JSON inválido) sin filtrar URL ni cuerpo, `has_protocol_data`, cocientes, filtro, resumen, tarjetas, pestaña en sus tres estados, fallo de DefiLlama sin romper la búsqueda y puntuación idéntica con y sin calidad. Se comprobó por mutación que las pruebas fallan si se rompe el cruce por `defillamaId`, el filtro o la caché. Las pruebas de 50f, 50g, 50i y 50j se actualizaron (fixtures de DefiLlama y seis pestañas) y siguen verdes.

## Límites
- DefiLlama es un servicio de terceros **sin límites ni condiciones documentados** para el uso gratuito; por eso solo se descarga una vez por hora y nada se guarda en disco.
- Cobertura pequeña: la mayoría de las monedas explosivas **no son protocolos DeFi**, así que para ellas el eje no dice nada (ni bueno ni malo).
- El TVL puede incluir doble recuento e incentivos que lo inflan, y las comisiones que paga la gente no son ingresos del token. Los cocientes son orientativos.
- Los niveles altos siguen midiendo actividad inusual, no solidez: este eje no la corrige.
- Pendiente opcional: fase 6 (carril DEX), comprobación a 375 px de la ficha, y una vista separada «Calidad cripto» si la cobertura creciera.
