# Scout Finance — Quickstart

## Arranque rápido

Ruta local del proyecto:

```powershell
cd "D:\Proyectos\💰 Scout Finance"
```

## 1. Validar que la versión congelada sigue correcta

Antes de usar el programa, comprueba que la versión candidate sigue válida:

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_0d_freeze_candidate.py
```

Resultado esperado:

```text
OK   v1.0D Freeze Candidate is valid
```

## 2. Ver candidatos revisables

Lista los candidatos disponibles y su estado manual actual:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --list
```

Verás una tabla con:

```text
ticker
verdict automático
red flags
severidad máxima
estado manual
notas
```

## 3. Marcar decisiones manuales

Formato general:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker TICKER --status ESTADO --note "Tu nota manual"
```

Estados permitidos:

```text
pending_review
reviewed_watchlist
reviewed_reject
needs_more_data
```

Ejemplo para añadir a watchlist:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker ADBE --status reviewed_watchlist --note "Empresa sólida. Revisar valoración antes de entrada."
```

Ejemplo para rechazar:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker BZ --status reviewed_reject --note "Riesgo demasiado alto para seguimiento actual."
```

Ejemplo para pedir más datos:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker AUPH --status needs_more_data --note "Revisar caja, deuda, pipeline y próximos catalysts."
```

## 4. Exportar revisión manual

Cuando termines de marcar decisiones:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --export
```

Esto genera o actualiza:

```text
outputs/scouting/manual_review/reviewed_watchlist.csv
outputs/scouting/manual_review/reviewed_reject.csv
outputs/scouting/manual_review/needs_more_data.csv
outputs/scouting/manual_review/manual_review_summary.md
```

## 5. Generar pack final

```powershell
.\.venv\Scripts\python.exe -m src.v1_0c_review_export_pack
```

Esto genera:

```text
outputs/scouting/manual_review/final_review_pack.md
outputs/scouting/manual_review/final_review_pack.json
outputs/scouting/manual_review/final_review_pack.csv
```

## 6. Abrir informes

Abrir resumen de revisión manual:

```powershell
notepad ".\outputs\scouting\manual_review\manual_review_summary.md"
```

Abrir pack final:

```powershell
notepad ".\outputs\scouting\manual_review\final_review_pack.md"
```

## 7. Validar documentación

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_0e_user_manual.py
```

Resultado esperado:

```text
OK   v1.0E User Manual is valid
```

## 8. Validar freeze documental

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_0f_final_documentation_freeze.py
```

Resultado esperado:

```text
OK   v1.0F Final Documentation Freeze is valid
```

## Archivos importantes

```text
docs/USER_GUIDE.md
docs/SAFETY_LIMITS.md
outputs/scouting/manual_review/manual_review_state.json
outputs/scouting/manual_review/manual_review_summary.md
outputs/scouting/manual_review/final_review_pack.md
releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip
releases/Scout_Finance_v1.0.0_candidate_DOCUMENTATION_FREEZE.zip
```

## Recordatorio importante

Scout Finance no es un asesor financiero ni un bot de trading.

El programa ordena información, genera candidatos, muestra riesgos y permite guardar una decisión humana documentada. La decisión final siempre es manual.
