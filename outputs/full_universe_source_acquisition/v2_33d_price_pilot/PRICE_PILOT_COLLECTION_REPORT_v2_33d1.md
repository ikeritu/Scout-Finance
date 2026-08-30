# Scout Finance v2.33D1 — informe agregado del piloto real de precios EODHD

Activos esperados: **77** · Activos válidos: **77** · Errores de esquema: **0**.

`P014` excluido (índice no empresarial) y ausente de la colección: **Sí**. `P230` resuelto como `MOG-B.US`.

## Observaciones

- Filas totales en bruto (incluyendo la fila de aviso del proveedor): 18791
- Filas de aviso del proveedor (no son datos numéricos): 77
- Observaciones numéricas válidas: 18714

> Nota: el total de 18.791 citado en validaciones previas corresponde a filas en bruto e incluye una fila de aviso por activo (77). El total de observaciones numéricas válidas es 18714.

## Profundidad histórica

- Sesiones por activo — mínimo: 102, máximo: 253, mediana: 250, media: 243.04, P10: 243, P25: 250, P75: 250, P90: 253.
- Activos con menos de 200 sesiones: 5/77.
- Activos cuya sesión más antigua llega a 2021 o antes: 0/77.
- Fecha mínima observada global: 2025-09-01.
- Fecha máxima observada global: 2026-08-28.
- Fecha solicitada en la descarga (`--from-date`): 2021-01-01.
- Ventana solicitada: 2065 días naturales (~1425 sesiones bursátiles estimadas).
- Cobertura de la mediana de sesiones frente a la ventana solicitada: **17.54%**.

## Distribución por mercado

| Mercado | Activos | Sesiones mín. | Sesiones máx. | Sesiones media |
|---|---:|---:|---:|---:|
| ASX | 13 | 180 | 253 | 242.2 |
| Cboe BZX | 1 | 250 | 250 | 250 |
| NASDAQ | 34 | 102 | 250 | 242.5 |
| NYSE | 18 | 144 | 250 | 243.1 |
| NYSE American | 3 | 250 | 250 | 250 |
| TWSE | 8 | 243 | 243 | 243 |

## Clasificación de la evidencia

### Hechos observados
- Los 77/77 archivos descargados incluyen literalmente el texto del proveedor 'Data is limited by one year as you have free subscription' como última fila de la respuesta EOD.
- Ningún activo tiene su sesión válida más antigua en 2021 o antes; la fecha mínima observada en toda la colección es 2025-09-01 y la máxima es 2026-08-28.
- La mediana de sesiones por activo es 250 frente a una estimación de 1425 sesiones bursátiles implícitas en la fecha de inicio solicitada (2021-01-01).

### Inferencias
- El plan gratuito de EODHD parece aplicar una ventana móvil de aproximadamente un año sobre el endpoint EOD, independientemente del parámetro 'from' solicitado, a partir de la combinación del texto del proveedor y la agrupación observada de fechas.

### Limitaciones no confirmadas
- La regla exacta de corte (días naturales, sesiones bursátiles o una fecha de aniversario fija) no queda confirmada únicamente con esta evidencia.
- No se ha confirmado localmente si un plan de pago de EODHD elimina o relaja este límite; no se ha probado y este piloto no lo autoriza.
- Los 5 activos con menos de 200 sesiones podrían reflejar cotizaciones recientes, baja liquidez u otra restricción del proveedor; no se ha consultado ninguna fuente externa de fecha de salida a bolsa para confirmarlo.

### Requisitos para una prueba de pago
- Confirmar profundidad histórica plurianual para momentum, volatilidad, drawdown y estabilidad plurianual requiere un piloto nuevo, explícitamente autorizado y acotado a un plan de pago. Este cierre no autoriza contratar ni activar dicho plan.

## Seguridad

- No se detectaron credenciales ni URLs con token en los archivos brutos.
- Scoring y ranking productivo: **no autorizados**.
- Este informe no reproduce precios fila a fila ni contenido licenciado.
