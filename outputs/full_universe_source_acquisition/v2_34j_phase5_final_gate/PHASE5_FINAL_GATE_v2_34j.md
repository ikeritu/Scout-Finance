# Scout Finance v2.34J — gate final y cierre de la fase 5 (Bloque J)

Fecha: 2026-08-31. Este documento cierra la fase 5 (adquisición, normalización y validación de fundamentales reales) con base en la evidencia acumulada de v2.34A a v2.34I. No autoriza scoring, rankings, recomendaciones de inversión, modificación de la interfaz más allá de pruebas internas, ni el inicio de la fase 6.

## J1 — Matriz de fuentes y licencias

| Mercado | Fuente | Endpoint | Cuenta/token | Límite real | Profundidad | Retraso | Licencia | Decisión (Bloque B) |
|---|---|---|---|---|---|---|---|---|
| JPX (Japón) | J-Quants (oficial) | `/v2/fins/summary` | Reutiliza la cuenta ya creada en fase 4 (`SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN`) | ~5 solicitudes/min documentadas, más estricto en la práctica (v2.33G) | ~2 años, trimestral+anual | 12 semanas | Uso personal, confirmada compatible en v2.33N; prohíbe redistribuir datos brutos | `APPROVED_SCOPED` (v2.34B) — desglose de deuda exige `/fins/details`, exclusivo del plan Premium de pago, descartado |
| TWSE (Taiwán) | MOPS opendata (regulador oficial) | `/opendata/{t187ap03_L,t187ap06_L_ci,t187ap07_L_ci,t187ap17_L}.csv` | Ninguna | No documentado; ritmo prudente autoimpuesto | Un único periodo (el más reciente divulgado) por empresa, sin histórico | No confirmado | 政府資料開放授權條款第1版 (Government Open Data License v1.0), misma familia que precios TWSE (v2.33I) | `APPROVED_SCOPED` (v2.34B) — sin flujo de caja confirmado, sin consulta histórica por empresa |

Ninguna fuente exigió `REQUIRES_PAID_PLAN` ni quedó `LICENSE_UNCLEAR`. Ninguna cuenta nueva se ha creado en la fase 5.

## J2 — Matriz de cobertura (real, medida — no estimada)

| | JPX | TWSE |
|---|---|---|
| Activos objetivo | 42 | 8 |
| Activos obtenidos | **42 (100%)** | **8 (100%)** |
| Registros normalizados (Bloque F) | 10.227 | 88 |
| Registros derivados (Bloque G) | incluidos en el total de 3.602 | incluidos en el total de 3.602 |
| Registros totales validados (Bloque H) | **13.917 combinados**, 0 inválidos contra el esquema | |
| Historia real | ~2 años, `1Q`/`2Q`/`3Q`/`FY` | Un único periodo (año ROC 115 / Q2 2026) |
| Cobertura de métricas núcleo (revenue/net_income/total_assets/eps/equity_ratio) | 87,9% de las divulgaciones reales (342/389); el resto son revisiones de previsión sin cifra real, excluidas por diseño del normalizador | 100% (8/8) de las 11 métricas confirmadas en v2.34B |
| Cobertura del catálogo canónico completo (37 métricas) | ~55% (`comparability_score` medio) | ~38% (`comparability_score` medio) |
| Ecuaciones contables comprobables | 0 (sin `total_liabilities`/`cost_of_sales` independientes — nunca comprobación circular) | 16/16 pasadas (100%), tolerancia 2% |
| Métricas derivadas exclusivas de esta fuente | `revenue_growth_yoy`, `net_income_growth_yoy` (203 cada una) | `gross_margin`, `current_ratio` (8 cada una) |
| Deuda desglosada, capex, FCF, buybacks | **No disponibles en ninguna fuente aprobada** — 648 registros bloqueados por métrica con motivo documentado (`calculation_impossible_missing_components`), no omitidos en silencio | |
| Score de calidad compuesto (Bloque H) | 0,87-0,90 según muestra, **50/50 activos `PROMOTABLE`** (umbral ≥0,75) | |

## J3 — Catálogo y esquema (resumen)

