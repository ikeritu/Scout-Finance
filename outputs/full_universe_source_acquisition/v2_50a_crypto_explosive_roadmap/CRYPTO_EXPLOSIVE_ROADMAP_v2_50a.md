# v2.50A — Unicornios explosivos en criptomonedas: análisis de opciones y roadmap

Estado: `CRYPTO_ROADMAP_DOCUMENTED` (solo investigación de escritorio y dos sondas de una llamada; **no hay código ni credenciales**). Fecha de las comprobaciones: 2026-10-19.

## Decisiones de la fase 0 (aprobadas por el usuario el 2026-10-19)
1. **Definición:** unicornio cripto = señales explosivas de mercado más filtros de seguridad y de volumen falso. El eje de calidad (TVL, comisiones) queda para la fase 7.
2. **Fuente base:** CoinGecko, plan Demo (gratuito, con clave).
3. **Alcance inicial:** unas 2.000 monedas de exchanges; sin carril DEX por ahora.
4. **Filtros de exclusión:** sin stablecoins ni versiones envueltas, liquidez y edad mínimas, y rotación sospechosa de volumen marcada (no oculta).

**Siguiente paso (fase 1):** la clave Demo la crea el usuario y la guarda en la variable de entorno de usuario `SCOUT_FINANCE_COINGECKO_API_KEY`; nunca en el chat ni en el repositorio. Hasta entonces no se escribe código de proveedor.

Restricciones que ya rigen el proyecto y se respetan aquí: sin fuentes de pago (v2.33D1 y siguientes), fallo cerrado, ningún dato inventado, ningún encuadre de asesoramiento financiero, y las cuentas y claves de API las crea la persona usuaria (nunca se escriben en el chat ni en el repositorio).

## 1. Qué hay que decidir primero: qué es un «unicornio explosivo» en cripto
En bolsa la app mide **señales de mercado explosivas** (capitalización pequeña, volumen relativo, momentum, float, short float, ruptura, catalizador) y las acota con topes cuando faltan datos. En cripto algunas señales tienen equivalente directo y otras no:

| Acciones | Cripto | Comentario |
|---|---|---|
| Capitalización micro/small | Capitalización pequeña | Directo. Umbrales distintos (a calibrar). |
| Precio ≤ 5 $ (penny stock) | — | **No se traslada**: el precio unitario de una moneda no significa nada (depende del suministro). |
| Volumen relativo (hoy / media 3 m) | Rotación (volumen 24 h / capitalización) y volumen 24 h frente a su media de 30 días | Directo. El mercado es 24/7: no hay «día parcial», la ventana es móvil de 24 h. |
| Cambio a 20 días | Cambio a 7 / 14 / 30 días | Directo; CoinGecko los entrega ya calculados. |
| Float bajo | Suministro circulante / total o máximo, y FDV / capitalización | **Invierte el sentido**: poco circulante frente al total es **riesgo de dilución** (desbloqueos), no señal alcista. Es un factor de riesgo, no de puntos. |
| Short float alto | Tasa de financiación negativa y open interest creciente (solo monedas con perpetuos) | Análogo del «short squeeze». Solo existe para las monedas con derivados líquidos (minoría). |
| Ruptura | Ruptura del máximo de 30 días con volumen | Directo si hay velas diarias. |
| Catalizador | Alta en un exchange grande, desbloqueo, evento | Manual o por listados; sin fuente gratuita fiable de calendario. |

Lo que **no** existe en acciones y es imprescindible aquí: **filtros de seguridad y de calidad de volumen**. Gran parte de lo que «explota» en cripto son monedas con volumen falso, liquidez ínfima o contratos fraudulentos. Una puntuación explosiva sin esos filtros marcaría sobre todo lo peor del mercado. Propuesta: la lente explosiva (puntos) y los **filtros de exclusión** (liquidez mínima, edad mínima, sin stablecoins ni versiones envueltas, señales de volumen sospechoso, y para tokens de DEX la comprobación del contrato) son dos capas distintas, como el criterio fundamental y el explosivo lo son en bolsa.

«Unicornio» como en bolsa (calidad + explosividad) pediría un eje de calidad (actividad real del protocolo: TVL, comisiones, usuarios). Eso es una fase posterior (§5).

## 2. Fuentes candidatas: hechos observados
Clasificación: **[oficial]** leído en la documentación o página del proveedor; **[sonda]** observado con una llamada real; **[tercero]** dicho por una fuente no oficial, sin verificar.

