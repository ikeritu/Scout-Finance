# Scout Finance — Fase 6A: fuente y formato del universo real inicial

## Objetivo

Preparar el paso de demo a universo real usando CSV.

Esta fase no llama APIs, no llama OpenAI y no modifica app.py.

## Archivos incluidos

```text
src/prepare_real_universe_csv.py
scripts/check_phase6a_real_universe.py
templates/universe_source_sample.csv
PHASE6A_REAL_UNIVERSE_SOURCE_FORMAT.md
PHASE6A_COLUMNS.md
README_PHASE6A_REAL_UNIVERSE.md
```

## Flujo recomendado

1. Descargar/exportar un CSV de acciones.
2. Guardarlo como:

```text
data/raw/universe_source.csv
```

3. Normalizarlo:

```powershell
.\.venv\Scripts\python.exe -m src.prepare_real_universe_csv --source nasdaq_csv
```

4. Validarlo:

```powershell
.\.venv\Scripts\python.exe scripts/check_phase6a_real_universe.py
```

5. Ejecutar el embudo:

```powershell
.\.venv\Scripts\python.exe -m src.load_global_universe
.\.venv\Scripts\python.exe -m src.run_stage1_filter
```

## Instalación

Desde la raíz del proyecto:

```powershell
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase6a_real_universe_source_format\src\prepare_real_universe_csv.py" ".\src\prepare_real_universe_csv.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase6a_real_universe_source_format\scripts\check_phase6a_real_universe.py" ".\scripts\check_phase6a_real_universe.py" -Force
New-Item -ItemType Directory -Force ".\data\raw"
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase6a_real_universe_source_format\templates\universe_source_sample.csv" ".\data\raw\universe_source.csv" -Force
```

## Probar con sample

```powershell
.\.venv\Scripts\python.exe -m src.prepare_real_universe_csv --source sample_csv
.\.venv\Scripts\python.exe scripts/check_phase6a_real_universe.py
.\.venv\Scripts\python.exe -m src.load_global_universe
.\.venv\Scripts\python.exe -m src.run_stage1_filter
```

## Siguiente fase

```text
Fase 6B — Enriquecimiento de datos fundamentales reales
```
