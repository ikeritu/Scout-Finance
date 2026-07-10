# Auditoría técnica Scout Finance

Fecha: 2026-07-10
Alcance: repositorio completo, solo lectura (sin modificaciones).
Commit auditado: `5a4e3f0` — Add v2.14G Deutsche Boerse Xetra closure report (rama `main`, 0 commits de diferencia con `origin/main`).

## 1. Resumen ejecutivo

Estado general: el proyecto tiene dos líneas de trabajo que han divergido en su documentación. La app Streamlit (`app.py`, `README.md`, `VERSION.md`, `CHANGELOG.md`) sigue documentada como `v1.1C — MVP Final Freeze`, mientras que el histórico de commits real llega hasta `v2.14G` de un pipeline de adquisición y expansión de universo de tickers (CBOE, SEC, NASDAQ, OTC, LSE, NYSE, HKEX, JPX, Xetra) que no está descrito en ningún documento de nivel superior. El cierre v2.14G en sí se verificó de forma independiente (recuento de filas, claves duplicadas exchange+ticker) y **las cifras del informe de cierre son correctas**; no se ha encontrado motivo para reabrirlo.

Riesgos principales:
- Un candado de Git obsoleto (`index.lock`) impide actualmente `git add`/`git commit` en el repositorio.
- El árbol de trabajo tiene 952 archivos marcados como modificados por un problema de fin de línea (CRLF/LF), no por cambios de contenido reales — riesgo de diffs ruidosos y de mezclar cambios reales con ruido de formato en un futuro commit.
- La documentación de versión/estado (README, VERSION, CHANGELOG) no refleja el pipeline v2.x y puede inducir a decisiones sobre una base obsoleta.
- El pipeline de expansión de universo (~223 scripts) no tiene ningún test automatizado; toda validación es manual vía scripts `check_*`/`validation_*`.

Principales oportunidades: fijar versiones de dependencias, normalizar el esquema del dataset expandido (columnas `ticker`/`symbol` y `company_name`/`security_name` duplicadas y dispersas por proveedor), consolidar documentación de arquitectura, y planificar la migración a Git LFS para los volcados crudos de proveedores (~150 MB y creciendo).

Nivel de confianza de la auditoría: alto para los hallazgos de Git, estructura, documentación y verificación aritmética de los datos del cierre v2.14G (todo comprobado con comandos reproducibles). Medio para el análisis de scripts (223 scripts en `scripts/` no se revisaron uno a uno, solo patrones y muestras representativas). No se pudieron ejecutar los tests de `pytest` en este entorno de auditoría por falta de acceso a red para instalar dependencias — queda marcado como pendiente de verificación.

## 2. Estado Git y estructura

- Rama actual: `main`.
- Último commit: `5a4e3f0` "Add v2.14G Deutsche Boerse Xetra closure report" (2026-07-10 00:58:25 +0200).
- Commits recientes: siguen el patrón `vX.YZ` por fase (A=ruta de proveedor, B=plan, C=adquisición cruda, D=validación, E=rebuild, F=validación expandida, G=cierre), consistente entre HKEX (v2.12), JPX (v2.13) y Xetra (v2.14).
- Diferencia con `origin/main`: 0 commits adelante / 0 atrás → el historial de commits está sincronizado con el remoto.
- Árbol de trabajo: **952 archivos con cambios sin commitear** (`git status --porcelain` → 952 líneas `M`), más 1 archivo no versionado: `Auditoria_Scout_Finance.docx`.
- Archivo de bloqueo `.git/index.lock` presente y no eliminable por el proceso actual (`Operation not permitted` al listar, `File exists` al intentar `git add`).
- Estructura: repo monolítico con `app.py` (7.961 líneas), `src/` (118 scripts), `scripts/` (223 scripts), `data/` (raw, stages, universe, cache, real), `outputs/` (analyses, audit, full_universe_source_acquisition ≈150 MB, scale_tests, scouting…), `docs/` (phase4–9, technical vacío, v1), `releases/` (freezes + zips), `templates/`, `schemas/`, `prompts/`, `tests/` (4 archivos).
- Observación estructural: no existe `.github/` ni ningún otro pipeline de CI. Toda ejecución de tests/checks es manual.