### CoinGecko (columna vertebral propuesta)
- Plan Demo (gratuito, con clave): **10.000 llamadas/mes, 100 llamadas/min, 1 clave, histórico diario y por hora de 1 año y de 5 min de 1 día, «atribución requerida»** [oficial, página de precios]. El uso comercial del plan Demo no se indica [oficial: la fila de licencia solo marca «Commercial» para los planes de pago].
- API sin clave: «~10–30 llamadas/min» dinámico, GeckoTerminal «~10 llamadas/min», bolsa compartida por IP, y la propia página dice que **no es adecuada para producción, consultas programadas ni actualizaciones frecuentes** [oficial]. No sirve de base; sí de sonda.
- `/coins/markets` [sonda, sin clave]: una llamada devolvió 250 filas; la página 8 cubría los puestos 1.666–1.908, así que **unas 8 llamadas recorren ~2.000 monedas**. Campos devueltos: `market_cap`, `total_volume`, `circulating_supply`, `total_supply`, `max_supply`, `fully_diluted_valuation`, `price_change_percentage_7d/14d/30d_in_currency`, ATH/ATL, `market_cap_rank`, `last_updated`. La respuesta no trajo cabeceras de límite, así que el consumo restante no se puede leer y habría que contarlo en la app.
- Velas: el endpoint de OHLC de CoinGecko tiene granularidad gruesa según el rango (de memoria: 30 min / 4 h / 4 días) **[sin verificar en esta sesión]**; las series diarias de precio, capitalización y volumen (`market_chart`) sí encajan para el volumen relativo. Para velas diarias reales de las monedas con ticker en Yahoo o en Binance, véanse esas filas.

### Yahoo Finance vía `yfinance` (ya está en la app)
- [sonda] `BTC-USD`, `WIF-USD`, `BONK-USD` y `PEPE24478-USD` devolvieron `marketCap`, `circulatingSupply`, `volume24Hr` y 93 barras diarias de 3 meses. Mismo código de búsqueda y de caché que bolsa.
- Limitación [sonda]: las monedas pequeñas llevan un **sufijo numérico propio de Yahoo** (`PEPE24478-USD`) que no se puede deducir del símbolo, así que **no sirve para descubrir el universo**, solo para cruzar o dibujar velas de monedas ya identificadas por otra fuente. Cobertura de monedas muy pequeñas: desconocida.

### Binance (datos públicos de mercado, sin clave)
- Host solo de datos públicos `data-api.binance.vision`; límites por IP medidos en «peso» por ruta, con la cabecera `X-MBX-USED-WEIGHT` [oficial]. Las cifras concretas de peso por ruta [tercero]: klines 2–20, ticker 24 h 2 (80 para todos), tope 1.200 por minuto.
- Derivados públicos (USDⓈ-M): `openInterest` sin clave, peso 1; `premiumIndex` (tasa de financiación actual), peso 1 con símbolo; **ratio largos/cortos solo de los últimos 30 días**; historial de financiación: los 200 últimos registros por defecto [oficial].
- Condiciones: el servicio «no es adecuado para arbitraje de precios ni trading de alta frecuencia» y puede restringir la conexión sin aviso [oficial/tercero]; los conjuntos históricos de `data.binance.vision` están bajo CC BY-NC-SA 4.0 (no comercial) [tercero: título y resumen de las condiciones]; hay restricciones regionales de acceso según un tercero (sin verificar) [tercero].
- Cobertura: solo monedas cotizadas en Binance (cientos, no miles) y sin capitalización ni suministro. Sirve como **capa de verificación** (liquidez real, velas diarias de calidad, open interest y financiación), no como descubrimiento.

### DexScreener y GeckoTerminal (monedas de DEX)
- DexScreener: perfiles y «boosts» de token a 60/min [oficial]; los endpoints de pares aparecen sin límite en esa página (300/min según un tercero) y la página no menciona clave ni condiciones de uso. Los pares traen `priceChange`, `volume`, `liquidity` (USD), `fdv`, `marketCap`, `pairCreatedAt` y `txns` (compras/ventas) [oficial, esquema de `/metas/meta`].
- GeckoTerminal (vía CoinGecko, sin clave): ~10 llamadas/min, API en beta [oficial].
- Es donde ocurren las explosiones de microcapitalización, y también la mayoría de estafas. Útil, pero **otra carril de mayor riesgo**, no el primero.

### Descartadas con evidencia
- **CoinPaprika (gratis):** 20.000 llamadas/mes, 2.000 activos, **OHLCV de solo 1 día**, uso personal, sin redistribución [oficial]. No sirve para histórico.
- **CoinMarketCap Básico:** gratis, 15.000 créditos/mes y 50/min, pero el histórico diario completo empieza en el plan de pago [oficial CMC Academy, 2026]. Sin histórico no hay momentum ni volumen relativo propios.
- **Pago o sin alternativa gratuita fiable:** CoinGlass, Santiment, LunarCrush, Messari en profundidad, calendarios de desbloqueos (la mayoría de pago). Coherente con la decisión de no usar fuentes de pago.

