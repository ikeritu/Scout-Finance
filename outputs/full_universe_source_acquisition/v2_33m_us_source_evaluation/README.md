# v2.33M — evaluación de fuentes gratuitas para EE. UU. (Bloque B, fase 4)

Estado: **`BLOCKED_USER_ACTION_REQUIRED`**. Afecta a 5.011 candidatos elegibles (23,67 % del universo, NASDAQ+NYSE+NYSE American+Cboe BZX).

## Resultado

- **Twelve Data (plan Basic)** es la única candidata gratuita viable identificada para EE. UU. — cubre acciones estadounidenses, tiene un parámetro `adjust` para ajuste por splits/dividendos, pero requiere crear una cuenta (no hecho, corresponde al usuario) y no tiene su profundidad histórica ni el plazo exacto de caché documentados con precisión.
- **Stooq descartada explícitamente**: sin términos de uso localizables, caracterizada por la comunidad como "API no documentada" — incumple las reglas del proyecto sobre endpoints no documentados.
- Alpha Vantage y EDGAR no aplican (ya descartada / no distribuye precios).

## Siguiente paso

Requiere que el usuario cree la cuenta gratuita en Twelve Data y guarde la clave como variable de entorno. Ver `US_SOURCE_EVALUATION_v2_33m.md` para el detalle completo y las condiciones.
