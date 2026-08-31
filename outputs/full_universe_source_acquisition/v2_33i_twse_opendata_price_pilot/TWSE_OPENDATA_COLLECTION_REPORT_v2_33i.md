# Scout Finance v2.33I — informe agregado del piloto TWSE (datos abiertos oficiales)

Activos esperados: **8** · Activos válidos: **8** · Errores de esquema: **0**.

- Observaciones numéricas válidas: 29472
- Filas de calendario sin operación (OHLC nulo): 12
- Sesiones por activo — mínimo: 1378, máximo: 4082, mediana: 4076.0, media: 3684, P10: 3628, P25: 4074, P75: 4079, P90: 4079.
- Fecha mínima confirmada por el propio proveedor: 2010-01-04.
- Fecha mínima observada global: 2010-01-04. Fecha máxima observada global: 2026-08-31.
- Activos que alcanzan la fecha mínima confirmada: 6/8.

## Por activo

| pilot_id | ticker | sesiones | fecha mínima | fecha máxima | filas sin operación |
|---|---|---:|---|---|---:|
| P016 | 1101.TW | 4079 | 2010-01-04 | 2026-08-28 | 3 |
| P017 | 1525.TW | 4078 | 2010-01-04 | 2026-08-31 | 5 |
| P018 | 2102.TW | 4079 | 2010-01-04 | 2026-08-28 | 3 |
| P019 | 2514.TW | 4074 | 2010-01-04 | 2026-08-28 | 1 |
| P020 | 3049.TW | 4074 | 2010-01-04 | 2026-08-28 | 0 |
| P021 | 4952.TW | 3628 | 2011-11-01 | 2026-08-28 | 0 |
| P022 | 6756.TW | 1378 | 2020-12-24 | 2026-08-28 | 0 |
| P023 | 9958.TW | 4082 | 2010-01-04 | 2026-08-28 | 0 |

## Clasificación de la evidencia

### Hechos observados
- El propio endpoint oficial STOCK_DAY de TWSE (www.twse.com.tw), gratuito y sin cuenta ni clave, rechaza explícitamente cualquier fecha anterior al 2010-01-04 con el mensaje '查詢日期小於99年1月4日，請重新查詢!' ('fecha de consulta anterior al 4 de enero del año 99 de la República'; año 99 ROC = 2010) -- un límite declarado por el propio proveedor, no inferido.
- 6/8 activos alcanzan esa fecha mínima confirmada; los otros 2 empiezan más tarde, coherente con una cotización más reciente.
- El endpoint devuelve OHLC en bruto (sin ajustar) -- no incluye ningún factor de ajuste por splits/dividendos, a diferencia del Adjusted_close de EODHD o los campos AdjFactor/AdjClose de J-Quants.
- 12 filas de calendario en 4 de los 8 activos tienen OHLC nulo (sin operación ese día), sin ningún código explicativo en el campo 'Note'; es una fracción muy pequeña del total.

### Limitaciones no confirmadas
- No se ha confirmado si alguno de los 8 tickers sufrió un split o un dividendo grande durante esta ventana que distorsione cálculos de rentabilidad a largo plazo hechos de forma ingenua (sin ajustar); el campo 'Note' de TWSE no marcó ninguna de las 12 filas nulas ni ninguna otra fila de la muestra.
- No se ha confirmado la causa exacta de las 12 filas de calendario con OHLC nulo (suspensión de cotización u otra causa).

## Seguridad

- Sin credenciales: fuente pública y oficial, sin cuenta ni clave.
- Scoring y ranking productivo: **no autorizados**.
- Este informe no reproduce precios fila a fila.