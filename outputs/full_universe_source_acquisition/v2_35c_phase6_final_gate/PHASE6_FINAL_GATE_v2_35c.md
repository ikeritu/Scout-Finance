# Scout Finance v2.35C — gate final y cierre de la fase 6

Fecha: 2026-08-31. Decisión: **`COMPLETED_SCOPED`**.

## Resultado real

- Universo autorizado: 50 activos (42 JPX + 8 TWSE).
- Precios y fundamentales disponibles: 50/50.
- Ranking principal comparable: **41 JPX**, todos con confianza `HIGH`.
- Comparabilidad parcial: **7 TWSE**, confianza `LOW`, conservados fuera del ranking principal.
- Revisión requerida: **2** — `P020` por margen neto real del 316,5% y `P178` por ser un banco incompatible con el contrato industrial.
- Shortlist predefinida: top 10.
- Doble ejecución real: byte-idéntica.
- Fecha de corte: 2026-08-31.

## Shortlist cuantitativa experimental

| # | ID | Ticker | Empresa | Score |
|---:|---|---|---|---:|
| 1 | P155 | 4040 | NANKAI CHEMICAL COMPANY,LIMITED | 73,19 |
| 2 | P173 | 7460 | YAGI & CO.,LTD. | 66,06 |
| 3 | P183 | 9769 | GAKKYUSHA CO.,LTD. | 61,50 |
| 4 | P182 | 9537 | HOKURIKU GAS CO.,LTD. | 60,95 |
| 5 | P160 | 4828 | Business Engineering Corporation | 60,69 |
| 6 | P170 | 6946 | Nippon Avionics Co.,Ltd. | 60,44 |
| 7 | P184 | 9997 | BELLUNA CO.,LTD. | 60,43 |
| 8 | P165 | 6098 | Recruit Holdings Co.,Ltd. | 60,24 |
| 9 | P167 | 6420 | GALILEI CO.LTD. | 58,58 |
| 10 | P174 | 7638 | NEW ART HOLDINGS Co.,Ltd. | 58,31 |

## Metodología

- 14 factores en calidad, crecimiento, valoración, momentum y riesgo.
- Pesos definidos antes de aceptar resultados y suma contractual del 100%.
- Periodos anuales preferidos; trimestre solo cuando no existe anual.
- Normalización mediante percentiles globales con midrank determinista.
- Ausencias sin imputar cero, media ni neutral 50.
- Ranking principal limitado a confianza `HIGH`/`MEDIUM`.
- Explicaciones deterministas, sin IA generativa.

## Por qué `COMPLETED_SCOPED`

El motor es reproducible, trazable y apto para validación histórica, pero la promoción se limita a 41 activos JPX. TWSE no es comparable por disponer de un único periodo fundamental y precios sin ajustar; `P178` necesitaría un contrato específico de financieras. No se declara cobertura sobre los 21.165 candidatos.

## Limitaciones

- No existe todavía backtest ni evidencia de rentabilidad fuera de muestra.
- Deuda, capex, FCF y recompras no están disponibles.
- TWSE queda fuera del ranking principal.
- La shortlist prioriza investigación y no constituye recomendación de inversión.

## Gate

**FASE 7 PREPARADA PERO NO AUTORIZADA: se requiere decisión expresa del usuario.**

No se ha ejecutado backtesting, optimización de pesos, interfaz, cartera ni recomendación de compra/venta.
