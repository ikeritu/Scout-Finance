# v2.50K — Fase 7 del roadmap cripto: piloto del eje de calidad (DefiLlama)

Estado: `PASS_FOR_NEXT_CONTROLLED_PILOT` para TVL y comisiones como **información**, con la salvedad de que **la cobertura es pequeña** (≈ 13 % de las candidatas). Fecha: 2026-10-20. Piloto de fuente con sondas reales y lectura de la documentación; **no hay código de la app**. El diseño propuesto espera la aprobación del usuario. Heurística local de investigación: no es una recomendación ni predice rentabilidad.

Por qué: los niveles altos miden actividad inusual, no solidez. En bolsa el «unicornio» combina calidad fundamental y señales explosivas; en cripto el equivalente de la calidad es la **actividad real de un protocolo** (valor depositado, comisiones que paga la gente por usarlo). DefiLlama es la fuente gratuita habitual de esos datos.

## Hechos observados
**Acceso (documentación oficial de DefiLlama):** «Free API — no authentication required»; base `https://api.llama.fi`; endpoints gratuitos `/protocols`, `/protocol/{id}`, `/overview/fees` (comisiones e ingresos), `/overview/dexs`, `/summary/fees/{protocolo}` y precios. **No se listan límites de uso ni condiciones** (atribución, uso comercial): quedan sin documentar. Las sondas funcionaron sin clave ni cabeceras de cuota.

**`/protocols` (una llamada, 9,3 MB, 1,4 s):** 8.769 protocolos, 5.537 con TVL > 0, y **2.432 con `gecko_id`**, el identificador de CoinGecko. Eso da una **identidad exacta** con las monedas de la app (sin la ambigüedad de símbolos que sí hubo con Binance). Trae `tvl`, `change_1d/7d`, `mcap`, `category`, `chains`.

**`/overview/fees` (5,1 MB, 0,8 s):** 3.032 protocolos con `total24h`, `total30d`, `total1y`… (comisiones; con `dataType=dailyRevenue`, ingresos: 2.674 protocolos). **No trae `gecko_id`**, pero su `defillamaId` coincide con el `id` de `/protocols`, que sí lo tiene (mapeo comprobado: 364 protocolos con comisiones a 30 días mapean a una moneda de CoinGecko; 305 con ingresos).

**Cobertura sobre las monedas reales** (universo del 2026-10-19: 1.822 no excluidas, 839 con liquidez suficiente, 155 en la preselección):
| Dato | No excluidas | Con liquidez | Preselección |
|---|---|---|---|
| Protocolo en DefiLlama (con `gecko_id`) | 20,0 % | 27,1 % | 26,5 % (41 de 155) |
| Con TVL > 0 **o** comisiones 30 d > 0 | — | 15,1 % | **12,9 % (20 de 155)** |
| Con comisiones a 30 días | — | 8,5 % | 5,8 % (9 de 155) |
- De las 41 monedas de la preselección que son protocolo, **más de la mitad tienen TVL 0** (categorías como juegos, NFT o cadenas propias): TVL en la mediana 0, percentil 90 de 14,6 M$. Las categorías más frecuentes: juegos 5, cadenas 5, DEX 3, puentes canónicos 3, agregadores de DEX 3.
- Para las que sí tienen TVL, capitalización / TVL: mediana 4,5; percentiles 10 y 90: 0,5 y 130 (muy dispersa).
- Comisiones a 30 días de las 9 monedas de la preselección que las tienen: mediana ≈ 43.000 $, percentil 90 ≈ 3,4 M$.

## Inferencias (razonadas, no confirmadas)
- **El eje de calidad solo puede describir a una de cada ocho candidatas.** La mayoría de las monedas explosivas (memecoins, tokens de comunidad, cadenas pequeñas) no son protocolos con TVL o comisiones medibles. **«Sin datos de DefiLlama» no es una mala señal**: significa que la moneda no es un protocolo DeFi seguido por DefiLlama.
- Por eso no tiene sentido sumar o restar puntos con ese eje: sesgaría la puntuación a favor de los pocos protocolos DeFi y no aportaría nada a los demás. Como información sí aporta (en una ficha de un protocolo, TVL y comisiones son justo lo que se querría ver).
- TVL y comisiones tienen sus propios problemas (doble recuento, incentivos que inflan el TVL, comisiones que no son ingresos del token): son un indicio, no una valoración.
- Coste de red: dos descargas grandes por búsqueda (14 MB). Se pueden guardar en memoria una hora; no hay norma de caché documentada, pero conviene no repetirlas.

## Limitaciones no confirmadas
Límites y condiciones de uso de DefiLlama (no documentados); estabilidad del formato; si los 9,3 MB y 5,1 MB cambian mucho con el tiempo; la cobertura de las monedas fuera de la preselección que se consulten desde el listado; la calidad de `gecko_id` (se supone correcta).

## Diseño propuesto (pendiente de aprobación)
Principio: **información, sin puntos; «sin datos» dicho como lo que es**.

| Pieza | Qué haría | Coste |
|---|---|---|
| **Pestaña «Calidad» en la ficha** | si la moneda es un protocolo: categoría, cadenas, TVL y su cambio a 7 días y 30 días, comisiones e ingresos a 24 h/7 d/30 d/1 año, capitalización/TVL, capitalización/comisiones anualizadas; si no lo es: «No es un protocolo DeFi seguido por DefiLlama (la mayoría de las monedas no lo son): sin datos de calidad, y eso no es una señal negativa» | 2 llamadas públicas por búsqueda (memoria, 1 h) |
| **Etiquetas en las tarjetas** | «Protocolo · TVL 14,6 M$» y «Comisiones 30 d 43 k$» solo cuando existen | ninguno extra |
| **Filtro del listado «Con datos de protocolo»** | para ver de un vistazo el subconjunto donde la calidad es medible | ninguno extra |
| **Puntuación** | **sin cambios** | — |

## Decisiones que necesito del usuario
1. ¿Se implementa como **información** (pestaña, etiquetas y filtro), sin puntos?
2. ¿Aceptas que cubra solo ≈ 13 % de las candidatas, con «sin datos» explicado como neutro?
3. ¿Una vista «Calidad cripto» aparte (lista de protocolos ordenados por TVL o comisiones, como «Calidad fundamental» en bolsa) en lugar de solo la pestaña? Mi recomendación es **no por ahora**: con ~13 % de cobertura sería una lista corta y de otro tipo de monedas; mejor empezar por lo mínimo y mirarlo.