## 3. Hallazgos críticos y altos

| ID | Severidad | Área | Evidencia | Riesgo | Acción recomendada |
|---|---|---|---|---|---|
| C1 | CRÍTICO | automatización/bug | `.git/index.lock` existente (0 bytes, timestamp 2026-07-10 01:26). `git add --dry-run app.py` falla con `fatal: Unable to create '.git/index.lock': File exists`. `git status` emite además `warning: unable to unlink '.git/index.lock': Operation not permitted` | Bloquea cualquier `git add`/`commit` nuevo; si alguien fuerza el borrado sin confirmar que no hay un proceso git activo, puede corromper un commit en curso | Verificar que no hay ningún proceso `git` en ejecución (Task Manager en Windows) y entonces eliminar manualmente `.git/index.lock`. Esfuerzo bajo. **Acción inmediata**, pero fuera del alcance de esta auditoría de solo lectura — requiere confirmación explícita antes de tocarlo |
| A1 | ALTO | bug/Windows-PowerShell | `git diff --stat app.py` → 7.961 inserciones / 7.961 eliminaciones; comparación byte a byte (`xxd`) confirma que el único cambio es `\n`→`\r\n`. Se repite en los 952 archivos modificados (CSV, MD, JSON, PY). No existe `.gitattributes` en el repo | Cualquier commit futuro en Windows puede arrastrar cientos de archivos con "ruido" de fin de línea mezclado con cambios reales, dificultando el `code review` y la trazabilidad exigida por las prioridades del proyecto | Añadir `.gitattributes` (p. ej. `* text=auto eol=lf` o la convención que se decida) y renormalizar el repo una sola vez, de forma controlada y documentada, sin mezclarlo con cambios de datos. Esfuerzo medio |
| A2 | ALTO | documentación | `VERSION.md` y `README.md` declaran versión actual `v1.1C — MVP Final Freeze`; `CHANGELOG.md` no menciona nada posterior a v1.1C. El `git log` real llega a `v2.14G` (más de 190 commits de fases v2.x: rutas de proveedor, adquisición, validación, rebuild, cierre) | Cualquier persona (o asistente) que confíe en README/VERSION/CHANGELOG para entender "en qué punto está el proyecto" trabajará sobre una imagen desactualizada en ~2 versiones mayores | Actualizar VERSION.md/README.md/CHANGELOG.md para reflejar el estado real, o documentar explícitamente que son dos líneas de trabajo independientes (app MVP congelada en v1.1C vs. pipeline de datos en v2.x). Esfuerzo medio |
| A3 | ALTO | automatización/datos | `tests/` solo contiene `test_app_static_integrity.py`, `test_combined_scoring_v1.py`, `test_fundamentals_input.py` (196 líneas totales); `grep` de "expanded_universe\|xetra\|hkex\|jpx\|cboe" en `tests/` no arroja ningún resultado. Los ~223 scripts de `scripts/` (todo el pipeline v2.x de expansión de universo) se validan solo con scripts `check_*`/`*_validation_*` ejecutados manualmente, sin framework de tests ni CI | Regresiones en el pipeline de expansión de universo no quedan cubiertas por ninguna prueba reproducible automatizada; el único checkpoint de calidad es la ejecución manual y disciplinada de los scripts de validación de cada fase | Añadir al menos un test ligero de "integridad post-cierre" (recuento de filas, claves duplicadas exchange+ticker, columnas obligatorias no vacías) ejecutable con `pytest` sobre el dataset expandido vigente. Esfuerzo medio |
| A4 | ALTO | datos/arquitectura | El dataset "expanded_universe" cambia de ubicación entre fases: versiones v2_4b/v2_7b/v2_8e viven en `data/raw/expanded_universe/`; desde v2_11e (CBOE Europe) en adelante (v2_12e HKEX, v2_13e JPX, v2_14e Xetra) solo existen en `outputs/full_universe_source_acquisition/`. `data/raw/expanded_universe/` no se actualizó desde v2_8e (3,3 MB, 9.200 filas) | Riesgo de que un script o una persona nueva lea `data/raw/expanded_universe/expanded_universe_v2_8e.csv` creyendo que es la versión vigente, cuando la real (38.287 filas) está en `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv` | Documentar explícitamente en el README/roadmap cuál es la ruta canónica vigente tras cada cierre, o mover siempre el "latest" también a `data/raw/expanded_universe/`. Esfuerzo bajo-medio |

