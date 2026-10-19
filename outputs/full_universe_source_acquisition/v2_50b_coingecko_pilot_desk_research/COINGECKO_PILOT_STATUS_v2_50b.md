# v2.50B — Piloto de CoinGecko (fase 1 del roadmap cripto): lectura oficial y estado

Estado: **`PASS_FOR_NEXT_CONTROLLED_PILOT`** (uso personal y local, ~2.000 monedas, sin promoción a producción). Fecha: 2026-10-19. Lectura oficial de la documentación **y** sonda con clave real (16 llamadas de las 10.000 mensuales). La clave está en la variable de usuario `SCOUT_FINANCE_COINGECKO_API_KEY` y no aparece en ningún archivo, salida ni mensaje. No hay código de la app en este cambio.

## Hechos observados (documentación oficial de CoinGecko leída hoy)
**Límites**
- Plan Demo: **100 llamadas/min**; superarlo devuelve `429`; **todas las peticiones cuentan, incluidos los errores 4xx y 5xx**. La página de límites no indica cabeceras con la cuota restante ni el tope mensual. (La página de precios, leída en v2.50A, da 10.000 llamadas/mes y 1 año de histórico diario y por hora.) Consecuencia: **la app tendrá que contar sus propias llamadas**; no hay cuota restante que leer.

**`/coins/markets`**
- `per_page` hasta **250**; `price_change_percentage` admite `1h, 24h, 7d, 14d, 30d, 200d, 1y`; filtro `category` (valores de la lista de categorías); `ids` hasta 250; devuelve capitalización, rango, FDV, volumen 24 h, suministro circulante/total/máximo, máximos y mínimos históricos y `last_updated`.
- La página no menciona stablecoins: la exclusión se construirá con la **categoría** de stablecoins (la lista de categorías es otro endpoint, aún por sondar), no con un campo propio.

**Velas e histórico**
- `/coins/{id}/ohlc`: `days` ∈ {1, 7, 14, 30, 90, 180, 365, max}; sin `interval`, la vela es de **30 min (1–2 días), 4 h (3–30 días) y 4 días (31 días o más)**. **`interval=daily` es solo de planes de pago.** → Con el plan gratuito **no hay velas diarias** de CoinGecko.
- `/coins/{id}/market_chart`: sin `interval` devuelve 5 min (1 día), **por hora (2–90 días) y diario a las 00:00 UTC (más de 90 días)**; `prices`, `market_caps` y `total_volumes` comparten granularidad. `interval=hourly` llega a los últimos 100 días; `5m` y `1m` son solo Enterprise. El dato del último día UTC completo está disponible a las 00:10 UTC (en el endpoint de OHLC, a las 00:35 UTC).
- La documentación de estos dos endpoints **no declara un límite de histórico para Demo** (cita 2 años para el plan Básico); el de 1 año sale de la página de precios. Hay que medirlo en la sonda.

**Condiciones de uso** (API terms, aplican a todos los planes)
- **Atribución obligatoria:** mostrar de forma destacada «Powered by CoinGecko», legible, no menor de tamaño 10.
- **Almacenamiento:** «No fomentamos el almacenamiento ni la caché de los datos»; si se cachean, **refrescar al menos cada 24 horas y aplicar cifrado fuerte** a los datos almacenados. Prohíben también «duplicar, reproducir, copiar, almacenar, derivar o traducir» los datos.
- **Reparto:** no se permite «vender, alquilar, sublicenciar, redistribuir o sindicar el acceso a la API».
- No se debe superar ni eludir el límite de llamadas, y pueden cambiarlo en cualquier momento.
- Los términos **no distinguen uso personal y comercial** y remiten a la página de precios, donde el plan Demo solo marca «atribución requerida».

## Inferencias (razonadas a partir de lo anterior; no confirmadas por el proveedor)
- **Caché:** una caché local de datos brutos de CoinGecko que dure días chocaría con la regla de refrescar cada 24 h y con el cifrado. Diseño prudente: **sin persistencia de datos brutos más allá de 24 h**, o cifrada; solo se conservan **resultados derivados** (puntuaciones, fechas, contadores) y siempre con la atribución. Si se quiere persistir más, hay que consultarlo con CoinGecko o descartarlo.
- **Compartir con colegas:** una app en red local que enseña a otras personas datos obtenidos con **tu** clave puede contar como «redistribuir el acceso». Diseño prudente: **la lente cripto es de uso personal**; si un colega la usa, con **su propia clave**. Esto condiciona la decisión pendiente de `?modo=unicornios`: el modo simple para colegas puede seguir siendo solo de bolsa.
- **Velas:** para dibujar velas diarias reales haría falta otra fuente (Yahoo o Binance, solo en monedas con símbolo verificado). Para el resto, **gráfico de línea de cierre con barras de volumen** (cierre y volumen salen de `market_chart` por hora/diario) y **sin inventar velas**: las velas construidas agregando puntos por hora no tendrían los máximos y mínimos reales.
- **Presupuesto:** ~108 llamadas por búsqueda completa (v2.50A) sigue siendo viable (~90 al mes con 10.000), pero con un **contador propio**, una **protección** que detenga la búsqueda al acercarse al tope y mensajes claros.

## Limitaciones no confirmadas
No se ha hecho ninguna llamada con clave; no se conocen el tope mensual real aplicado por la cuenta, la profundidad real de histórico del plan Demo, el comportamiento exacto de las cabeceras, ni la lista de categorías de stablecoins. La lectura de los términos no es asesoramiento jurídico.

