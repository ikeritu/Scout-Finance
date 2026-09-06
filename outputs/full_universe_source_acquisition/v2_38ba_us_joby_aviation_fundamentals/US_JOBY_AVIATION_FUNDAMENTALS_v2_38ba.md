# v2.38BA — Joby Aviation: fundamentales reales de la SEC, la primera empresa 556

Fecha: 2026-09-06. Alcance: extraer fundamentales reales para Joby Aviation, Inc. (`asset_id U04441`, ticker `JOBY`, NYSE, CIK `0001819848`) — la empresa real que `v2.38AZ` descubrió detrás del activo Xetra `8TQ` que `v2.38AV` había clasificado como "Islas Caimán" a partir solo del prefijo de su ISIN.

## Por qué esta empresa, y por qué no tocar el pipeline fijo de 555

`v2.38D` ya había resuelto el CIK de Joby Aviation (`US_SEC_CIK_RESOLVED`) desde que se construyó el censo de identidad de EE. UU. — nunca fue un problema de identidad. El motivo por el que nunca se procesaron sus fundamentales reales es simplemente que nunca formó parte del lote de 555 empresas ya extraídas por el pipeline `v2.38E→F→G`.

Ese pipeline tiene contratos de conteo fijo (`config/us_sec_foundation_contract_v1.json`, `config/us_sec_fundamental_normalization_contract_v1.json`) que bloquean la ejecución (`BLOCKED`) si el número de filas de entrada no coincide exactamente con lo esperado — una salvaguarda deliberada contra cambios silenciosos en el censo. Añadir una empresa más ahí exigiría tocar esos contratos, un cambio de mayor alcance del que esta tarea justifica. En su lugar, este bloque **reutiliza sin modificar** las dos funciones puras ya probadas en las 555 empresas:

- `normalize_us_sec_fundamentals_v2_38f.normalize_company()` — misma extracción de conceptos US-GAAP, misma lógica de rechazo fail-closed.
- `build_us_sec_fundamental_features_v2_38g.build_company()` — mismo cálculo de crecimiento interanual, márgenes, ratios y banderas de calidad.

Cero lógica nueva de extracción o de features — solo aplicada a una empresa más.

## Ejecución real

Con la credencial `SCOUT_FINANCE_SEC_USER_AGENT` (variable de entorno, misma ya usada para las 555 empresas, provista por el usuario), se descargó primero, de forma acotada a este único activo:

```
python scripts/run_us_sec_enrichment_v2_38e.py --asset-id U04441 --execute
→ {"collected": 1, "companyfacts_available": 1, "failed": 0, "network_calls": 2, "status": "COMPLETED"}
```

Y después, sin red, la extracción de fundamentales:

```
python scripts/build_us_joby_aviation_fundamentals_v2_38ba.py
```

## Resultado real

**Los 9 conceptos contables básicos están presentes** (`NORMALIZED_READY`): ingresos, beneficio neto, activo, pasivo, patrimonio neto, flujo de caja operativo, capex, BPA básico y diluido — 558 registros normalizados reales, 6 ejercicios fiscales, 139 registros trimestrales.

**17/20 features calculadas** (`FEATURES_READY`), ejercicio de referencia 2025 (periodo cerrado 2026-06-30, presentado 2026-08-06):

| Feature | Valor real |
|---|---:|
| Crecimiento de ingresos interanual | +391,8% |
| Crecimiento de activo interanual | +49,2% |
| Crecimiento de patrimonio neto interanual | +54,5% |
| Margen neto | -1.740% |
| Flujo de caja libre | -563.811.000 $ |
| Patrimonio/Activo | 0,79 |
| `positive_fcf_flag` | falso |
| `balance_strength_flag` | verdadero |

**3 features quedan honestamente sin calcular, nunca inventadas**: `net_income_yoy_growth` y `operating_cash_flow_yoy_growth` (el beneficio neto y el flujo de caja operativo del ejercicio anterior fueron negativos — la regla ya establecida en `yoy()`, `previous <= 0 → None`, se aplica sin excepción) y `cash_conversion_ratio` (mismo motivo, denominador negativo).

**Lectura honesta de las cifras**: Joby Aviation es una empresa de aviación eléctrica (eVTOL) en fase preoperativa/de escalado, con ingresos todavía muy pequeños y pérdidas netas grandes financiadas con capital propio (patrimonio neto en fuerte crecimiento, `balance_strength_flag=true` pese a las pérdidas) — un patrón real y coherente con lo que es públicamente conocido de la empresa, no una anomalía del cálculo.

## Qué NO hace este bloque

No modifica el fichero fijo de 555 empresas (`us_sec_fundamental_features_v2_38g.csv`) ni sus contratos de conteo. No reconstruye `v2.38AL` (matriz de cobertura global) ni `v2.38AM` (contexto geopolítico) — haría falta decidir explícitamente si Joby Aviation entra en esas reconstrucciones, dado que su verdadero país es EE. UU., no Islas Caimán como el censo original sugería para el activo Xetra. No calcula ningún score, ranking ni recomendación.

## Pruebas offline

`tests/qa_us_joby_aviation_fundamentals_v2_38ba.py` — 4 casos: bloqueo real cuando falta la caché de la SEC, features reales con datos de forma realista de 2 años (crecimiento de ingresos calculado, crecimiento de beneficio neto correctamente ausente por denominador negativo), verificación de que el bloque reutiliza las funciones reales de v2.38F/G en vez de reimplementarlas, y un solo ejercicio fiscal produciendo `FEATURES_PARTIAL` sin inventar ningún crecimiento interanual.

```
.venv/Scripts/python.exe tests/qa_us_joby_aviation_fundamentals_v2_38ba.py
PASS: v2.38BA-us-joby-aviation-fundamentals/blocked-no-cache/two-year-features/reuses-v2.38f-g/single-year-insufficient/no-network
```

## Seguridad y alcance

Red real usada solo para el fetch acotado a este activo (2 llamadas: `submissions` + `companyfacts`), vía la credencial ya provista por el usuario, nunca vista por este proyecto. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_US_JOBY_AVIATION_FUNDAMENTALS`.** Primera empresa fuera del lote original de 555 con fundamentales reales de la SEC, extraída reutilizando el 100% de la metodología ya validada. Sube el recuento real de empresas de EE. UU. con fundamentales reales a **556**.