## 4. Hallazgos medios y bajos

| ID | Severidad | Área | Evidencia | Riesgo | Acción recomendada |
|---|---|---|---|---|---|
| M1 | MEDIO | datos/dependencias | `requirements.txt`: `pandas`, `numpy`, `python-dotenv`, `streamlit`, `yfinance`, `openai`, `plotly`, `matplotlib>=3.8` — ninguna versión fijada salvo el mínimo de matplotlib | `yfinance` en particular cambia su API con frecuencia sin aviso formal; una actualización silenciosa de dependencias podría alterar datos de mercado sin que se note | Fijar versiones exactas (o rango acotado) en `requirements.txt`; considerar `requirements.lock`. Esfuerzo bajo |
| M2 | MEDIO | arquitectura | `check_phase7a5_2_institutional_dashboard.py` y `hotfix_phase7a5_2_dashboard.py` existen de forma idéntica (diff vacío confirmado) tanto en la raíz del repo como en `scripts/` | Mantenimiento duplicado; riesgo de editar una copia y no la otra | Eliminar la copia de la raíz (dejar solo en `scripts/`) tras confirmar que nada las referencia por esa ruta. Esfuerzo bajo |
| M3 | MEDIO | arquitectura | `app.py` (7.961 líneas) construido por acumulación secuencial de parches "empaquetados" (comentarios de cabecera desde v1.5D2 hasta v1.6D3B). Auditorías internas ya existentes (`outputs/audit/app_dead_code_audit_v1_6d1.md`, `outputs/audit/legacy_helper_usage_v1_6d3.md`) documentan funciones sin uso (`_render_login`, `_render_faq_main`, 12 "no-call candidates" de helpers `_sf15x`) | Deuda técnica ya identificada internamente pero no resuelta; archivo de este tamaño incrementa el riesgo de error en futuras modificaciones | Planificar limpieza incremental basada en las auditorías ya existentes, sin tocar lógica activa ni romper las pestañas ya cerradas. Esfuerzo medio-alto (por volumen) |
| M4 | MEDIO | documentación | Mojibake recurrente en documentos autogenerados: `outputs/audit/legacy_helper_usage_v1_6d3.md` → "Scout Finance ? v1.6D3A..."; `data/raw/expanded_universe/README_v2_3e.md` → "Scout Finance ? Expanded Universe..."; `README.md` línea final corrupta: `#   S c o u t - F i n a n c e` | Indica un problema sistemático de encoding (probable escritura sin `encoding='utf-8'` explícito) que puede reaparecer en futuros informes generados por script | Forzar `encoding='utf-8'` en toda escritura de texto/Markdown en los scripts generadores de reportes; corregir los 3 archivos afectados. Esfuerzo bajo |
| M5 | MEDIO | datos | En `expanded_universe_v2_14e.csv` (38.287 filas) las columnas `symbol` y `security_name` solo están pobladas para las 1.424 filas de Xetra (el resto, 36.863 filas = exactamente el baseline previo, las tiene vacías); `ticker`/`company_name` sí están pobladas en todas. Ambas parejas de columnas son redundantes entre sí para las filas de Xetra | Si en el futuro algún script de scoring o filtrado consultara `symbol` en vez de `ticker` sin saberlo, perdería silenciosamente el 96% de las filas. Hoy no hay ningún consumidor de `symbol` en `app.py`/`src/` (verificado por grep), por lo que el riesgo es preventivo, no activo | Antes de integrar el universo expandido en el pipeline de scoring de la app, normalizar el esquema (una sola columna canónica por concepto; campos crudos específicos de proveedor en columnas aparte claramente prefijadas). Esfuerzo medio |
| M6 | MEDIO | escalabilidad | `outputs/full_universe_source_acquisition/` pesa ~150 MB (incluye HTML/CSV/ZIP crudos de proveedores versionados directamente en git); repo total 770 MB en disco, `.git` 25 MB (bien comprimido por delta entre versiones similares, sin corrupción — `git fsck --full` y `git count-objects -v` limpios) | A medida que se añadan más exchanges hacia 50k/full source, el repo seguirá creciendo linealmente; clonar/operar sobre él será cada vez más lento | Evaluar Git LFS para volcados crudos >1 MB, o mantenerlos fuera de git con un manifiesto de hashes/checksums como evidencia. Esfuerzo medio, no urgente |
| B1 | BAJO | bug | Varios `except Exception: pass` revisados (`src/clean_universe_institutional.py:115`, `src/enrich_market_data_yfinance.py:85` y `189`, `src/data_quality.py:70`, `src/export.py:152`, `src/filters.py:58`) — todos son coerciones defensivas de tipo (`pd.isna` sobre valores no escalares), no ocultan errores de negocio graves en las muestras revisadas | Bajo, pero dificulta detectar pérdida silenciosa de datos si el patrón se reutiliza en contextos menos triviales | Añadir log en modo debug en estos puntos si se sospecha pérdida de datos en el futuro. Esfuerzo bajo |
| B2 | BAJO/OPORTUNIDAD | arquitectura | `scripts/` tiene 223 archivos + `src/` 118 = 341 scripts Python, mayoritariamente de una sola fase (`check_`, `apply_`, `rollback_`, `hotfix_`). Es coherente con la metodología aditiva conservadora del proyecto (no reescribir, no romper cierres), pero dificulta la navegación | Bajo impacto funcional, alto impacto en mantenibilidad a largo plazo | Archivar scripts de fases ya cerradas y congeladas (p. ej. anteriores a v2.0) en `scripts/archive/` sin eliminarlos. Esfuerzo bajo |
| B3 | BAJO | documentación | `docs/technical/` existe como carpeta pero está completamente vacía (`ls -la` → 0 archivos) | No hay documentación de arquitectura consolidada del pipeline v2.x (extracción/normalización/validación/reporting) | Documento breve de arquitectura enlazando los scripts de cada fase. Esfuerzo bajo-medio |
| B4 | BAJO/pendiente de verificar | datos | `data/universe/global_universe.csv` tiene BOM UTF-8 al inicio de la cabecera (`﻿ticker`); no se verificó si esto afecta a algún script que compare el nombre de columna de forma estricta | Bajo, pandas suele manejar BOM automáticamente, pero no se confirmó en todos los puntos de lectura | Verificar lectura de este archivo con `encoding='utf-8-sig'` explícito si se detecta algún problema real; por ahora, pendiente de verificación, no se detectó fallo activo |

