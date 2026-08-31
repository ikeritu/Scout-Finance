# Scout Finance v2.34H — validación y score de calidad (Bloque H, fase 5)

Fecha: 2026-08-31. Alcance: **validar el conjunto real de 13.917 registros** (10.315 normalizados del Bloque F + 3.602 derivados del Bloque G) mediante ecuaciones contables, consistencia temporal y sanidad económica, y calcular un **score de calidad de los datos** (nunca de inversión) por activo. Sin red, sin credenciales. Los umbrales de promoción se definen en el código **antes** de calcular ningún score (`PROMOTION_THRESHOLDS` al principio de `scripts/build_fundamental_validation_v2_34h.py`), tal como exige el encargo.

## H.1 — Validación de esquema

Los 13.917 registros (normalizados + derivados) se revalidan contra `schema.validate_record()` — **0 inválidos**, consistente con los Bloques F y G que ya lo habían verificado por separado.

## H.2 — Ecuaciones contables (con tolerancia, nunca igualdad exacta)

Tolerancia relativa del 2% (`RELATIVE_TOLERANCE = 0.02`), justificada porque las cifras proceden de redondeos/conversiones de escala independientes del proveedor, no porque se esperen discrepancias reales.

| Ecuación | Aplicable | Resultado real |
|---|---|---|
| `activo ≈ pasivo + patrimonio` | **Solo TWSE** — JPX no reporta `total_liabilities` de forma independiente; calcularlo como `activo − patrimonio` y luego "comprobar" la misma ecuación sería una tautología, no una validación real, así que nunca se intenta para JPX | **8/8 pasadas (100%)**, 640 `not_applicable` (JPX) |
| `beneficio bruto ≈ ingresos − coste de ventas` | Solo TWSE (`gross_profit`/`cost_of_sales` no existen en J-Quants `/fins/summary`) | **8/8 pasadas (100%)**, 640 `not_applicable` (JPX) |

Ambas ecuaciones pasan al 100% de los casos donde son comprobables — evidencia directa de que la conversión de escala del Bloque F (miles → unidades TWD) es internamente consistente.

## H.3 — Consistencia temporal

`period_start` ≤ `period_end`, `fiscal_quarter` ∈ {1,2,3,4,None}. **Resultado real: 0 problemas** sobre los 10.315 registros normalizados.

## H.4 — Sanidad económica (marcar, nunca corregir en silencio)

Rangos de plausibilidad deliberadamente laxos (existen para atrapar defectos claros de escala/normalización, no para cuestionar un mal trimestre real). **1 caso real marcado**: `P020` (精金科技股份有限公司, TWSE, Q2 2026) — `net_margin = 316.5%` (`net_income` = 629.799.000 TWD frente a `revenue` = 198.992.000 TWD). Verificado manualmente contra los campos crudos del proveedor (`本期淨利（淨損）` y `營業收入`): la cifra es exactamente la que reporta MOPS, no un error de nuestra normalización. Queda **marcada, no corregida ni descartada** — es compatible con una ganancia extraordinaria (venta de activo, resultado por método de participación, etc.) que este proyecto no tiene forma de confirmar sin acceso al informe completo de la empresa, fuera del alcance de la fase 5.

## H.5 — Score de calidad de los datos (7 dimensiones, ningún score de inversión)

| Dimensión | Cómo se calcula | Nota |
|---|---|---|
| `identity` | 1.0 fijo — los 50 activos ya son `identity_verified` desde el Bloque A; no se recalcula | |
| `provenance` | Fracción de registros con `normalization_status="normalized"` | |
| `completeness` | Fracción de 5 métricas núcleo (`revenue`, `operating_income`, `net_income`, `total_assets`, `total_equity`) con valor real | |
| `continuity` | Periodos reales con datos ÷ objetivo por proveedor (JPX: 8: ~2 años trimestrales+FY ya confirmados; TWSE: 1, su propio límite estructural ya aceptado en el Bloque B — nunca se penaliza a TWSE por una limitación que este proyecto ya aprobó al aceptar la fuente) | |
| `coherence` | Fracción de ecuaciones contables comprobables que pasaron; **`null`, nunca 0 ni 1, cuando no hay ninguna comprobable** (JPX) | Ver H.6 |
| `comparability` | Nº de métricas del catálogo (29) con valor real ÷ 29 | Estructural por fuente, no varía dentro del mismo proveedor |
| `freshness` | Decaimiento lineal desde el `period_end` más reciente sobre una ventana de 2 años (convención definida, no un estándar externo) | |

