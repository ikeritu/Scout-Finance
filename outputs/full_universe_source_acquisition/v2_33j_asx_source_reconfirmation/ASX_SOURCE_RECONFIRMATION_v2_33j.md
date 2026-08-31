# Scout Finance v2.33J — reconfirmación de fuentes ASX (Australia)

Fecha: 2026-08-31. Alcance: **investigación documental + una única comprobación técnica de existencia (sin autenticación, sin cuenta, sin gasto)**. No se ha descargado ningún precio, no se ha intentado sortear ninguna medida de seguridad ni sesión autenticada.

## Por qué se hizo

Tras el éxito de v2.33I con TWSE (fuente oficial gratuita real, 16 años de histórico), se pidió comprobar si ASX tiene un equivalente. v2.33F ya había concluido que no, basándose en búsquedas generales; esta pasada busca confirmarlo con evidencia de primera mano en vez de solo resultados de búsqueda.

## Hallazgo 1: política oficial de ASX — sin nivel gratuito

La propia página oficial de ASX ("How to access ASX Price data") describe únicamente dos vías de acceso, ambas de pago:

1. **Acceso directo:** contrato "MarketSource" con ASX, con reporting mensual.
2. **Acceso indirecto:** suscripción a un distribuidor de datos externo (real-time, delayed o end-of-day, todos de pago).

No se menciona ningún nivel gratuito para investigadores individuales. A diferencia de TWSE (Taiwán) o JPX (Japón), **ASX no ofrece una vía oficial gratuita de precios históricos**, ni para descarga puntual ni para consulta programática.

## Hallazgo 2: el único atajo conocido (no oficial) está muerto

Existía un endpoint no documentado usado por el propio sitio web de ASX para mostrar gráficos de precio (`https://www.asx.com.au/asx/1/share/{TICKER}/prices?interval=daily&count=N`), usado durante años por herramientas de terceros (por ejemplo, la librería `pyasx`). Se ha comprobado en vivo con una única petición sin autenticar:

```
GET https://www.asx.com.au/asx/1/share/BHP/prices?interval=daily&count=5
→ HTTP 404 {"error_code":"uri-not-found","error_desc":"Unable to find API service call."}
```

El endpoint ya no existe. Esto coincide con reportes de la comunidad de que ASX añadió medidas de seguridad (sesión/cookies) a partir de febrero de 2024 y que las herramientas basadas en este endpoint dejaron de funcionar desde entonces. No se ha intentado ni se intentará sortear ninguna protección para revivirlo: sería exactamente el tipo de elusión de medidas de seguridad que este proyecto tiene prohibido.

## Decisión

**`NO_FREE_SOURCE_FOUND`, confirmado con evidencia de primera mano** (no solo inferido de búsquedas). ASX se descarta como candidato a fuente gratuita de precios, con la misma conclusión que v2.33F pero ahora respaldada por: (a) la declaración oficial explícita de ASX sobre su modelo de acceso, y (b) la comprobación directa de que el único atajo conocido está bloqueado.

No se autoriza ninguna descarga, scoring, ranking, ni el inicio de la fase 5.

## Estado del roadmap

- No cambia el estado de v2.33D1, v2.33E, v2.33F, v2.33G, v2.33H ni v2.33I.
- Progreso global: 3/8 fases cerradas, fase 4 en curso.
- De los mercados bloqueados/limitados originales (Cboe Europe, ASX, TWSE, BVC), quedan resueltos con fuente gratuita real: **JPX (v2.33G)** y **TWSE (v2.33I)**. Quedan sin fuente gratuita conocida: **ASX** (este cierre) y **Cboe Europe** (v2.33H, bloqueado de forma indefinida). **BVC** (1 símbolo) no se ha investigado con el mismo nivel de detalle por su bajo impacto.
- Siguiente paso recomendado (no ejecutado): ninguno para ASX salvo que el usuario decida investigar distribuidores de pago (ya descartados como categoría por decisión del usuario) o quiera que se revise BVC (Colombia, 1 símbolo) con el mismo nivel de detalle aplicado aquí.