## 5. Inconsistencias de datos o documentación

- **VERSION.md / README.md / CHANGELOG.md vs. `git log` real**: documentación fija en `v1.1C`, historial real en `v2.14G` (hallazgo A2). No es un error de los datos del pipeline, sino de la documentación de estado general.
- **Ubicación del dataset maestro "expanded_universe"**: cambia de `data/raw/expanded_universe/` a `outputs/full_universe_source_acquisition/` a partir de v2_11e, sin aviso explícito en ningún README (hallazgo A4).
- **Esquema con columnas duplicadas/dispersas** (`ticker`/`symbol`, `company_name`/`security_name`) pobladas solo para el proveedor más reciente (hallazgo M5).
- **Verificación independiente del cierre v2.14G** (no es una inconsistencia, se documenta para trazabilidad): se recalcularon de forma independiente, contando directamente sobre `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv` (38.287 filas) y `expanded_universe_v2_13e.csv` (36.863 filas):
  - Baseline antes de Xetra: 36.863 → coincide.
  - Expandido después de Xetra: 38.287 → coincide.
  - Claves duplicadas `exchange+ticker`: 0 → coincide (recalculado con Python/`csv`, no solo confiado en el informe).
  - Filas pendientes hacia 50k: 50.000 − 38.287 = 11.713 → coincide.
  - Suma de la tabla "Provider breakdown" del informe de cierre (21.154+3.705+3.244+2.804+2.404+2.359+1.424+1.193) = 38.287 → coincide.
  - **Conclusión: no hay evidencia que justifique reabrir el cierre v2.14G.**
