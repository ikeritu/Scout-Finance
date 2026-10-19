# v2.50E — Puntuación cripto v1 implementada

Estado: `CRYPTO_SCORE_V1_IMPLEMENTED`. Cierra la fase 3 del roadmap cripto. Código nuevo en `src/crypto_v2_50/scoring.py` y `src/crypto_v2_50/signals.py` (funciones puras: sin red, sin caché, sin Streamlit) con su prueba. **La app no cambia**: el botón «Unicornios Crypto» sigue desactivado hasta la fase 4. Es una heurística local de investigación: no predice rentabilidad ni es una recomendación.

## Decisiones aprobadas el 2026-10-19 y cómo quedan
El usuario aprobó los seis puntos de `CRYPTO_SCORE_PROPOSAL_v2_50d.md` («sí a todo»):

| # | Decisión | Implementación |
|---|---|---|
| 1 | Capitalización con peso bajo | 6 puntos si ≤ 100 M$; no cuenta como señal fuerte |
| 2 | Puertas de liquidez | capitalización ≥ 5 M$ y volumen 24 h ≥ 0,5 M$; por debajo, nivel `NO_LIQUIDITY` («Sin liquidez suficiente»), puntuación 0, contada y visible |
| 3 | Rotación ≥ 1,00 sospechosa | etiqueta «rotación sospechosa», sin puntos de rotación, máximo 44 |
| 4 | Dilución alta con tope | circulante/total < 0,3 **o** FDV/capitalización ≥ 3 → máximo 69 |
| 5 | Umbrales | rotación ≥ 0,25 / ≥ 0,10 (20 / 10 pts), volumen relativo ≥ 3 / ≥ 2 (22 / 12), momentum 30 d ≥ +60 % / ≥ +25 % (16 / 8), momentum 7 d ≥ +30 % / ≥ +15 % (12 / 6), ruptura de 30 días con volumen relativo ≥ 2 (14) |
| 6 | Volumen relativo móvil | volumen de 24 h de `/coins/markets` / media de los 30 últimos días completos (UTC); la ventana solapa con el último día completo y eso se declara |

Máximo 90 puntos. Topes: dato crítico ausente (volumen relativo o momentum 30 d) → 44; menos de 3 señales fuertes → 59; exactamente 3 → 74; 4 sin ruptura → 84. Niveles: alto ≥ 88 con ≥ 5 señales fuertes y ruptura; medio ≥ 72 con ≥ 4; bajo ≥ 55 con ≥ 3; el resto, vigilancia. Sin capitalización o volumen: `NO_DATA`.

**Consecuencia que conviene tener clara:** el tope de 69 de la dilución queda por debajo de los 72 puntos que exige el nivel medio, así que **una moneda con dilución alta no puede pasar del nivel bajo** (en la propuesta se decía «nunca nivel alto»; el efecto real es más estricto). La prueba lo fija.

## Preselección: cuánto detalle cargar
`preselect()` decide para qué monedas vale la pena gastar una llamada de serie diaria: las que, con las mejores señales posibles de la serie (volumen relativo fuerte y ruptura), todavía podrían llegar al nivel bajo. La regla es exacta, no una aproximación: se comprobó **exhaustivamente sobre una cuadrícula** de 5×5×6×5×2×31 combinaciones que ninguna moneda que llegue a candidata queda fuera.
- **Hecho observado hoy (caché del 2026-10-19):** de 1.822 monedas no excluidas, 839 pasan las puertas y **155** podrían aún llegar al nivel bajo. El roadmap suponía ~100: con 155 una búsqueda completa cuesta unas 8 + 155 ≈ **163 llamadas** (más 5 una vez al día para las exclusiones), unas 49 búsquedas al mes con el tope de 8.000. La caché de 24 h hace que repetir la búsqueda el mismo día no gaste llamadas.

## Verificación
- `tests/qa_crypto_explosive_score_v2_50e.py` (8 casos, sin red): cada umbral en su límite inferior y superior; puertas y límites exactos; topes por dato ausente y por número de señales fuertes; factores de riesgo (rotación justo en 1,0 y justo debajo; dilución en 0,29/0,30 y FDV 2,99/3); niveles; monotonía (ninguna señal que mejora baja la puntuación, salvo el caso deliberado de la rotación sospechosa); nada se inventa (None, NaN e infinitos no puntúan); la preselección exhaustiva. **Se comprobó que las pruebas fallan** al mutar el código en tres puntos (umbral de rotación, tope de dilución y preselección demasiado estricta).
- **Reproducción de la propuesta con la implementación real**, sobre los datos en caché (sin llamadas): muestra de 120 monedas → 35 «sin liquidez suficiente», **1 candidato medio y 84 en vigilancia**; señales fuertes 0/1/2/4 en 75/8/1/1 monedas; dilución marcada en 11; máximo 74. Idéntico a la simulación de v2.50D.
- `daily_signals` pasó del script de estudio al paquete (`signals.py`) y ahora trata NaN como dato ausente; su prueba del script sigue pasando.

## Límites
Los umbrales son hipótesis elegidas por selectividad con una foto del 2026-10-19 y un año de histórico como máximo; no hay evidencia de capacidad predictiva ni se afirma. Las señales de derivados y los catalizadores no puntúan en v1. Con el mercado a la baja ese día, la proporción de candidatas puede cambiar mucho con otro régimen de mercado: conviene volver a mirar la distribución cuando la interfaz esté funcionando.