- `schemas/fundamental_record_v1.schema.json` — contrato JSON Schema draft 2020-12, formato long (una fila por observación), `additionalProperties: false`.
- `config/fundamental_metrics_v1.json` — **37 métricas canónicas** (29 del Bloque C + 8 calculadas añadidas en el Bloque G), cada una con `reported_by` explícito por fuente.
- `config/fundamental_missing_reasons_v1.json` — 10 códigos cerrados de motivo de ausencia.
- `value_status="estimated"` prohibido en código (regla 3.1), aunque el enum del esquema lo conserva para poder fallar explícitamente si apareciera.
- `statement_type` distingue `derived_reported_by_provider` (una ratio que el proveedor mismo calcula y publica, p. ej. ROE de J-Quants) de `derived_calculated_by_scout_finance` (calculado por este proyecto en el Bloque G) — nunca confundidos.

## J4 — Limitaciones (declaradas explícitamente, no ocultas)

1. **Alcance de 50 activos, no del universo completo.** Esta fase trabaja exclusivamente sobre los 50 activos ya validados en la fase 4 (42 JPX + 8 TWSE) — **0,24% del censo canónico de 21.165 candidatos**, la misma cifra de cobertura de precios heredada de v2.33R. La fase 5 no ha intentado ni intenta ampliar el universo de mercados ni de activos.
2. **Deuda desglosada, capex, flujo de caja libre y recompras no están disponibles en ninguna de las dos fuentes aprobadas**, confirmado empíricamente (no asumido) en v2.34B y re-confirmado con datos reales en el Bloque G: 648 registros por métrica, 100% bloqueados con motivo documentado.
3. **TWSE ofrece un único periodo por empresa**, sin histórico — cualquier serie temporal real para TWSE solo podrá construirse acumulando esta fotografía trimestral hacia adelante en futuras ejecuciones, no retrospectivamente.
4. **JPX excluye por diseño las revisiones de previsión** (`EarnForecastRevision`, `DividendForecastRevision`) — 47 de 389 divulgaciones reales no producen ningún `FundamentalRecord`, porque son guidance del proveedor, no un estado financiero.
5. **No está confirmado si las cifras de MOPS son del trimestre discreto o acumuladas desde el inicio del ejercicio** — cada registro TWSE lleva la bandera `period_cumulative_vs_discrete_unconfirmed` en vez de asumir una de las dos.
6. **Una anomalía económica real queda sin resolver**: `P020` (TWSE) tiene un margen neto del 316,5% en Q2 2026, verificado como una cifra real del proveedor (no un error de normalización), marcada para revisión humana, no corregida.
7. **Ninguna conversión de divisa se ha aplicado** — JPY y TWD se mantienen tal cual, sin ningún tipo de cambio ni comparación cruzada de moneda.
8. **La dimensión `coherence` del score de calidad es `null` (no comprobable) para el 100% de los activos JPX**, porque ninguna de sus ecuaciones contables tiene los componentes independientes necesarios — esto no penaliza el score compuesto (se excluye del promedio), pero significa que la validación contable real solo existe para TWSE.

## J5 — Runbooks (reproducibilidad, bloque por bloque)

```bash
# Bloque D — adquisición real (requiere SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN para JPX; TWSE no necesita credencial)
python scripts/download_jquants_fundamentals_v2_34d.py --execute
python scripts/download_twse_mops_fundamentals_v2_34d.py --execute

# Bloque E — informe de cobertura de la adquisición (sin red)
python scripts/build_fundamentals_acquisition_report_v2_34e.py

# Bloque F — normalización a FundamentalRecord (sin red)
python scripts/build_fundamental_dataset_v2_34f.py

# Bloque G — métricas derivadas (sin red)
python scripts/build_fundamental_derived_metrics_v2_34g.py

# Bloque H — validación y score de calidad (sin red)
python scripts/build_fundamental_validation_v2_34h.py

# Bloque I — suite offline completa (sin red, sin credenciales)
python tests/qa_fundamentals_phase5_full_suite_v2_34i.py
```

Cada script de `build_*` es idempotente y determinista: dos ejecuciones consecutivas contra los mismos ficheros locales producen un JSON byte-idéntico (verificado en cada bloque).

## J6 — Decisión

**`COMPLETED_PROMOTABLE`**

