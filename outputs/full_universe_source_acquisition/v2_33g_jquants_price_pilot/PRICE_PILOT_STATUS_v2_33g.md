# Scout Finance v2.33G — piloto real de precios J-Quants (JPX / Japón)

Estado: **PASS_FOR_NEXT_CONTROLLED_PILOT, acotado exclusivamente a renta variable japonesa (JPX) vía el plan gratuito de J-Quants**. Esto **no** es una promoción a producción, **no** es un aprobado del "problema global de precios" de Scout Finance, y **no** autoriza scoring, rankings, recomendaciones de inversión, fundamentales, incorporación masiva de precios, contratación de planes de pago, conexión con brokers ni el inicio de la fase 5.

## Alcance de este piloto

Tras v2.33F (evaluación documental de fuentes oficiales por bolsa), J-Quants —API oficial de Japan Exchange Group (JPX)— se identificó como la candidata más prometedora para los 42 símbolos JPX bloqueados en el piloto v2.33D. El usuario creó una cuenta gratuita explícitamente para este piloto. Este cierre cubre **únicamente Japón (42 activos)**; no toca Cboe Europe (119 bloqueados), ASX, TWSE ni BVC.

## Trabajo realizado

1. **Verificación mínima de la API** (2 llamadas de sondeo): confirmó que el ticker interno (`1301`, `277A`, etc.) coincide directamente con el código oficial JPX, y que la ventana real del plan gratuito es exactamente **2024-06-08 → 2026-06-08**, confirmada literalmente por J-Quants en un mensaje de error al pedir un rango mayor.
2. **Resolución determinista** (`scripts/resolve_jquants_price_pilot_v2_33g.py`): para cada uno de los 42 símbolos, se consultó `/v2/equities/master?code=<ticker>` y se exigió coincidencia **exacta** de `CompanyNameEnglish` contra nuestro `company_name`. **42/42 resueltos, 0 sin resolver, 0 emparejamientos dudosos** — cero equivalencias inferidas.
3. **Descarga real autorizada** (`scripts/download_jquants_price_pilot_v2_33g.py`), fail-closed, reanudable, con escritura atómica y sin registrar nunca la clave ni la URL completa en errores: **42/42 activos descargados, 0 fallos**.
4. **Validación local de los 42 históricos** (`scripts/build_jquants_collection_report_v2_33g.py` + `tests/qa_jquants_price_pilot_collection_v2_33g.py`): 42/42 válidos, 0 errores de esquema, 0 incoherencias OHLC, 0 volúmenes negativos.
5. **QA sin red del pipeline** (`tests/qa_jquants_price_pilot_downloader_v2_33g.py`): bloqueo sin clave, bloqueo sin `--execute`, resolución por coincidencia exacta, rechazo fail-closed ante nombre no coincidente, reintento automático ante error 429 (ver incidente abajo), omisión de archivos existentes sin llamar a la red, continuidad tras HTTP 404 simulado, ausencia de clave/URL en informes, escritura atómica. Todo con mocks, sin red y sin credenciales reales.

## Incidente operativo: límite de tasa más estricto de lo documentado

La documentación pública indica 5 peticiones/minuto para el plan gratuito. En la práctica, un espaciado de 13 segundos entre llamadas (compatible en teoría con ese límite) produjo **errores HTTP 429 reales** de forma repetida. Se corrigió aumentando el espaciado a 15 segundos y añadiendo reintento automático con espera de 65 segundos ante un 429, lo que resolvió el problema sin pérdida de datos en la ejecución final. Esto es un **hecho observado**, no una suposición: quien reutilice esta integración debe esperar el mismo comportamiento y no confiar únicamente en la cifra publicada de "5/min".

Durante la depuración de este incidente, un script auxiliar de fusión de resultados (no parte del pipeline final) truncó por error un CSV intermedio a mitad de escritura. Se detectó de inmediato por el conteo de filas inesperado y se corrigió repitiendo la resolución completa desde cero (que ya se sabía reproducible al 100%) en vez de reconstruir a mano — ningún dato final se vio afectado, pero la lección aplicada fue endurecer la escritura del propio script de resolución con archivo temporal + reemplazo atómico, igual que ya tenían el descargador y el resto del pipeline de precios.

## Cifras confirmadas (reproducidas localmente)

