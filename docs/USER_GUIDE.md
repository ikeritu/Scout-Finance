# Scout Finance — User Guide

## 1. Finalidad

Scout Finance es una herramienta local de scouting financiero para filtrar empresas, generar candidatos, revisar memos, detectar red flags y guardar una decisión humana documentada.

No es un asesor financiero, no es un bot de trading y no debe usarse para comprar o vender acciones de forma automática.

## 2. Flujo completo

```text
universo de empresas
→ filtros cuantitativos
→ ranking
→ research memo
→ red flags
→ revisión humana
→ watchlist / reject / needs_more_data
→ final review pack
```

## 3. Versiones relevantes

```text
v0.9.0-experimental-ai
→ capa experimental segura
→ memos v2
→ red flags
→ perfiles IA dry-run
→ sin llamadas reales

v1.0.0-candidate
→ revisión humana
→ export pack final
→ freeze candidate
```

## 4. Ejecutar revisión manual

Listar candidatos:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --list
```

Marcar watchlist:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker ADBE --status reviewed_watchlist --note "Empresa sólida. Revisar valoración antes de entrada."
```

Marcar rechazo:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker BZ --status reviewed_reject --note "Riesgo demasiado alto para seguimiento actual."
```

Marcar necesita más datos:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker AUPH --status needs_more_data --note "Revisar caja, deuda, pipeline y próximos catalysts."
```

Exportar buckets:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --export
```

## 5. Generar pack final

```powershell
.\.venv\Scripts\python.exe -m src.v1_0c_review_export_pack
```

Abrir informe:

```powershell
notepad ".\outputs\scouting\manual_review\final_review_pack.md"
```

## 6. Verificar freeze v1.0.0-candidate

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_0d_freeze_candidate.py
```

## 7. Archivos importantes

```text
outputs/scouting/manual_review/manual_review_state.json
outputs/scouting/manual_review/manual_review_summary.md
outputs/scouting/manual_review/final_review_pack.md
outputs/scouting/manual_review/final_review_pack.json
outputs/scouting/manual_review/final_review_pack.csv
releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip
```

## 8. Restaurar desde freeze

El ZIP congelado está en:

```text
releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip
```

Para restaurar, copia el ZIP a una carpeta limpia y descomprímelo. No sobrescribas la carpeta activa sin copia previa.

## 9. Interpretación de estados manuales

```text
pending_review
→ pendiente de revisar

reviewed_watchlist
→ candidato aceptado para seguimiento, no para compra automática

reviewed_reject
→ descartado manualmente

needs_more_data
→ requiere más datos antes de decidir
```

## 10. Regla de oro

Scout Finance prepara material de análisis. La decisión final siempre es humana.