- Mojibake recurrente en 3 documentos generados por script (hallazgo M4) — inconsistencia de forma, no de contenido.

## 6. Mejoras recomendadas

### Quick wins
- Fijar versiones en `requirements.txt` (M1).
- Eliminar duplicado de `check_phase7a5_2_institutional_dashboard.py` / `hotfix_phase7a5_2_dashboard.py` en la raíz (M2).
- Corregir los 3 documentos con mojibake y forzar `encoding='utf-8'` en generadores de reportes (M4).
- Añadir `.gitattributes` para fijar el criterio de fin de línea antes de que crezca más el volumen de archivos afectados (A1).

### Mejoras de robustez
- Test ligero de integridad post-cierre ejecutable con `pytest` sobre el dataset expandido vigente (A3).
- Normalizar esquema de `expanded_universe` (`ticker` vs `symbol`, `company_name` vs `security_name`) antes de integrarlo con el scoring de la app (M5).
- Documentar y fijar la ruta canónica del dataset "vigente" tras cada cierre (A4).

### Mejoras de escalabilidad
- Evaluar Git LFS o almacenamiento externo para los volcados crudos de proveedores (M6), especialmente de cara a los exchanges que faltan para llegar a 50k/full source.
- Archivar scripts de fases ya congeladas en `scripts/archive/` (B2).

### Mejoras de documentación
- Actualizar VERSION.md/README.md/CHANGELOG.md para reflejar el estado real del proyecto o separar explícitamente las dos líneas de trabajo (app MVP vs. pipeline de datos) (A2).
- Documento de arquitectura en `docs/technical/` (actualmente vacío) que explique el flujo extracción → normalización → validación → reporting del pipeline v2.x (B3).

## 7. Plan de acción recomendado

### Fase 1 — Correcciones seguras
- Confirmar que no hay procesos git activos y resolver el `index.lock` (C1) — requiere aprobación explícita antes de tocar `.git/`.
- Corregir mojibake en los 3 documentos identificados (M4).
- Eliminar el duplicado de scripts en la raíz (M2).
- Fijar versiones en `requirements.txt` (M1).

### Fase 2 — Refuerzo del pipeline
- Añadir `.gitattributes` y renormalizar fin de línea de forma controlada, en un commit dedicado y documentado, separado de cualquier cambio de datos (A1).
- Añadir test de integridad post-cierre reproducible (A3).
- Actualizar VERSION.md/README.md/CHANGELOG.md (A2).
- Documentar la ruta canónica del dataset vigente (A4).

### Fase 3 — Escalado
- Normalizar esquema del universo expandido antes de conectarlo al scoring de la app (M5).
- Evaluar Git LFS / almacenamiento externo para raw dumps (M6).
- Archivar scripts de fases congeladas (B2) y redactar documento de arquitectura (B3).
- Continuar la ruta hacia 50k/full source siguiendo el patrón conservador ya validado (v2.15A propuesto en el propio informe de cierre v2.14G).

## 8. Checklist final

