# Scout Finance — Phase 8B AI Equity Research Memo Blueprint

## Instalar

```powershell
cd "C:\Users\ikeri\proyectos\Scout Finance"

Expand-Archive "$env:USERPROFILE\Downloads\scout_finance_phase8b_ai_equity_research_memo_blueprint.zip" "$env:USERPROFILE\Downloads\scout_finance_phase8b_ai_equity_research_memo_blueprint" -Force

Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase8b_ai_equity_research_memo_blueprint\src\phase8b_ai_equity_research_memo_blueprint.py" ".\src\phase8b_ai_equity_research_memo_blueprint.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase8b_ai_equity_research_memo_blueprint\scripts\check_phase8b_ai_equity_research_memo_blueprint.py" ".\scripts\check_phase8b_ai_equity_research_memo_blueprint.py" -Force
New-Item -ItemType Directory -Force ".\docs\phase8"
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase8b_ai_equity_research_memo_blueprint\docs\phase8\PHASE8B_AI_EQUITY_RESEARCH_MEMO_BLUEPRINT.md" ".\docs\phase8\PHASE8B_AI_EQUITY_RESEARCH_MEMO_BLUEPRINT.md" -Force
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.phase8b_ai_equity_research_memo_blueprint
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase8b_ai_equity_research_memo_blueprint.py
```