## Cambios que esto introduce en el roadmap v2.50A
| Punto | Antes | Ahora |
|---|---|---|
| Caché | «Caché atómica con archivos dañados apartados» | Datos brutos de CoinGecko con **vida máxima de 24 h** (o cifrados); resultados derivados sí persisten |
| Gráfico | Reutilizar velas de bolsa | **Línea de cierre + volumen** por defecto; velas solo con fuente verificada (Yahoo/Binance) |
| Uso compartido | Pendiente de confirmar | Lente cripto **personal**; colegas con su propia clave |
| Interfaz | — | Mostrar «Powered by CoinGecko» (≥ 10) en la página cripto |
| Contador | «Contador visible» | Contador propio **obligatorio** (la API no devuelve la cuota) y tope de seguridad |

## Resultado de la sonda con clave (hechos observados el 2026-10-19)
Autenticación: cabecera `x-cg-demo-api-key` contra `https://api.coingecko.com/api/v3` (clave de 27 caracteres, prefijo `CG-`). Se hicieron 16 llamadas en total; ninguna superó el límite.

| Comprobación | Resultado |
|---|---|
| `/ping` con clave | 200 |
| `/key` (consumo de cuota) | **401, código 10005: solo para suscriptores PRO.** Confirma que la cuota restante no se puede consultar: el contador es de la app |
| Cabeceras de cuota en las respuestas | **Ninguna** en ninguna llamada |
| `/coins/markets`, 250 por página, con cambios 24 h/7 d/14 d/30 d | 200, 250 filas, 247 KB, ~0,5 s; los tres cambios a plazo presentes |
| `/coins/categories/list` | 200, 1.050 categorías; existen `stablecoins` (y otras por divisa: `eur-stablecoin`, `algorithmic-stablecoin`…), `wrapped-tokens` y `liquid-staking` |
| `/coins/markets?category=stablecoins` / `wrapped-tokens` / `liquid-staking` | 250 / 250 / 212 monedas en la primera página; las dos primeras vienen llenas, así que **hay más páginas** (cada una cuesta una llamada) |
| `market_chart` de `bonk`, `days=365` | 200, **366 puntos diarios** (2025-10-20 a hoy) con 366 volúmenes; el último punto es de hoy a las 08:19 UTC (hueco de 8,3 h respecto al anterior: es una marca intradía parcial del día en curso) |
| `market_chart` de `bonk`, `days=max` | **401, código 10012: «exceeds the allowed time range»**. Confirma el límite de **1 año** del plan Demo |
| Exclusión de stablecoins en las monedas de rango 20–70 | 11 de 51 caen en las categorías (`BFUSD`, `DAI`, `PYUSD`, `RLUSD`, `U`, `USD1`, `USDD`, `USDE`, `USDF`, `USDG`, `USDGO`): todas son stablecoins |

### Cruce con Yahoo (`SYMBOL-USD`, 51 monedas de rango 20–70)
- **Cobertura de Yahoo: 27 de 51 (53 %)**: casi la mitad de las monedas medianas no tienen ese símbolo en Yahoo.
- **Concordancia donde hay dato:** capitalización dentro de ±25 % en **26 de 27**; la única discrepante es `BFUSD` (cociente 1,39), una stablecoin. **Mediana, p10 y p90 del cociente de capitalización = 1,00:** las cifras son prácticamente idénticas, lo que sugiere que **no son una fuente independiente** para la capitalización (inferencia).
- **Volumen 24 h:** cociente Yahoo/CoinGecko p10 / mediana / p90 = 0,62 / 0,98 / 1,29 (n = 27): coinciden en el orden de magnitud pero difieren hasta ~30 % por definición o ventana, así que sirven de comprobación de cordura, no de dato exacto.
- Consecuencia: **Yahoo es una comprobación parcial** (mitad de las monedas, capitalización no independiente), no la verificación universal que sugería el roadmap.

### Incidencia del entorno
Con el Python del proyecto (`.venv`), `yfinance` falló con `UnicodeEncodeError` por el emoji `💰` de la carpeta en la ruta del certificado; es el problema que `ensure_ascii_ca_bundle` de la app ya resuelve para bolsa. Los scripts de sonda sueltos deben usar el Python del sistema o ese mismo ajuste.

## Estado y evaluación frente a la barra del proyecto
- **Identidad:** CoinGecko es la fuente de descubrimiento y su `id` es el identificador canónico; no hay emparejamiento por nombre que pueda fallar. Con Yahoo, 26/27 concuerdan y la excepción es una stablecoin (excluida de todos modos).
- **Histórico:** 1 año diario con volumen, suficiente para volumen relativo a 30 días, ruptura a 30 días y tasas base descriptivas; no para backtests largos.
- **Licencia:** utilizable con atribución, sin redistribuir el acceso y con datos brutos de vida ≤ 24 h o cifrados (ver arriba). Es compatible con **uso personal y local**.
- **Decisión: `PASS_FOR_NEXT_CONTROLLED_PILOT`**, con estas condiciones de diseño ya fijadas: contador propio de llamadas con tope de seguridad; datos brutos de vida máxima de 24 h; atribución «Powered by CoinGecko» visible; línea de cierre con volumen (sin velas diarias inventadas); lente cripto personal; exclusión de stablecoins, envueltas y liquid staking por categorías (paginando).

## Siguiente (fase 2 del roadmap)
Capa de datos de la app: proveedor CoinGecko con clave leída del entorno (nunca impresa), contador y tope de llamadas, caché de vida máxima de 24 h con archivos dañados apartados, conjunto de exclusión por categorías, y pruebas con respuestas simuladas sin red.
