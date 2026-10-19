# v2.50D — Puntuación cripto v1: estudio del universo real y umbrales propuestos

Estado: `CRYPTO_SCORE_THRESHOLDS_APPROVED` (los seis puntos fueron aprobados por el usuario el 2026-10-19; la implementación está en `CRYPTO_SCORE_v2_50e.md`). Fase 3 del roadmap cripto, primera mitad: **estudio descriptivo y propuesta**. Todo es heurística local de investigación: **no predice rentabilidad ni es una recomendación**.

Datos: universo real de CoinGecko del 2026-10-19 (2.000 monedas), leído con la capa de datos v2.50C; 133 llamadas (133 de 8.000 del tope de seguridad). Informe completo, solo con agregados: `universe_signal_study_v2_50d.md` (reproducible con `scripts/crypto_base_rate_study_v2_50d.py`).

## Hechos observados
- **Exclusión:** de 2.000 monedas se excluyen 178 (8,9 %): 149 stablecoins, 26 de liquid staking y 3 envueltas. Quedan 1.822.
- **El universo es casi todo microcapitalización:** mediana 14,8 M$; el 55 % está entre 5 y 30 M$ y el 13 % por debajo de 5 M$. Con ≤ 100 M$ pasa el 87 % y con ≤ 500 M$ el 95 %. **«Capitalización pequeña» no discrimina**: no sirve como señal principal como en bolsa.
- **Liquidez muy desigual:** volumen 24 h con mediana de 0,45 M$; solo el 49 % supera 0,5 M$. Capitalización ≥ 5 M$ y volumen ≥ 0,5 M$ deja 839 monedas (46 %).
- **Rotación (volumen 24 h / capitalización):** p50 0,02, p90 0,26, p99 1,25. ≥ 0,25: 10,4 %; ≥ 0,50: 4,1 %; **≥ 1,00 (el volumen de un día supera la capitalización): 25 monedas (1,4 %)**, sospechoso de volumen artificial.
- **Mercado a la baja ese día:** mediana de −7,8 % a 7 días y −3,9 % a 30 días. Momentum 30 d ≥ +25 %: 11,1 %; ≥ +60 %: 5,8 %; ≥ +100 %: 2,9 %. Momentum 7 d ≥ +15 %: 4,7 %; ≥ +30 %: 2,8 %.
- **Dilución:** circulante/total < 0,5 en el 23 % y < 0,3 en el 14,5 %; FDV/capitalización ≥ 3 en el 15,6 %.
- **Volumen relativo** (muestra estratificada de 120 monedas, 111 con dato): mediana 0,65 y p90 1,05; ≥ 2 en 2 monedas y ≥ 3 en 1. La señal es **rara**, como en bolsa. La versión «estable» (último día completo / media de los 30 anteriores) da cifras parecidas (≥ 2 en 3 monedas).
- **Ruptura del máximo de cierre de 30 días:** 7 de 111 (5,8 %); **con volumen relativo ≥ 2: 1**.

## Propuesta de umbrales (hipótesis a aprobar o ajustar)
**Capas, igual que en bolsa:** puertas de exclusión → puntos por señales → topes por dato ausente y por riesgo → nivel.

**Puertas (no son puntos):** categorías excluidas (ya hecho); capitalización ≥ 5 M$ y volumen 24 h ≥ 0,5 M$. Por debajo, la moneda no se puntúa y aparece como «Sin liquidez suficiente» (visible y contada, nunca oculta).

| Señal | Fuerte (cuenta como «señal fuerte») | Parcial | Puntos (fuerte / parcial) | Frecuencia en el universo |
|---|---|---|---|---|
| Rotación (volumen 24 h / capitalización) | ≥ 0,25 y < 1,00 | ≥ 0,10 | 20 / 10 | 10 % / 25 % |
| Volumen relativo (24 h móvil / media de 30 días completos) | ≥ 3 | ≥ 2 | 22 / 12 | ~1 % / ~2 % (muestra) |
| Momentum 30 d | ≥ +60 % | ≥ +25 % | 16 / 8 | 5,8 % / 11 % |
| Momentum 7 d | ≥ +30 % | ≥ +15 % | 12 / 6 | 2,8 % / 4,7 % |
| Ruptura del máximo de cierre de 30 d con volumen relativo ≥ 2 | sí | — | 14 / — | ~1 % (muestra) |
| Capitalización ≤ 100 M$ | — | sí | — / 6 | 87 % (poco informativa: peso bajo) |

