# Scout Finance v2.34E — adquisición controlada real (Bloque E, fase 5)

Fecha: 2026-08-31. Alcance: **descarga real de los 50 activos validados en fase 4 (42 JPX + 8 TWSE)** usando los adaptadores del Bloque D. Ninguna cuenta nueva creada; J-Quants reutiliza la credencial ya existente (`SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN`, fase 4); MOPS no requiere credencial.

## Secuencia real ejecutada

1. **Piloto JPX** (5 activos representativos, dispersos entre los 42: `P143`, `P155`, `P163`, `P172`, `P184`) → 5/5 recolectados, 0 fallos, 8-12 divulgaciones reales por activo, los 4 tipos de periodo (`1Q`/`2Q`/`3Q`/`FY`) presentes. **Puerta superada.**
2. **Piloto TWSE** (3 activos: `P016`, `P019`, `P023`) → 3/3 extraídos, 0 fallos, 1 fila real por activo y por fichero (confirma el patrón de fotografía única ya documentado en v2.34B). **Puerta superada.**
3. **Escalado a los 50** → JPX: 42/42 (37 nuevos + 5 del piloto), 0 fallos. TWSE: 8/8 (5 nuevos + 3 del piloto), 0 fallos — sin nueva llamada de red a los 4 CSV de MOPS (ya cacheados del piloto).

## Resultado cuantitativo (evidencia real, `fundamentals_acquisition_report_v2_34e.json`)

| | JPX (J-Quants) | TWSE (MOPS) |
|---|---|---|
| Activos solicitados | 42 | 8 |
| Activos obtenidos | **42 (100%)** | **8 (100%)** |
| Activos faltantes/bloqueados/con error | 0 / 0 / 0 | 0 / 0 / 0 |
| Llamadas de red reales | 42 (una por activo) | 4 (una por fichero de fotografía, no por activo) |
| Divulgaciones totales obtenidas | 389 | 8 activos × 1 periodo × 4 ficheros = 32 filas |
| Rango de ejercicios fiscales cubierto | `CurFYSt` entre 2023-04-01 y 2026-04-01 (~2 años, según el límite ya confirmado en v2.34B) | Un único periodo por empresa: año ROC 115 (2026), trimestre 2 |
| Tipos de periodo presentes | `1Q`, `2Q`, `3Q`, `FY` (84/93/83/129) | Solo trimestral (el más reciente) |

## Cobertura por métrica (presencia real en el campo crudo, no normalizada todavía)

JPX — de 389 divulgaciones totales, las métricas núcleo (`revenue`, `net_income`, `total_assets`, `eps_basic`, `equity_ratio_reported`) están presentes en **342** (87.9%). La diferencia (47 divulgaciones) se investigó y tiene una causa concreta y no ambigua: son anuncios de tipo `EarnForecastRevision` (42) y `DividendForecastRevision` (5) — revisiones de previsión, no estados financieros reales — que el propio proveedor emite sin cifras reales de resultado. **Recomendación directa para el Bloque F**: el normalizador debe excluir estos dos `DocType` de la generación de `FundamentalRecord`, porque no son datos reportados sino guidance, y el esquema de la fase 5 no admite valores estimados (`value_status="estimated"` está prohibido, ver v2.34C).

Otras métricas con cobertura parcial, ya anticipada por la asimetría de fuentes documentada en v2.34B: `roe_reported` (90/389, JGAAP no siempre lo reporta), `book_value_per_share` (120/389), `eps_diluted` (124/389, muchas empresas no tienen instrumentos dilutivos). Ninguna de estas ausencias se ha rellenado ni inferido — quedan como huecos reales a marcar con `missing_reason` en el Bloque F.

TWSE — de las 8 empresas, cobertura del 100% (8/8) en las 11 métricas confirmadas en v2.34B (`revenue`, `cost_of_sales`, `gross_profit`, `operating_income`, `pretax_income`, `net_income`, `current_assets`, `total_assets`, `current_liabilities`, `total_liabilities`, `total_equity`) — consistente con que MOPS reporta el estado financiero completo, no un resumen, para el único periodo que expone.

## Reproducibilidad

`scripts/build_fundamentals_acquisition_report_v2_34e.py` no hace red ni usa credenciales; lee solo lo ya descargado localmente. Verificado: dos ejecuciones consecutivas producen un JSON byte-idéntico (claves ordenadas, sin timestamps en el payload).

## Decisión de la puerta del Bloque E

```json
{"jpx_full_coverage": true, "twse_full_coverage": true}
```

**Ambas puertas superadas con evidencia real, no simulada.** Se autoriza continuar al Bloque F (normalización) con el conjunto completo de 50 activos.

## Seguridad y alcance

- Ninguna credencial nueva creada; la existente nunca se ha impreso ni registrado en ningún informe.
- Ningún dato crudo se ha comiteado (las dos carpetas de salida cruda están en `.gitignore` desde el Bloque D).
- `production_scoring_authorized: false`, `allow_ranking: false` — esta adquisición no habilita puntuación, ranking ni recomendaciones.

**Estado del bloque: `COMPLETED`.**
