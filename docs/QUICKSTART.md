# Scout Finance — Quickstart

## Arranque rápido

Ruta local:

```powershell
cd "D:\Proyectos\💰 Scout Finance"
```

## 1. Ver candidatos revisables

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --list
```

## 2. Marcar decisiones

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker ADBE --status reviewed_watchlist --note "Empresa sólida. Revisar valoración antes de entrada."

.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker BZ --status reviewed_reject --note "Riesgo demasiado alto para seguimiento actual."

.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker AUPH --status needs_more_data --note "Revisar caja, deuda, pipeline y próximos catalysts."
```

## 3. Exportar revisión

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --export
```

## 4. Generar pack final

```powershell
.\.venv\Scripts\python.exe -m src.v1_0c_review_export_pack
```

## 5. Abrir informe final

```powershell
notepad ".\outputs\scouting\manual_review\final_review_pack.md"
```

## 6. Validar candidate freeze

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_0d_freeze_candidate.py
```

## Resultado esperado

```text
OK   v1.0D Freeze Candidate is valid
```
