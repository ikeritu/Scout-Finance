# Scout Finance v2.34I — integración de QA offline y verificación cruzada (Bloque I, fase 5)

Fecha: 2026-08-31. Alcance: **integrar en un único punto de entrada las suites offline ya construidas en los Bloques C-H, y ejecutar la lista de verificación completa del encargo** (compilación, pruebas de fase 5, pruebas relevantes ya existentes, `git diff --check`, validación de `.gitignore`, búsqueda de secretos, revisión de ficheros grandes, comprobación de determinismo). Sin red, sin credenciales reales.

## Por qué este bloque es principalmente integración, no ficheros nuevos de prueba

Este proyecto ya sigue, desde la fase 4, la disciplina de escribir pruebas offline como parte de cada bloque (nunca al final): cada uno de los Bloques C-H cerró con su propia suite `qa_fundamental_*_v2_34X.py`, verificada contra `schema.validate_record()` real y, cuando aplicaba, contra los datos reales adquiridos. El resultado es que la cobertura exigida explícitamente por el Bloque I ya existe, distribuida:

| Requisito del Bloque I | Dónde ya está cubierto |
|---|---|
| Esquema | `qa_fundamental_schema_v2_34c.py` (9 casos) |
| Ambos normalizadores | `qa_fundamental_normalizers_v2_34f.py` (7 casos) |
| Escalas/monedas/periodos | `qa_fundamental_normalizers_v2_34f.py` (conversión miles→unidades, derivación de `period_end`) |
| Ecuación contable | `qa_fundamental_validators_v2_34h.py` (tolerancia, `not_applicable` vs `failed`) |
| FCF, deuda neta | `qa_fundamental_derived_metrics_v2_34g.py` (bloqueo explícito, nunca silencioso) |
| Crecimiento con bases positivas y negativas | `qa_fundamental_derived_metrics_v2_34g.py` |
| División por cero | `qa_fundamental_derived_metrics_v2_34g.py`, `qa_fundamental_validators_v2_34h.py` |
| Identidad | `qa_fundamental_acquisition_v2_34d.py` (`IDENTITY_MISMATCH`) |
| Escrituras atómicas, reanudabilidad | `qa_fundamental_acquisition_v2_34d.py` |
| Bloqueo por defecto de `--execute` | `qa_fundamental_acquisition_v2_34d.py` |
| Redacción de credenciales | `qa_fundamental_acquisition_v2_34d.py` (nunca aparece `FIXTURE_KEY` ni una URL completa en ningún informe) |
| Fallos HTTP/vacíos/schema-mismatch | `qa_fundamental_acquisition_v2_34d.py` |
| Manifiesto de cobertura, determinismo | Los 4 scripts `build_*_v2_34{e,f,g,h}.py` — cada uno verificado manualmente con dos ejecuciones consecutivas produciendo un JSON byte-idéntico |

**Limitación documentada, no ausencia silenciosa**: `sign_convention` en ambos normalizadores es siempre `"natural"` porque ninguna de las dos fuentes aprobadas expone una convención de signo invertida en los datos reales observados; no existe, por tanto, ninguna ruta de código de "volteo de signo" que probar. Si en el futuro se incorporase una fuente que reporte gastos en negativo, esa ruta necesitará su propia prueba entonces.

## Lo que este bloque añade de verdad

1. **`tests/qa_fundamentals_phase5_full_suite_v2_34i.py`** — un único punto de entrada que importa y ejecuta el `main()` real de cada uno de los 6 módulos anteriores (sin duplicar su lógica), y reporta cuáles pasaron. Resultado real: **6/6 módulos, 44 casos individuales, todos en verde**.
2. **Confirmación explícita del patrón de integración con pytest**: `pytest.ini` restringe el descubrimiento a `test_*.py` (`testpaths = tests`, `python_files = test_*.py`); los ficheros `qa_*.py` de este proyecto (fase 4 y fase 5 por igual) se ejecutan siempre como scripts independientes, nunca vía `pytest -q`, exactamente el mismo patrón que ya usaban las 18 suites `qa_*.py` de la fase 4. No se ha roto ni modificado esta convención.
3. **Ejecución completa de la lista de verificación del Bloque I** (evidencia abajo).

## Evidencia real de la lista de verificación

```
# Compilación de todos los ficheros Python de la fase 5
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/*.py \
  scripts/download_jquants_fundamentals_v2_34d.py scripts/download_twse_mops_fundamentals_v2_34d.py \
  scripts/build_fundamentals_acquisition_report_v2_34e.py scripts/build_fundamental_dataset_v2_34f.py \
  scripts/build_fundamental_derived_metrics_v2_34g.py scripts/build_fundamental_validation_v2_34h.py \
  scripts/prepare_fundamental_universe_v2_34a.py tests/qa_fundamental_*.py tests/qa_fundamentals_*.py
COMPILE OK

# Suite offline integrada
.venv/Scripts/python.exe tests/qa_fundamentals_phase5_full_suite_v2_34i.py
6/6 modules passed
PASS: v2.34I-phase5-full-offline-qa-suite/all-blocks-c-through-h/no-network/no-real-credentials

# Suite de pytest completa del proyecto (fase 4 + fase 5 + todo lo anterior)
.venv/Scripts/python.exe -m pytest -q
# 3 fallos, los MISMOS 3 ya conocidos y documentados desde antes de la fase 5
# (tests/test_expanded_universe_post_closure_v2_14j.py) -- ninguna regresión nueva

# git diff --check (sin problemas de espacio en blanco/EOF)
git diff --check
(sin salida)

# Búsqueda de secretos restringida a los ficheros de fase 5 versionados
git grep -inE "api[_-]?key\s*=\s*['\"a-zA-Z0-9]|x-api-key['\"]:\s*['\"][a-zA-Z0-9]|refresh_token\s*=\s*['\"][a-zA-Z0-9]" -- \
  'scripts/*fundamental*' 'tests/qa_fundamental*' 'config/fundamental*' 'schemas/*'
(sin coincidencias inesperadas -- solo el nombre de la variable de entorno y el fixture de pruebas)

# Revisión de ficheros grandes versionados bajo rutas de fase 5
# el más grande es fundamental_coverage_manifest_v2_34f.json, 36 KB -- ningún dato en bruto ni fila con valores reales
```

## Confirmación de que los datos con valor real siguen fuera de git

```
git status --porcelain=v1 --ignored=matching | grep v2_34
!! outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/jquants_fundamentals_raw_v2_34d/
!! outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/twse_mops_raw_v2_34d/
!! outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl
!! outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_records_v2_34g.jsonl
!! outputs/full_universe_source_acquisition/v2_34h_validation/validation_detail_v2_34h.json
```

Los 5 ficheros/directorios con valores reales de fundamentales están correctamente ignorados, tal como se declaró proactivamente en `.gitignore` antes de crear cada uno (Bloques D, F, G, H).

## Seguridad y alcance

- Sin red, sin credenciales reales en ningún módulo de este bloque.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED`.** La suite offline de la fase 5 (44 casos individuales + 1 orquestador) está completa, integrada y verificada sin romper ninguna suite anterior. El Bloque J (informes, documentación y decisión final) puede proceder.
