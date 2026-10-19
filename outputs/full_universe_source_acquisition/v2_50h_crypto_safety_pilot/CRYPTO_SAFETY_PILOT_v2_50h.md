# v2.50H — Fase 5 del roadmap cripto: piloto de las comprobaciones de seguridad

Estado: `PARTIAL_PASS_NO_PRODUCTION_PROMOTION` para la seguridad de contratos (GoPlus: cobertura parcial) y `PASS_FOR_NEXT_CONTROLLED_PILOT` para los derivados (Binance público) y para la antigüedad medida con la serie diaria. Fecha: 2026-10-19. Es un piloto de fuentes con sondas reales: **no hay código de la app**; el diseño propuesto espera la aprobación del usuario. Todo es heurística local de investigación: no es una recomendación ni predice rentabilidad.

Por qué: hoy el nivel alto mide **actividad inusual**, no solidez (v2.50F: las candidatas más altas son microcapitalizaciones de 6 a 50 M$ con rotación y momentum muy altos). Esta fase busca datos gratuitos para que la ficha diga qué se sabe y qué no del contrato, la antigüedad y los derivados.

## Hechos observados
**Muestra:** de las 155 monedas que hoy todavía podrían llegar al nivel bajo (v2.50E), las **60 más prometedoras**; 60 llamadas de CoinGecko (`/coins/{id}` sin los bloques pesados) y 48 de GoPlus, más una de Binance. Los porcentajes son sobre esa muestra, no sobre el universo.

**CoinGecko `/coins/{id}` (60 de 60 respondieron):**
- **59 de 60 tienen un contrato en alguna cadena** (casi todas son tokens, no monedas nativas): BNB Chain 24, Ethereum 17, Solana 12, Base 8, y otras (Robinhood, Energi, NEAR, Arbitrum, Polygon, Osmosis…). Una sola moneda nativa.
- **`genesis_date` solo viene en 2 de 60**: sirve de poco como antigüedad. La antigüedad hay que medirla de otra manera (ver diseño).
- 48 de 60 tienen contrato en una cadena que GoPlus cubre (lista EVM habitual o Solana).

**GoPlus (token security), sin clave:**
- Responde **sin clave** (HTTP 200, `code: 1`) y no mostró cabeceras de cuota ni un 429 en 48 llamadas a 0,7 s de separación. Admite 46 cadenas. Fuera de la documentación oficial, un sitio de terceros da el plan gratuito con clave en 150.000 CU/mes, 30.000/día y 150/min sin llamadas por lotes [tercero, sin verificar]; el acceso sin clave y sus límites **no están documentados**. No se encontraron condiciones de uso.
- **Cobertura parcial:** de 48 consultas, **19 devolvieron datos y 29 vinieron vacías** (el 40 %; el 32 % de las 60 monedas). Se consultó la primera cadena de la lista de cada moneda; probar todas sus cadenas podría mejorar la cobertura a costa de más llamadas (no medido).
- **Campos presentes** (sobre 19 respuestas): número de tenedores 18, lista de mayores tenedores 17, `is_open_source` 13, `is_proxy` 13, porcentaje del creador 13, `is_in_dex` 13, tasas de compra y venta 11, `is_honeypot` 10, `is_mintable` 9, propietario 8. La documentación avisa de que muchos campos se **omiten cuando el resultado es desconocido** («no devolver significa desconocido») y de que, con contrato no abierto o proxy, no se evalúan casi todos los riesgos.
- **Señales levantadas** (sobre las 19): acuñable (`is_mintable`) 5, proxy 4, transferencias pausables 1; **ningún honeypot** ni propietario oculto entre los que lo informaron. Tenedores: mediana de 18.190, un 10 % por debajo de 36, y 1 con 10 o menos. **El 10 % mayor de tenedores concentra una mediana del 66 %; en 3 de 17 supera el 90 %** (esas cifras incluyen contratos de liquidez, exchanges y cuentas bloqueadas: hay que leerlas con las etiquetas que da GoPlus).
- **Anomalía de calidad de datos:** para el contrato de USDT GoPlus devolvió `holder_count = 1` (evidentemente erróneo). Sus campos son un indicio, no una verdad.

