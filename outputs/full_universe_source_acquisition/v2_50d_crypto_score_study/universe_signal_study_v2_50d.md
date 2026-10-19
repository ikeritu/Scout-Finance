# Estudio descriptivo de señales cripto sobre el universo real (v2.50D)

Describe cuántas monedas pasaría cada umbral candidato. **No predice nada** ni mide rentabilidad futura. Solo agregados: no se guardan cifras por moneda.

Universo leído: **2,000** monedas (datos de CoinGecko del 2026-10-19 10:48 UTC). Excluidas por categoría: **178** (8.9 %) — liquid-staking: 26, stablecoins: 149, wrapped-tokens: 3 (una moneda puede estar en más de una). Quedan **1,822**.

### Composición por capitalización (monedas no excluidas)

| Banda | Monedas |
|---|---|
| ≥ 1.000 M$ | 60 (3.3 %) |
| 300 M$ – 1.000 M$ | 56 (3.1 %) |
| 100 – 300 M$ | 123 (6.8 %) |
| 30 – 100 M$ | 336 (18.4 %) |
| 5 – 30 M$ | 1,002 (55.0 %) |
| < 5 M$ | 245 (13.4 %) |

Sin capitalización utilizable: 0.

## A. Señales que salen solo de `/coins/markets` (todas las monedas no excluidas con capitalización)

Base: **1,822** monedas.

### Distribuciones

- Capitalización (M$): p10 4.49 · p25 6.90 · p50 14.83 · p75 42.40 · p90 147.19 · p99 5,382.30
- Volumen 24 h (M$): p10 0.00 · p25 0.02 · p50 0.45 · p75 2.77 · p90 9.45 · p99 239.42
- Rotación (volumen 24 h / capitalización): p10 0.00 · p25 0.00 · p50 0.02 · p75 0.10 · p90 0.26 · p99 1.25
- Cambio 7 d (%): p10 -20.65 · p25 -14.33 · p50 -7.77 · p75 -0.93 · p90 3.28 · p99 69.23
- Cambio 14 d (%): p10 -27.77 · p25 -19.36 · p50 -11.22 · p75 -0.75 · p90 7.20 · p99 88.65
- Cambio 30 d (%): p10 -28.59 · p25 -15.45 · p50 -3.90 · p75 3.96 · p90 29.65 · p99 255.25

### Cuántas monedas pasa cada umbral candidato

| Señal | Umbral | Monedas que lo cumplen |
|---|---|---|
| Capitalización pequeña | ≤ 50 M$ | 1,432 (78.6 %) |
| Capitalización pequeña | ≤ 100 M$ | 1,583 (86.9 %) |
| Capitalización pequeña | ≤ 500 M$ | 1,727 (94.8 %) |
| Liquidez mínima (suelo) | volumen 24 h ≥ 0,1 M$ | 1,157 (63.5 %) |
| Liquidez mínima (suelo) | volumen 24 h ≥ 0,5 M$ | 892 (49.0 %) |
| Liquidez mínima (suelo) | volumen 24 h ≥ 1 M$ | 755 (41.4 %) |
| Rotación | ≥ 0,10 | 459 (25.2 %) |
| Rotación | ≥ 0,25 | 190 (10.4 %) |
| Rotación | ≥ 0,50 | 74 (4.1 %) |
| Rotación sospechosa | ≥ 1,00 (el volumen de un día supera la capitalización) | 25 (1.4 %) |
| Momentum 7 d | ≥ +15 % | 86 (4.7 %) |
| Momentum 7 d | ≥ +30 % | 51 (2.8 %) |
| Momentum 30 d | ≥ +25 % | 203 (11.1 %) |
| Momentum 30 d | ≥ +60 % | 105 (5.8 %) |
| Momentum 30 d | ≥ +100 % | 53 (2.9 %) |

Con el suelo propuesto (capitalización ≥ 5 M$ **y** volumen 24 h ≥ 0,5 M$) quedan **839 (46.0 %)** monedas.

### Dilución (factor de riesgo, no de puntos)

- Circulante / total: p10 0.23 · p25 0.54 · p50 1.00 · p75 1.00 · p90 1.00 · p99 1.00 (base 1,819; sin total declarado: 3).
- Circulante / total < 0,5: 422 (23.2 %) · < 0,3: 264 (14.5 %).
- FDV / capitalización: p10 1.00 · p25 1.00 · p50 1.00 · p75 1.86 · p90 4.38 · p99 20.61 (base 1,822). ≥ 3: 284 (15.6 %).

## B. Señales que necesitan la serie diaria (muestra estratificada)

Muestra de **120** monedas repartidas por banda de capitalización (de 5 M$ para arriba), elegidas sin azar: a intervalos regulares por orden de capitalización dentro de cada banda. No es representativa del universo entero: sirve para ver el orden de magnitud de las señales con serie diaria.

| Banda | Monedas en la muestra |
|---|---|
| ≥ 1.000 M$ | 24 |
| 300 M$ – 1.000 M$ | 24 |
| 100 – 300 M$ | 24 |
| 30 – 100 M$ | 24 |
| 5 – 30 M$ | 24 |

- Volumen relativo (volumen 24 h móvil / media de los últimos 30 días completos): p10 0.28 · p25 0.44 · p50 0.65 · p75 0.84 · p90 1.05 · p99 2.61 (base 111).
- Volumen relativo estable (último día completo / media de los 30 anteriores): p10 0.19 · p25 0.37 · p50 0.51 · p75 0.78 · p90 0.93 · p99 3.79 (base 111).

| Señal | Umbral | Monedas de la muestra |
|---|---|---|
| Volumen relativo móvil | ≥ 2 | 2 (1.7 %) |
| Volumen relativo móvil | ≥ 3 | 1 (0.8 %) |
| Volumen relativo estable | ≥ 2 | 3 (2.5 %) |
| Volumen relativo estable | ≥ 3 | 3 (2.5 %) |
| Ruptura del máximo de cierre de 30 días | precio actual > máximo de los 30 cierres anteriores | 7 (5.8 %) |

Ruptura **con** volumen relativo móvil ≥ 2: 1 (0.8 %).

Llamadas usadas por esta ejecución: 133 · mes 2026-10: 133 de 8,000 (tope de seguridad).
