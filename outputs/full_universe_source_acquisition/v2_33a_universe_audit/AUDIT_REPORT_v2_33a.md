# Scout Finance v2.33A — auditoría de elegibilidad y cobertura

## Resultado

Se han auditado las **43.089 filas** del universo operativo v2.30D, verificando previamente su SHA-256. El proceso es de solo lectura y produce exactamente una fila de auditoría por registro de entrada.

## Tipología normalizada preliminar

| Grupo de auditoría | Filas | Interpretación |
|---|---:|---|
| Candidato a capital común | 23.730 | Requiere política final de v2.33B |
| Fondo o nota (ETF/ETC/ETN) | 10.409 | No debe mezclarse automáticamente con acciones |
| Sin clasificar | 8.765 | Requiere enriquecimiento o revisión |
| Recibo depositario (ADR/DR) | 158 | Puede representar una cotización alternativa |
| Tipo específico sin resolver | 20 | Revisión por reglas del proveedor |
| Vehículo de inversión condicional | 7 | Revisión individual o por clase |

Estos grupos no son una decisión de elegibilidad ni una puntuación financiera.

## Identidad y posibles duplicados

- 39.883 filas conservan ticker y nombre; 3.206 carecen de al menos uno de esos campos.
- No hay colisiones en la clave `exchange + ticker` entre las filas que tienen ticker.
- Hay 299 filas repartidas en 133 grupos con ISIN repetido. Se marcan como posibles cotizaciones cruzadas o duplicados, sin eliminarlas automáticamente.

## Cobertura financiera actual

| Campo | Disponible | Ausente |
|---|---:|---:|
| Moneda | 11.311 | 31.778 |
| Sector | 3.705 | 39.384 |
| Industria | 4.401 | 38.688 |
| Capitalización | 23 | 43.066 |

El catálogo actual es suficiente para identidad y procedencia, pero **no permite construir un scoring fundamental fiable**. No contiene todavía series de precios, estados financieros históricos, múltiplos ni métricas de riesgo comparables.

## Decisiones reservadas para v2.33B

1. Qué tipos de instrumento serán elegibles para cada estrategia.
2. Cómo tratar cotizaciones cruzadas, ADR/DR e ISIN repetidos.
3. Qué hacer con filas sin ticker o nombre.
4. Qué cobertura mínima exigirá el futuro análisis.

## Garantías preservadas

- dataset de entrada no modificado;
- punteros operativos no modificados;
- scoring productivo no autorizado;
- rankings y recomendaciones deshabilitados.
