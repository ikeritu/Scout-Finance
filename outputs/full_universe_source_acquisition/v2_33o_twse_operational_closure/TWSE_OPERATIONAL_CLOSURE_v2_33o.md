# Scout Finance v2.33O — cierre operativo de TWSE (Bloque D)

Fecha: 2026-08-31. Alcance: decisión de sustitución de fuente + investigación de splits/dividendos + bloqueo formal de ampliación. Sin descargas nuevas de precios, sin cuenta, sin gasto.

Universo afectado: TWSE, 696 candidatos elegibles (3,29 % del universo, v2.33L). Piloto ya validado: 8/8 activos (v2.33I).

## D1 — Sustitución de EODHD: decidida, afirmativa, con una salvedad honesta

| Criterio | EODHD (v2.33D1) | TWSE oficial (v2.33I) | Gana |
|---|---|---|---|
| Profundidad | mediana 250 sesiones (~1 año) | mediana 4.076 sesiones (~16 años) | **TWSE**, por 16× |
| Completitud | 8/8 activos, 0 fallos | 8/8 activos, 0 fallos | Empate |
| Fiabilidad observada | sin incidentes en la ejecución | 1 error transitorio de ~1.600 llamadas (99,94 % éxito), resuelto con reintento | Empate, ambas limpias en la práctica |
| Latencia/retraso | limitado por el plan (~1 año hacia atrás desde hoy) | ninguno declarado, datos hasta el día anterior | **TWSE** |
| Licencia | términos de plan gratuito de EODHD, con matices no completamente confirmados | Open Government Data License v1.0, abierta y documentada | **TWSE** |
| Estabilidad del endpoint | oficial de proveedor comercial | oficial del gobierno/bolsa de Taiwán | Empate, ambas oficiales |
| Precio ajustado | **sí**, `Adjusted_close` presente en la respuesta | **no**, sin factor de ajuste | **EODHD** |
| Acciones corporativas | incluidas de forma implícita en el ajuste | no incluidas | **EODHD** |

**Decisión:** sustituir EODHD por TWSE oficial como fuente de precios para estos 8 activos. La profundidad histórica (16× mayor) y la licencia abierta pesan más que la pérdida del ajuste automático, especialmente porque EODHD ya fue descartado en `COMPLETED_NO_PROMOTION` (v2.33D1) precisamente por profundidad insuficiente — mantenerlo solo para estos 8 activos no sería coherente con esa decisión ya publicada.

**Salvedad que se documenta sin ocultar:** esta sustitución **pierde el ajuste por splits/dividendos** que sí tenía EODHD. Ver D2.

## D2 — Splits y dividendos: fuente oficial identificada, algoritmo no construido en este cierre

Se ha localizado y confirmado en vivo un endpoint oficial adicional de TWSE, `TWT49U` ("除權除息計算結果表" / tabla de resultados de cálculo ex-derecho/ex-dividendo), con exactamente los campos necesarios para un ajuste real: fecha, código, nombre, **precio de cierre antes del ex-derecho/ex-dividendo**, **precio de referencia tras el ajuste**, valor del derecho + valor del dividendo.

```
GET https://www.twse.com.tw/exchangeReport/TWT49U?response=json&date=YYYYMMDD&stockNo=XXXX
```

Confirmado con una llamada real: devuelve datos reales con esa estructura para la fecha probada. Es del mismo dominio oficial (`www.twse.com.tw`) que el endpoint `STOCK_DAY` ya validado en v2.33I.

**No se ha construido el algoritmo de ajuste en este cierre.** Definir el algoritmo, crear fixtures, validarlo contra ejemplos externos autorizados y documentar su precisión es un trabajo de ingeniería cuantitativa que merece su propia pasada dedicada, no una extensión apresurada de este bloque. Por tanto, siguiendo exactamente la instrucción del encargo para el caso "si no es posible [todavía]":

- **Las series TWSE se mantienen sin ajustar (`unadjusted`).**
- Cada registro del adaptador TWSE (`scripts/price_adapters/twse_adapter.py`, v2.33Q) ya marca explícitamente `is_adjusted=False`, `adjustment_source="not_available"` — no se simula ningún factor.
- Ningún indicador sensible a acciones corporativas (retornos de largo plazo que crucen un split o un dividendo grande) debe calcularse sobre estas series como si estuvieran ajustadas.

## D3 — Ampliación: bloqueada, requiere autorización explícita

El universo TWSE elegible completo es de **696 candidatos**, por encima del umbral de 500 que exige autorización explícita.

Estimación previa a cualquier ejecución: al ritmo usado en v2.33I (~0,8 s entre llamadas, ~200 meses por activo desde 2010-01-04), 696 activos × 200 meses × 0,8 s ≈ **31 horas** de ejecución acumulada. Como en JPX, esto no cabe en una sola sesión de trabajo y debería ejecutarse en segundo plano a lo largo de varios días con reanudación.

**No se ha lanzado ninguna descarga masiva.** Queda pendiente de autorización explícita del usuario.

## D4 — Decisión TWSE

**Operativo sin ajustar, con restricciones — no ampliado.**

- Sustituye a EODHD para los 8 activos ya validados (D1).
- Series `unadjusted`, marcadas explícitamente (D2); fuente oficial para el ajuste identificada pero algoritmo no implementado todavía.
- Alcance sigue acotado a 8/696 candidatos (D3), pendiente de autorización para ampliar.

No se autoriza ninguna descarga masiva, scoring, ranking, ni el inicio de la fase 5.

## Seguridad y alcance

- No se ha descargado ningún precio nuevo (solo una llamada de sondeo a `TWT49U`, sin credenciales, fuente pública).
- No se ha creado ninguna cuenta, no se ha gastado dinero.
- `production_scoring_authorized: false`, `allow_ranking: false`.

## Estado del roadmap

- No cambia el estado de v2.33I.
- Bloque D: sustitución decidida (D1), fuente de ajuste identificada pero no implementada (D2), ampliación bloqueada pendiente de autorización (D3).
- Siguiente paso: si el usuario autoriza la ampliación, y por separado, si se quiere invertir en construir el algoritmo de ajuste usando `TWT49U`.