- [ ] Confirmar ausencia de procesos git activos y eliminar `.git/index.lock` | Prioridad: crítica | Archivo: `.git/index.lock` | Validación: `git status -sb` sin warnings, `git add` funcional
- [ ] Añadir `.gitattributes` y renormalizar fin de línea | Prioridad: alta | Archivo: nuevo `.gitattributes` + repo completo | Validación: `git status --porcelain` sin los 952 falsos positivos tras un checkout limpio
- [ ] Actualizar VERSION.md / README.md / CHANGELOG.md al estado real | Prioridad: alta | Archivos: `VERSION.md`, `README.md`, `CHANGELOG.md` | Validación: revisión manual de coherencia con `git log`
- [ ] Añadir test de integridad post-cierre (filas, dup keys, columnas obligatorias) | Prioridad: alta | Archivo: nuevo en `tests/` | Validación: `pytest -q` en verde
- [ ] Documentar ruta canónica del dataset expandido vigente | Prioridad: alta | Archivo: README de `data/raw/expanded_universe/` u otro central | Validación: coincide con el path usado en el último script de cierre
- [ ] Fijar versiones en `requirements.txt` | Prioridad: media | Archivo: `requirements.txt` | Validación: `pip install -r requirements.txt` reproducible
- [ ] Eliminar duplicado de scripts en la raíz | Prioridad: media | Archivos: `check_phase7a5_2_institutional_dashboard.py`, `hotfix_phase7a5_2_dashboard.py` (raíz) | Validación: `grep` confirma que nada referencia la ruta de raíz
- [ ] Corregir mojibake en documentos generados | Prioridad: media | Archivos: `outputs/audit/legacy_helper_usage_v1_6d3.md`, `data/raw/expanded_universe/README_v2_3e.md`, `README.md` | Validación: apertura visual sin caracteres corruptos
- [ ] Normalizar esquema `ticker`/`symbol`, `company_name`/`security_name` | Prioridad: media (antes de integrar a scoring) | Archivo: `expanded_universe_v2_14e.csv` y script de rebuild correspondiente | Validación: script de test de esquema
- [ ] Evaluar Git LFS para raw dumps de proveedores | Prioridad: baja | Archivos: `outputs/full_universe_source_acquisition/raw/*` | Validación: tamaño de `.git` tras migración
- [ ] Archivar scripts de fases congeladas | Prioridad: baja | Directorio: `scripts/` | Validación: scripts activos siguen ejecutándose igual
- [ ] Documento de arquitectura del pipeline v2.x | Prioridad: baja | Directorio: `docs/technical/` | Validación: revisión manual

## Comandos de validación usados en esta auditoría (reproducibles)

```
git status -sb
git log --oneline -n 20
git rev-list --left-right --count origin/main...main
git diff --stat app.py
git fsck --full
git count-objects -v
wc -l outputs/full_universe_source_acquisition/expanded_universe_v2_1{1,2,3,4}e.csv
```
Más un script Python puntual (no persistido) para recontar filas y claves duplicadas `exchange+ticker` sobre `expanded_universe_v2_14e.csv`.

---

## Las 5 acciones que haría primero, y por qué

1. **Resolver el `index.lock` (C1)** — es lo único que bloquea físicamente poder trabajar con git ahora mismo; sin esto no se puede ni empezar el resto del plan.
2. **Añadir `.gitattributes` y renormalizar fin de línea (A1)** — mientras no se resuelva, cualquier commit futuro en Windows arrastra ruido en cientos de archivos, contaminando la trazabilidad que el proyecto exige explícitamente.
3. **Actualizar VERSION.md/README.md/CHANGELOG.md (A2)** — es el hallazgo con más riesgo de generar decisiones equivocadas por trabajar sobre una imagen desactualizada del proyecto (2 versiones mayores de diferencia).
4. **Documentar la ruta canónica del dataset expandido vigente (A4)** — barato de corregir y evita que alguien use por error `expanded_universe_v2_8e.csv` (9.200 filas) en vez de la versión real de 38.287 filas.
5. **Test de integridad post-cierre automatizado (A3)** — es la pieza que falta para que "critical/warning failed checks: 0" deje de depender solo de la disciplina manual y empiece a ser verificable de forma reproducible en cada fase futura (JPX→Xetra→v2.15A y sucesivas).