`composite_quality_score` = media de las dimensiones con valor no nulo (excluye `coherence` cuando es `null`, en vez de tratarlo como 0).

## H.6 — Decisión de diseño: `coherence=null` no es lo mismo que "falló"

Durante la construcción de este bloque se decidió explícitamente que un activo sin ninguna ecuación comprobable (todo JPX, por la limitación de fuente ya conocida) **no debe verse penalizado como si sus cuentas fueran incoherentes** — sería castigar una limitación de la fuente, no un problema real de los datos. Se implementó y probó (`test_coherence_is_null_not_zero_when_no_equations_attempted`) que el score compuesto excluye la dimensión `null` del promedio en vez de tratarla como 0.

## Umbrales de promoción (definidos antes de calcular ningún score)

```python
PROMOTION_THRESHOLDS = {"PROMOTABLE": 0.75, "PARTIAL": 0.50}  # NOT_PROMOTABLE por debajo de 0.50
```

## Resultado real (evidencia, `fundamental_validation_report_v2_34h.json`)

- **13.917 registros validados, 0 inválidos contra el esquema.**
- Ecuaciones contables: **16/16 pasadas (100%)** de las comprobables (8 balance + 8 margen bruto, todas TWSE); 1.280 `not_applicable` documentadas con motivo (JPX, componentes no reportados independientemente).
- **0 problemas temporales.**
- **1 bandera de sanidad económica** (`net_margin_outside_plausible_range`, `P020`), investigada y documentada, no corregida.
- **50/50 activos en el nivel `PROMOTABLE`** (score compuesto entre 0.87 y 0.90 según muestra), impulsado principalmente por `identity`/`provenance`/`completeness`/`continuity` perfectos o casi perfectos; la dimensión que más baja el score en ambos mercados es `comparability` (JPX ~55%, TWSE ~38% de las 29 métricas del catálogo) — refleja honestamente la asimetría de cobertura ya documentada desde v2.34B, no un defecto de calidad de los datos obtenidos.

## Pruebas offline

`tests/qa_fundamental_validators_v2_34h.py` — 11 casos, sin red, sin datos reales:

1-2. Ecuación de balance pasa dentro de tolerancia (no exacta) y falla fuera de tolerancia.
3. Ecuación de balance `not_applicable` sin `total_liabilities` independiente (caso tipo JPX).
4. Ecuación de margen bruto solo se comprueba con los tres componentes presentes.
5-7. Consistencia temporal: fecha de inicio posterior a fin marcada, trimestre fuera de rango marcado, datos limpios no generan ninguna bandera.
8-9. Activo total negativo marcado; margen implausible marcado y margen plausible NO marcado (falsos positivos evitados).
10. Score de calidad: dimensiones correctas, coherencia calculada cuando hay ecuaciones comprobables.
11. `coherence=null` (nunca 0 ni 1) cuando no hay ninguna ecuación comprobable, y el compuesto excluye correctamente esa dimensión del promedio.

```
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/validators.py scripts/build_fundamental_validation_v2_34h.py tests/qa_fundamental_validators_v2_34h.py
.venv/Scripts/python.exe tests/qa_fundamental_validators_v2_34h.py
PASS: v2.34H-fundamental-validators/tolerance-not-exact-equality/not-applicable-vs-failed/sanity-flags/quality-score/null-dimension-handling
.venv/Scripts/python.exe scripts/build_fundamental_validation_v2_34h.py
{"status": "COMPLETED", "total_records_validated": 13917, "schema_invalid_records_count": 0, "assets_by_promotion_tier": {"PROMOTABLE": 50}}
```

Verificado además: dos ejecuciones consecutivas producen un informe agregado byte-idéntico.

## Seguridad y alcance

- El detalle con valores reales (`validation_detail_v2_34h.json`, incluye la magnitud de la bandera de sanidad de P020) queda **fuera de git** (añadido a `.gitignore` antes de crearse). Solo el informe agregado (`fundamental_validation_report_v2_34h.json`: recuentos, umbrales, scores por activo redondeados, sin magnitudes de banderas individuales) se publica.
- Sin red, sin credenciales en este bloque.
- `production_scoring_authorized: false`, `allow_ranking: false` — el score de calidad de datos aquí calculado **no es** un score de inversión ni una recomendación; no ordena ni puntúa activos por atractivo.

**Estado del bloque: `COMPLETED`.** Los 50 activos alcanzan el nivel `PROMOTABLE` de calidad de datos según los umbrales definidos; esta evidencia alimenta la decisión final del Bloque J, que sigue siendo la única autorizada a declarar el cierre formal de la fase 5.
