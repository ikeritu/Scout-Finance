# Scout Finance — Fase 4H: Documentación y versión estable + FAQ

## Objetivo

Cerrar una versión estable documentada de Scout Finance v0.4.

## Archivos incluidos

```text
app_phase4h_stable_docs_faq.py
README.md
CHANGELOG.md
VERSION.md
CHECKLIST_USO.md
FAQ_SCOUT_FINANCE.md
README_PHASE4H_DOCS_FAQ.md
```

## Cambios en la app

- FAQ de Streamlit actualizado a la versión v0.4.
- Se documentan Dashboard, Ranking, Análisis empresa, Fase 2, Comparar empresas, Histórico, Ajustes y checker.
- No se modifica la lógica de OpenAI, pipeline ni análisis.

## Instalación

```powershell
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\app_phase4h_stable_docs_faq.py" ".\app.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\README.md" ".\README.md" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\CHANGELOG.md" ".\CHANGELOG.md" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\VERSION.md" ".\VERSION.md" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\CHECKLIST_USO.md" ".\CHECKLIST_USO.md" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h_docs_faq\FAQ_SCOUT_FINANCE.md" ".\FAQ_SCOUT_FINANCE.md" -Force
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Validación

- Abrir FAQ desde la barra lateral.
- Confirmar que habla de v0.4.
- Confirmar que explica Fase 2, Comparar empresas, Histórico, Ajustes y checker.
- Ejecutar checker de estabilidad.
