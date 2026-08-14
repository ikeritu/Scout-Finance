@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [Scout Finance] No se encontro .venv\Scripts\python.exe
  echo Crea el entorno e instala requirements.txt antes de continuar.
  pause
  exit /b 1
)
echo [Scout Finance] Iniciando UI local estable v2.28...
".venv\Scripts\python.exe" -m streamlit run app_v2_28.py
endlocal