Máximo: 90 puntos (como en bolsa, que no llega a 100). No hay punto por precio unitario (no significa nada en cripto) ni por catalizador (sin fuente gratuita fiable).

**Topes (copiados de bolsa):** falta rotación, volumen relativo o momentum 30 d → máximo 44; menos de 3 señales fuertes → máximo 59; exactamente 3 → máximo 74; 4 sin ruptura → máximo 84.

**Factores de riesgo, que no suman puntos:** *rotación ≥ 1,00* (volumen sospechoso) → sin puntos de rotación y máximo 44; *dilución alta* (circulante/total < 0,3 **o** FDV/capitalización ≥ 3) → máximo 69, que queda por debajo de los 72 puntos del nivel medio: **una moneda con dilución alta no puede pasar del nivel bajo**. Ambos se muestran como etiqueta en la ficha.

**Niveles (mismas reglas que en bolsa):** alto: ≥ 88, ≥ 5 señales fuertes y ruptura; medio: ≥ 72 y ≥ 4 señales fuertes; bajo: ≥ 55 y ≥ 3 señales fuertes; el resto, vigilancia. Con un dato crítico ausente: máximo 59 y nunca alto.

**Volumen relativo con ventana móvil de 24 h:** a diferencia de bolsa no hay «día parcial» que avisar, porque el mercado no cierra. Se compara el volumen de 24 h con la media de los últimos 30 días completos (UTC); la ventana de 24 h solapa con el último día completo, y eso se declara.

## Simulación de la propuesta sobre la muestra (sin llamadas nuevas)
Muestra estratificada de 120 monedas (no representativa: pesa más a las grandes): 35 quedan bajo las puertas, 85 se puntúan.
- Niveles: **1 medio, 0 bajo, 84 vigilancia.**
- Señales fuertes por moneda: 0 en 75, 1 en 8, 2 en 1, 4 en 1.
- Dilución alta marcada en 11; rotación sospechosa en 0 (dentro de la muestra).

Es selectiva, como la de bolsa (hoy 0 candidatos de 140): **no genera ruido**, pero con una muestra de 85 monedas y un día de mercado a la baja no se puede afinar más.

## Decisiones que necesito del usuario (con mi recomendación)
1. **Capitalización como señal:** peso bajo (6 puntos, no cuenta como señal fuerte) porque el 87 % la cumple. *Recomendado.* Alternativa: dejarla solo como puerta.
2. **Puertas de liquidez:** capitalización ≥ 5 M$ y volumen ≥ 0,5 M$ (46 % del universo). *Recomendado.* Más estricto (≥ 1 M$) dejaría el 41 % de las monedas.
3. **Rotación ≥ 1,00 como volumen sospechoso** (tope 44, sin puntos): afecta al 1,4 %. *Recomendado.*
4. **Dilución alta** como tope de 69 en vez de solo una etiqueta: afecta a ~15–23 % de las monedas. *Recomendado el tope*, porque el desbloqueo de suministro es un riesgo real y de otro modo una moneda con dilución fuerte podría salir como candidata alta.
5. **Umbrales de momentum y volumen relativo** como en la tabla (+60 %/+25 % a 30 d, +30 %/+15 % a 7 d, 3/2 de volumen). *Recomendado*; son los más selectivos con la señal ya rara.
6. **Ventana de volumen relativo móvil de 24 h**, en lugar del último día completo: *recomendado la móvil* (la «estable» no aporta diferencia visible y la móvil refleja lo que pasa ahora).

## Límites
Los umbrales se han mirado con **una foto de un día** (2026-10-19, con el mercado a la baja) y con una muestra de 120 monedas para las señales con serie diaria. El plan gratuito da 1 año de histórico: sirve para tasas base descriptivas, no para afirmar capacidad predictiva ni para un backtest largo. Las señales de derivados (financiación, open interest) quedan para la fase 5 y no puntúan en v1.