Justificación, no elegida por conveniencia sino por evidencia medida:

1. **Alcance declarado desde el inicio de la fase** (los 50 activos de la fase 4, no el universo completo) — cumplido al 100% (50/50), sin necesidad de re-litigar el alcance de mercados, ya decidido en la fase 4.
2. **Esquema canónico formal, probado y sin excepciones** — 13.917 registros reales, **0 inválidos contra el esquema** en todos los bloques F, G y H.
3. **Adquisición real, no simulada** — 42/42 JPX y 8/8 TWSE, 0 fallos, evidencia con `download_report` real por fuente.
4. **Normalización honesta** — ningún valor ausente se convirtió en cero; 43,5% de los campos JPX quedan `not_reported_by_company` con motivo explícito, nunca inventado.
5. **Métricas derivadas solo donde son reales** — deuda/capex/FCF bloqueados con motivo, nunca aproximados; división por cero y denominador negativo manejados sin excepción y sin ocultar el problema.
6. **Validación con evidencia real, no solo con fixtures** — 16/16 ecuaciones contables comprobables pasaron (tolerancia del 2%, nunca igualdad exacta); 1 anomalía económica real detectada, investigada y marcada, no descartada.
7. **Umbrales de promoción definidos ANTES de calcular ningún score** (`PROMOTABLE ≥ 0,75`) — **50/50 activos alcanzan `PROMOTABLE`** con evidencia medida, no proyectada.
8. **QA offline completa e integrada** — 44 casos individuales en 6 módulos, un único punto de entrada, sin romper ninguna suite anterior (los mismos 3 fallos preexistentes de fase 4, sin regresiones nuevas).
9. **Seguridad y licencias respetadas** — sin cuentas nuevas, sin credenciales expuestas, sin datos con valor real comiteados (solo informes agregados).

**Esta decisión NO implica:**
- Que el universo de fundamentales cubra más del 0,24% del censo canónico — sigue siendo exactamente los mismos 50 activos de la fase 4.
- Que las métricas de deuda, capex o flujo de caja libre estén disponibles — están estructuralmente bloqueadas en ambas fuentes aprobadas.
- Ninguna autorización automática para la fase 6 — ver J7.
- Ningún juicio de valor sobre si estos 50 activos son buenas inversiones — el score de calidad mide fiabilidad e integridad de los datos, no mérito de inversión.

## J7 — Autorización posterior

Aunque la fase 5 se cierra con la decisión anterior:

- **FASE 6 BLOQUEADA: la fase 5 no permite promoción.**
- **No se ha generado ningún score de inversión, ranking ni recomendación.**
- **No se ha modificado la interfaz más allá de las pruebas internas ya descritas.**
- **No se ha ampliado el universo de activos ni de mercados.**

El paso a la fase 6 requiere una autorización nueva y explícita del usuario, después de leer este informe.

## Seguridad y alcance

- Ninguna cuenta nueva creada; la única credencial usada (J-Quants) ya existía de la fase 4, nunca impresa ni comiteada — verificado en cada bloque con un escaneo de secretos sobre el diff staged.
- Cero valores reales de fundamentales comiteados: los 5 ficheros/directorios con datos reales (crudos, normalizados, derivados, detalle de validación) permanecen en `.gitignore`, añadidos antes de crearse en cada bloque. Solo informes agregados (recuentos, sin cifras individuales) se publican.
- Los 6 archivos locales protegidos permanecen intactos y sin versionar, verificados explícitamente antes de cada uno de los 10 commits de esta fase (A–I, más este cierre J).
- `production_scoring_authorized: false`, `allow_ranking: false` en todos los informes generados.

## Estado del roadmap

- **Fase 5: cerrada** con la decisión `COMPLETED_PROMOTABLE`.
- Progreso global: 4/8 fases cerradas (fase 4) + fase 5 cerrada = **5/8 fases cerradas**.
- Interfaz estable: `v2.32F` (sin cambios).
- Pipeline de precios vigente: `v2.33R — Fase 4 Final Gate` (sin cambios).
- Pipeline de fundamentales vigente: `v2.34J — Fase 5 Final Gate`.
- **Fase 6: no iniciada, no autorizada.** Requiere decisión explícita nueva del usuario tras leer este informe.
