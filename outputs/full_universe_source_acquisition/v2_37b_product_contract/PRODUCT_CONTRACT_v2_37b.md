# Scout Finance v2.37B — contrato de producto

## Propósito

Scout Finance v2.37 es un centro **local y privado de investigación**. Permite explorar el universo acotado de las fases 4–6, consultar evidencia, comparar empresas, mantener listas privadas y exportar informes trazables.

No es un asesor financiero, un sistema de señales, un gestor de cartera ni una interfaz de broker.

## Estados canónicos

| Estado | Uso en producto | Acción permitida |
|---|---|---|
| `ELIGIBLE_PARTIAL` | 41 activos JPX comparables bajo el contrato v2.35 | Ranking experimental principal |
| `PARTIAL_COMPARABILITY` | 7 activos TWSE | Vista separada, nunca mezclada en el ranking JPX |
| `REVIEW_REQUIRED` | P020 y P178 | Inspección manual, sin posición automática |
| `BLOCKED` | Datos ausentes o incompatibles | Bloqueo explícito, sin sustitución demo |

## Modos de datos

- `REAL_LOCAL_READY`: precios, fundamentales y scoring detallado locales disponibles.
- `AGGREGATE_ONLY`: solo universo y evidencia agregada publicable.
- `PARTIAL_DATA`: existe parte del detalle local; cada vista declara sus ausencias.
- `BLOCKED_MISSING_DATA`: falta un contrato canónico.
- `INCOMPATIBLE_VERSION`: los datos contradicen el gate de fases anteriores.

No existe fallback automático a datos demo, sintéticos o descargados de Internet.

## Límites obligatorios

- Decisión de fase 7: `INSUFFICIENT_EVIDENCE`.
- JPX no alcanza la profundidad exigida para dos ventanas OOS.
- TWSE no dispone de fechas de publicación fundamental verificadas y sus precios no están ajustados.
- El scoring ordena prioridades de investigación; no se presenta como predictivo.
- Sin llamadas de red, cuentas nuevas, broker, ejecución de órdenes o despliegue público.
- P020 conserva su anomalía real; P178 requiere un contrato específico para financieras.

## Privacidad y licencia

Las watchlists se guardan en `data/watchlists/` y permanecen fuera de Git. Los datos detallados derivados de fuentes licenciadas permanecen locales. Solo se versionan contratos, código, pruebas e informes agregados revisados.

## Aviso obligatorio

> Herramienta experimental de investigación. No constituye asesoramiento financiero. El scoring no dispone de evidencia histórica suficiente para considerarse predictivo.
