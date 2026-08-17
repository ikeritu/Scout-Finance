@echo off
setlocal
chcp 65001 >nul
title Scout Finance
cd /d "%~dp0"

echo.
echo ============================================================
echo   SCOUT FINANCE - INICIO SEGURO
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Primera ejecucion: se preparara la aplicacion automaticamente.
  echo Este proceso puede tardar unos minutos y necesita Internet.
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -File ".\setup_local_ui_v2_29a.ps1" -Launch
  if errorlevel 1 goto :error
  goto :end
)

echo Comprobando archivos y datos operativos...
".venv\Scripts\python.exe" "scripts\verify_local_ui_install_v2_29a.py" --root "%CD%"
if errorlevel 1 goto :error

echo.
echo Todo correcto. Abriendo Scout Finance...
echo Para cerrar la aplicacion, vuelve a esta ventana y pulsa Ctrl+C.
echo.
".venv\Scripts\python.exe" -m streamlit run "app_v2_28.py" --browser.gatherUsageStats=false
if errorlevel 1 goto :error
goto :end

:error
echo.
echo [ERROR] Scout Finance no ha podido iniciarse de forma segura.
echo Consulta la seccion "Solucion de problemas" de GUIA_SCOUT_FINANCE.md.
echo No se ha modificado el universo operativo.
pause
exit /b 1

:end
endlocal
