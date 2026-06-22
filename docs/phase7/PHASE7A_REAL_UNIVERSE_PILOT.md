# Scout Finance — Fase 7A: primer CSV real amplio

## Objetivo

Probar el sistema con un CSV real más amplio, pero sin saltar directamente a 59.000 empresas.

Rango recomendado:

```text
100-500 empresas
```

## Flujo

```text
CSV real
↓
piloto limitado a N filas
↓
normalización Fase 6A
↓
Stage 0 validación
↓
Stage 1 filtro de invertibilidad
↓
Fase 6B cobertura fundamental
```

## Qué NO hace

```text
No llama APIs
No llama OpenAI
No toca app.py
No modifica releases/v0.6
No ejecuta Stage 2
No ejecuta Stage 3
```

## Archivo de entrada recomendado

```text
data/raw/universe_source_real.csv
```

## Comando recomendado

```powershell
.\.venv\Scripts\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real.csv --limit 500 --source real_csv_pilot
```

Para empezar más prudente:

```powershell
.\.venv\Scripts\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real.csv --limit 100 --source real_csv_pilot
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7a_real_universe_pilot.py
```

## Mirar motivos de rechazo

```powershell
Import-Csv ".\data\stages\stage1_rejection_log.csv" | Group-Object reason_code | Sort-Object Count -Descending
```

## Siguiente fase

```text
Fase 7B — Ajuste de Stage 1 con datos reales
```