### Pendientes de verificar en un piloto (no se han comprobado)
Límites reales de DefiLlama (fuentes discrepantes: ~500 por 5 min frente a ~300 por min) y qué endpoints son gratis; límites y respuesta del API gratuito de GoPlus para seguridad de tokens (la documentación solo da límites generales); condiciones de uso de DexScreener; si el plan Demo de CoinGecko admite uso en una app que ven varios colegas.

## 3. Opciones de arquitectura (todas las posibilidades) y recomendación
| Opción | Qué es | A favor | En contra | Veredicto |
|---|---|---|---|---|
| A. Solo CoinGecko Demo | Descubrimiento y datos con una fuente | Una clave, ~2.000 monedas en ~8 llamadas, histórico de 1 año, enlace a ficha | Requiere clave del usuario, 10.000/mes, atribución, volumen agregado con posible lavado | **Base recomendada** |
| B. Directa de exchanges (Binance, Coinbase, Kraken) | Datos públicos de pares | Sin clave, velas reales, liquidez, derivados | Solo monedas listadas, sin capitalización ni suministro | **Capa de verificación** |
| C. Solo DEX | DexScreener + GeckoTerminal | Capta microcapitalización, edad del par, liquidez, compras/ventas | Riesgo de estafa, ~10/min en GeckoTerminal, términos poco claros | **Carril posterior de alto riesgo** |
| D. Reutilizar `yfinance` | Mismo código que bolsa | Cero infraestructura nueva | No descubre monedas pequeñas (sufijo numérico) | **Cruce y velas**, no descubrimiento |
| E. CoinMarketCap / CoinPaprika | Agregadores | — | Sin histórico gratis (ver arriba) | Descartada |
| F. Capa de calidad on-chain | DefiLlama (TVL, comisiones), actividad de repositorios | Da el eje de «unicornio» (calidad) | Cobertura parcial (DeFi), límites sin verificar | **Fase posterior** |
| G. Sentimiento social | APIs de redes y de pago | — | Sin fuente gratuita fiable | Fuera de alcance |
| H. Derivados | Open interest y financiación de Binance | Único análogo del «short squeeze» | Solo monedas con perpetuos; ratio largos/cortos 30 días | **Señal opcional** de la capa de verificación |

Arquitectura recomendada, por capas (igual que bolsa: censo → mercado → puntuación):
1. **Descubrimiento (A):** `/coins/markets`, 8 páginas, universo ≈ 2.000 monedas con capitalización, volumen, suministros y cambios 7/14/30 d.
2. **Filtros de exclusión previos:** stablecoins y versiones envueltas o de staking líquido (categorías de CoinGecko), liquidez/volumen mínimos, edad mínima, rotación absurda (volumen ≫ capitalización) como sospecha de lavado.
3. **Preselección con campos baratos:** puntuación con lo que ya trae `/coins/markets`; quedan ~100 candidatas.
4. **Detalle de las candidatas (A):** `market_chart` diario (volumen relativo propio de 30 días y ruptura): ~100 llamadas.
5. **Verificación (B, D, H):** cruce de volumen y precio con Binance o Yahoo cuando la moneda cotiza allí; open interest y financiación si hay perpetuo. Si la verificación discrepa, se **marca**, no se oculta.
6. **Presentación:** misma interfaz que bolsa (tarjetas, filtros, ficha con pestañas, gráfico, enlaces a CoinGecko y Yahoo donde haya símbolo verificado).

**Presupuesto de llamadas (Demo 10.000/mes):** una búsqueda ≈ 8 + ~100 = ~108 llamadas ⇒ unas **90 búsquedas al mes**; con caché y un contador visible en la app es suficiente. Las ~100 de detalle se pueden recortar a 60 sin perder el sentido.

## 4. Riesgos y cómo se tratan
| Riesgo | Tratamiento |
|---|---|
| Volumen falso o lavado | Filtro de rotación absurda; volumen cruzado con una fuente independiente cuando existe; marcar, no ocultar. |
| Estafas y contratos fraudulentos | Mínimos de liquidez y edad; para tokens de DEX, comprobación del contrato (GoPlus, pendiente de verificar); aviso explícito de riesgo. |
| Stablecoins / envueltas que inflan listas | Exclusión por categoría y por precio fijo ≈ 1 $ con volumen alto. |
| Mercado 24/7 | Ventana móvil de 24 h; sin la advertencia de «día parcial» de EE. UU.; indicar la hora del dato. |
| Dependencia de una fuente con clave | Falla cerrada si no hay clave o se agota el cupo; caché local con fecha; mensaje claro. Ningún dato inventado. |
| Condiciones del plan Demo | Atribución visible; uso personal y local confirmado, uso compartido con colegas **por confirmar**. |
| «Predicción» implícita | Mismo encuadre que bolsa: heurística local de investigación, no recomendación ni predicción. Los umbrales son hipótesis hasta calibrarse. |
| Calibración sin histórico largo | El plan gratuito da 1 año: sirve para tasas base descriptivas (cuántas monedas pasan cada semana), no para afirmar capacidad predictiva. |

