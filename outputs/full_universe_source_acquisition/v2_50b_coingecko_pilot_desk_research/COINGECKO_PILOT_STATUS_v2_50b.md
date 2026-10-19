# v2.50B — Piloto de CoinGecko (fase 1 del roadmap cripto): lectura oficial y estado

Estado: `PILOT_DESK_RESEARCH_COMPLETED_LIVE_PROBE_BLOCKED_ON_API_KEY`. Fecha: 2026-10-19. La parte de escritorio está cerrada; la sonda con clave no se ha podido hacer porque la variable `SCOUT_FINANCE_COINGECKO_API_KEY` **no existe** en el usuario (comprobado sin imprimir nada). No hay código ni credenciales en este cambio.

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

## Qué falta para cerrar la fase 1
1. **Tú:** crear la clave Demo en coingecko.com/en/api (plan Demo) y guardarla en la variable de entorno de usuario `SCOUT_FINANCE_COINGECKO_API_KEY`. No pegarla en el chat.
2. **Sonda mínima con clave** (una vez puesta): `/ping` o `/coins/markets` de una página; comprobar cabeceras y que la clave funciona sin imprimirla; medir `days=365` frente a `days=max` en una moneda; lista de categorías y las de stablecoins; cruce de capitalización y volumen con Yahoo en una muestra pequeña.
3. **Cierre:** estado final del piloto (`PASS_FOR_NEXT_CONTROLLED_PILOT`, `PARTIAL_PASS_NO_PRODUCTION_PROMOTION` o `COMPLETED_NO_PROMOTION`) con la evidencia.
