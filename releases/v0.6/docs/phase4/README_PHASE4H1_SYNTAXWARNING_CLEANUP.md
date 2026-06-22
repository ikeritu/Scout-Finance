# Scout Finance — Fase 4H.1: limpieza de SyntaxWarning

## Objetivo

Eliminar avisos no críticos de Python por rutas Windows escritas dentro de docstrings o textos embebidos.

Ejemplo del warning eliminado:

```text
SyntaxWarning: "\." is an invalid escape sequence
```

## Qué se corrige

1. `app_phase4h1_stable_no_syntaxwarning.py`
   - Misma app estable v0.4.
   - Textos internos con rutas en formato `./` para evitar escapes inválidos.
   - Sin cambios funcionales.

2. `check_phase4h1_stability.py`
   - Checker limpio.
   - Docstring convertido a raw string.
   - Sin warning por rutas tipo `.\.venv\Scripts`.

## Qué NO toca

```text
OpenAI
Pipeline
Scoring
Fase 2
Dashboard
Ranking
Comparativa visual
Histórico
Ajustes
Outputs
Base de datos
Prompts
Feedback
JSON
```

No llama a OpenAI.  
No modifica outputs.  
No cambia lógica de análisis.

## Instalación

Desde la raíz del proyecto:

```powershell
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h1_syntaxwarning_cleanup_v2\app_phase4h1_stable_no_syntaxwarning.py" ".\app.py" -Force
Copy-Item "$env:USERPROFILE\Downloads\scout_finance_phase4h1_syntaxwarning_cleanup_v2\check_phase4h1_stability.py" ".\check_phase4g_stability.py" -Force
```

## Ejecutar checker

```powershell
.\.venv\Scripts\python.exe check_phase4g_stability.py
```

## Resultado esperado

```text
Scout Finance — Phase 4H.1 stability checker
OK   app.py encontrado
OK   app.py compila correctamente
OK   AST de app.py leído correctamente
OK   Funciones principales presentes
OK   Markers principales de UI presentes
OK   outputs/analyses existe
OK   Hay JSON Fase 2 para comparativa/histórico
OK   Revisión de estabilidad completada
```

Y sin `SyntaxWarning`.

## Después de validar

Actualizar release local:

```powershell
Copy-Item ".\app.py" ".\app_v0_4_stable.py" -Force
Copy-Item ".\app.py" ".\releases\v0.4\app.py" -Force
Copy-Item ".\check_phase4g_stability.py" ".\releases\v0.4\check_phase4g_stability.py" -Force
```