## 5. Roadmap por fases
Cada fase termina en uno o varios PRs pequeños, con prueba sin red, documento de cierre y entradas de estado, como hasta ahora. Los tamaños son orientativos.

| Fase | Contenido | Salida / criterio | Decisión tuya |
|---|---|---|---|
| **0. Decisiones (sin código)** | Definir «unicornio cripto» (§1); confirmar CoinGecko Demo como base; confirmar el alcance inicial (≈ 2.000 monedas, sin DEX); aprobar los filtros de exclusión | Este documento aprobado o ajustado | **Sí: las cuatro** |
| **1. Piloto de fuente** (skill de pilotos) | Una persona crea la clave Demo (variable `SCOUT_FINANCE_COINGECKO_API_KEY`); sonda mínima con clave; medir límite real, campos, histórico de 1 año, enlaces; cruce con Yahoo/Binance en una muestra; leer atribución y uso compartido | Estado `PASS_FOR_NEXT_CONTROLLED_PILOT` o `COMPLETED_NO_PROMOTION` con evidencia | **Crear la clave** (no puedo hacerlo yo) |
| **2. Capa de datos** | Proveedor con id canónico de CoinGecko; caché atómica con archivos dañados apartados; contador de llamadas; exclusión de stablecoins/envueltas; fallo cerrado sin clave | Pruebas con respuestas simuladas; ningún dato sin fuente | — |
| **3. Puntuación cripto v1** | Señales de §1, topes por dato ausente, factores de riesgo separados; pruebas de umbral y de monotonía; estudio descriptivo de tasas base con el año de histórico | `crypto_explosive_score` documentado; ninguna afirmación predictiva | Aprobar umbrales iniciales |
| **4. Interfaz** | Activar el botón «Unicornios Crypto»; página de búsqueda, tarjetas, filtros, ficha con pestañas y gráfico (reutilizando lo de bolsa); enlaces a CoinGecko y Yahoo con símbolo verificado; avisos de riesgo reforzados | Mismo recorrido que bolsa, verificado con AppTest y en navegador (escritorio y 375 px) | — |
| **5. Verificación y derivados** | Cruce con Binance/Yahoo; open interest y financiación para monedas con perpetuos; marcar discrepancias | Señal de «squeeze» opcional y visible solo cuando hay dato | — |
| **6. Carril DEX (alto riesgo)** | DexScreener/GeckoTerminal para monedas que CoinGecko aún no lista; comprobación del contrato; pestaña separada con avisos fuertes | Solo si las fases 1–5 funcionan; pilotos de límites y de términos | **Si lo quieres** |
| **7. Eje de calidad («unicornio» de verdad)** | DefiLlama (TVL, comisiones) y otras señales de actividad para quienes tengan dato; cobertura parcial declarada | Lente de calidad opcional, como la fundamental en bolsa | **Si lo quieres** |
| **8. Endurecimiento** | Datos dañados, claves de botón únicas, accesibilidad, rendimiento; matriz de pruebas del informe de QA aplicada a cripto | Cierre del bloque | — |

**Ruta mínima para ver algo funcionando:** fases 0 → 1 → 2 → 3 → 4 (≈ 6–8 PRs). Las fases 5 a 7 mejoran la fiabilidad y la profundidad, no hacen falta para la primera versión. La fase 1 puede tardar poco y es la que desbloquea todo; su único requisito externo es la clave.

## 6. Qué no se hace
- No se paga ninguna fuente ni plan.
- No se crean cuentas ni se piden claves por chat; no se escriben claves en el repositorio.
- No se presenta ninguna puntuación como señal de compra ni como predicción.
- No se completan datos que falten: sin dato, sin puntos y con tope (como en bolsa).

## 7. Límites de este análisis
Las cifras de proveedores se leyeron o sondearon el 2026-10-19 y pueden cambiar; las marcadas [tercero] y las de «pendientes de verificar» no son confirmaciones. No se ha medido cobertura real de monedas pequeñas en Yahoo ni en Binance, ni la tasa de lavado de volumen del universo. Los umbrales de la puntuación cripto son hipótesis de partida, no resultados.