- Activos esperados: 42 · válidos: 42 · errores de esquema: 0.
- Observaciones numéricas válidas: **20.228** (20.294 filas de calendario en total, incluyendo 66 filas de "sin operación" con OHLC nulo en 2 activos poco líquidos).
- Sesiones por activo: mínimo 368, máximo 486, mediana 486.
- Ventana confirmada por el proveedor: 2024-06-08 → 2026-06-08 (2 años exactos, con 12 semanas de retraso respecto a la fecha actual).
- **Cobertura de la mediana de sesiones frente a la ventana confirmada: 99.18%** — muy por encima del 90% exigido en v2.33C.
- 41/42 activos alcanzan el máximo de 486 sesiones; 1 (`P148`, Globe-ing Inc., ticker `277A`) tiene 368, empezando el 2024-11-29 — probablemente una cotización más reciente, no confirmado externamente.
- 2 activos (`P182` HOKURIKU GAS CO., `P154`) registran días sin operación (OHLC nulo): 64 y 2 respectivamente — coherente con acciones de baja liquidez, no un error de datos.

Detalle completo en `jquants_collection_report_v2_33g.json` y `JQUANTS_COLLECTION_REPORT_v2_33g.md`.

## Evaluación frente al contrato de v2.33C (acotado a JPX)

| Criterio v2.33C | Umbral | Resultado real (JPX, plan gratuito) | Cumple |
|---|---|---|---|
| Cobertura histórica de precios | ≥ 90% | 99.18% | **Sí** |
| Emparejamiento correcto de símbolos | ≥ 90% | 42/42 (100%) por coincidencia exacta de nombre | **Sí** |
| Cero emparejamientos falsos | 0 | 0 | **Sí** |
| Cobertura fundamental | ≥ 75% | No evaluada (fuera de alcance de este piloto) | No evaluado |
| Licencia y retención documentadas | Documentado | Uso personal permitido; **prohíbe explícitamente redistribuir datos en bruto y proveer resultados de análisis a terceros de forma repetida** — no confirmado por escrito si el uso interno de Scout Finance encaja sin fricción | Parcial |

## Limitaciones conocidas, no resueltas por este piloto

- **Alcance de mercado:** J-Quants solo cubre Japón. No resuelve Cboe Europe (119 bloqueados), ni mejora ASX/TWSE/BVC.
- **Retraso de 12 semanas:** los datos más recientes del plan gratuito siempre están ~3 meses por detrás. Irrelevante para este piloto histórico, pero relevante si en el futuro se plantea uso "en vivo".
- **Restricción de licencia sobre redistribución/resultados repetidos a terceros:** no se ha confirmado por escrito con JPX que el uso privado de Scout Finance (herramienta de investigación personal, no comercial) encaje sin ambigüedad. Antes de cualquier uso más allá de este piloto, se recomienda una confirmación explícita.
- **Origen de la profundidad menor en P148:** no confirmado si es una cotización reciente u otra causa.

## Decisión del gate

**`PASS_FOR_NEXT_CONTROLLED_PILOT`**, con alcance exclusivo a JPX/Japón vía J-Quants (plan gratuito).

- Los 42 activos japoneses superan los umbrales de cobertura histórica y calidad de emparejamiento de v2.33C con margen amplio (99.18% y 100% respectivamente, cero falsos).
- Esto **no** es una promoción a producción ni resuelve el problema global de precios de Scout Finance: Cboe Europe, ASX, TWSE y BVC siguen sin una fuente que los cubra adecuadamente (ver v2.33E, v2.33F).
- No se autoriza scoring, ranking, recomendaciones, fundamentales, incorporación masiva de precios, contratación de ningún plan de pago, conexión con brokers ni el inicio de la fase 5.
- Antes de cualquier paso más allá de este piloto (por ejemplo, ampliar a más activos JPX o usarlo de forma continuada), se recomienda confirmar por escrito con JPX el alcance exacto de la restricción de redistribución/resultados repetidos frente al uso interno de Scout Finance.

## Seguridad y alcance

- La clave de J-Quants (`SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN`) nunca se ha impreso, registrado ni versionado.
- Los 42 JSON brutos permanecen fuera de Git (`outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_prices_collection_v2_33g/`, ignorado).
- Este documento y los informes agregados no reproducen precios fila a fila ni contenido licenciado.
- `production_scoring_authorized: false`, `allow_ranking: false` en todos los informes generados.

## Estado del roadmap

- Interfaz estable: `v2.32F` (sin cambios).
- Pipeline de datos: se añade `v2.33G` (JPX/Japón vía J-Quants) junto a `v2.33D1` (EODHD, `COMPLETED_NO_PROMOTION`), `v2.33E` (Twelve Data, descartado) y `v2.33F` (evaluación de fuentes oficiales).
- Progreso global: **3/8 fases cerradas, fase 4 en curso**. La fase 4 sigue abierta: Cboe Europe (119), ASX y TWSE (profundidad) y BVC (1) siguen sin una fuente gratuita que los resuelva completamente.
- Siguiente paso recomendado (no ejecutado, no autorizado por este cierre): decidir si se confirma por escrito con JPX el alcance de licencia antes de dar cualquier uso adicional a J-Quants, y/o continuar explorando el resto de mercados bloqueados (Cboe Europe requiere mapeo de identificadores previo, según v2.33F).
