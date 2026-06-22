# Scout Finance — Fase 5B: Cargar universo global mínimo desde CSV

## Objetivo

Implementar la primera pieza técnica del embudo global:

```text
Stage 0 — Universo global
```

Esta fase:

- crea estructura de carpetas;
- lee `data/universe/global_universe.csv`;
- valida columnas mínimas;
- normaliza campos básicos;
- detecta duplicados;
- calcula `dollar_volume_90d`;
- genera `data/universe/global_universe_validated.csv`;
- genera `outputs/scouting/universe_validation_summary.json`.

No filtra empresas todavía.

## Qué NO toca

No toca:

```text
app.py
OpenAI
pipeline actual
Fase 2
Dashboard
Ranking
Comparativa
Histórico
Ajustes
outputs existentes
```

No llama a OpenAI.

## Archivos incluidos

```text
src/funnel_paths.py
src/global_universe.py
src/create_global_universe_template.py
src/load_global_universe.py
scripts/check_phase5b_global_universe.py
templates/global_universe_sample.csv
README_PHASE5B_GLOBAL_UNIVERSE_LOADER.md
```

## Instalación

Copia los archivos en la raíz de Scout Finance respetando carpetas:

```powershell
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\src\funnel_paths.py" ".\src\funnel_paths.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\src\global_universe.py" ".\src\global_universe.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\src\create_global_universe_template.py" ".\src\create_global_universe_template.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\src\load_global_universe.py" ".\src\load_global_universe.py" -Force
New-Item -ItemType Directory -Force ".\scripts"
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\scripts\check_phase5b_global_universe.py" ".\scripts\check_phase5b_global_universe.py" -Force
```

## Crear plantilla del universo

```powershell
.\.venv\Scripts\python.exe -m src.create_global_universe_template
```

Esto crea:

```text
data/universe/global_universe.csv
```

## Probar con CSV demo

Si quieres probar rápido:

```powershell
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase5b_global_universe_loader\templates\global_universe_sample.csv" ".\data\universe\global_universe.csv" -Force
```

## Ejecutar validación

```powershell
.\.venv\Scripts\python.exe -m src.load_global_universe
```

## Ejecutar checker

```powershell
.\.venv\Scripts\python.exe scripts/check_phase5b_global_universe.py
```

## Resultado esperado

```text
Scout Finance — Phase 5B global universe loader
Status: OK
Input companies: 3
Has required columns: True
Duplicated ticker rows: 0
```

Y deben crearse:

```text
data/universe/global_universe_validated.csv
outputs/scouting/universe_validation_summary.json
```

## Siguiente fase

```text
Fase 5C — Stage 1: Investable universe filter
```

Ahí sí empezaremos a clasificar empresas como:

```text
PASSED
WATCHLIST
REJECTED
```