**Binance, derivados públicos (sin clave):**
- `premiumIndex` sin símbolo devuelve **todas** las perpetuas en una llamada (HTTP 200): 881 contratos USDT, con precio de marca y tasa de financiación actual (mediana en valor absoluto 0,005 %; máximo 0,289 %).
- De las 155 monedas de la preselección, **84 coinciden por símbolo con una perpetua y 74 (48 %) con el precio de marca a menos del 10 % del de CoinGecko**: 10 coincidencias por símbolo eran **monedas distintas con el mismo símbolo** (6 % de la preselección). Sin la comprobación por precio se habrían enlazado datos de derivados de otra moneda.
- De los hechos oficiales ya leídos en v2.50A: el open interest es público (peso 1 por símbolo), el historial del ratio largos/cortos solo guarda 30 días, y la financiación guarda 200 registros por defecto.

## Inferencias (razonadas, no confirmadas)
- Con cobertura del 32 % y datos que a veces faltan o fallan, **la ausencia de un dato de GoPlus no debe leerse como «seguro»**: la ficha tiene que decir «no verificado».
- Las señales graves de contrato (honeypot, imposible vender, propietario oculto, propietario que puede recuperar la propiedad o cambiar saldos, enfriamiento de operaciones) justifican un aviso fuerte cuando aparecen, porque son específicas. «Acuñable» y «proxy» son frecuentes entre tokens legítimos: informativas, no sancionadoras.
- La antigüedad medida con la serie diaria de CoinGecko (primer día con datos, hasta 365 días) es mucho más fiable que `genesis_date`: pedir `days=365` cuesta la misma llamada que `days=120`; solo cambia el tamaño de la respuesta.
- Los derivados cubren casi la mitad de la preselección con identidad verificada: es la señal con mejor cobertura y la única con equivalente directo del «short squeeze».

## Limitaciones no confirmadas
Límites y condiciones del acceso a GoPlus sin clave; si probar todas las cadenas de cada moneda mejora la cobertura; la cobertura sobre las otras 95 monedas de la preselección y sobre el resto del universo; la estabilidad de las respuestas de GoPlus en el tiempo; el comportamiento de Binance desde otras regiones (hay restricciones regionales documentadas por terceros). La muestra son las 60 más prometedoras, no una muestra aleatoria.

## Diseño propuesto (pendiente de aprobación)
Principio: **informar, no inventar; lo no verificado se dice como no verificado**.

| Pieza | Qué haría | Coste por moneda | Efecto en la puntuación |
|---|---|---|---|
| **Antigüedad** | pedir la serie de 365 días (misma llamada) y mostrar «N días de historial en CoinGecko» | 0 extra | Etiqueta «moneda reciente» si < 90 días; **tope 44 si < 30 días** |
| **Derivados** | una llamada a `premiumIndex` (todas las perpetuas) para marcar en cada tarjeta «con perpetuo» y la financiación; en la ficha, open interest y ratio largos/cortos (30 d); identidad verificada por precio (±10 %) | 1 llamada total + 1–2 por ficha | **Ninguno en v1** (información); etiqueta «financiación negativa con subida» como indicio de squeeze |
| **Contrato (GoPlus)** | pestaña «Seguridad» en la ficha, **bajo demanda** (botón «Comprobar contrato»): dirección de CoinGecko → GoPlus; muestra señales graves, información (acuñable, proxy, tenedores, concentración con etiquetas) y «no verificado» si no hay datos | 1 de CoinGecko + 1 de GoPlus por moneda abierta | Señal grave de contrato → **tope 44 y aviso**; sin datos, ningún efecto |

Orden de implementación sugerido en dos PRs: **5a** (antigüedad + derivados, que tienen cobertura fiable) y **5b** (GoPlus bajo demanda, con cobertura parcial declarada).

## Decisiones que necesito del usuario
1. ¿Se implementan los tres bloques en ese orden (5a y 5b)?
2. ¿Antigüedad como tope: etiqueta < 90 días y tope 44 < 30 días?
3. ¿Derivados solo informativos en v1 (sin puntos)?
4. ¿Señal grave de contrato como tope 44 y aviso, y «no verificado» sin efecto?
5. ¿GoPlus bajo demanda (botón) y no automático en el listado, para no depender de un servicio de límites no documentados?
