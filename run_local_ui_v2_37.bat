@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "SF_PYTHON=.venv\Scripts\python.exe"
) else (
  where python >nul 2>nul || (
    echo ERROR: Python no esta instalado o no esta en PATH.
    pause
    exit /b 1
  )
  set "SF_PYTHON=python"
)
%SF_PYTHON% -c "import streamlit, pandas" >nul 2>nul || (
  echo ERROR: faltan dependencias. Ejecuta: %SF_PYTHON% -m pip install -r requirements-ui-v2_28.txt
  pause
  exit /b 1
)
echo Abriendo Scout Finance en http://localhost:8501
%SF_PYTHON% -m streamlit run app_v2_37.py --server.address localhost --server.port 8501
endlocal
