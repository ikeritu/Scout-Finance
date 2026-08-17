param(
    [switch]$Launch,
    [switch]$SkipHash
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Scout Finance v2.32E - preparacion segura de la UI local" -ForegroundColor Cyan

$PythonExe = $null
$PythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -c "import sys; print(sys.version)" 2>$null
    $PythonExe = "py"
    if ($LASTEXITCODE -eq 0) { $PythonArgs = @("-3.11") }
    else { $PythonArgs = @("-3") }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
} else {
    throw "Python no esta instalado o no esta disponible en PATH. Instala Python 3.11 y vuelve a ejecutar este script."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual .venv..." -ForegroundColor Yellow
    & $PythonExe @PythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Python no pudo crear el entorno virtual." }
}

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { throw "No se pudo crear el entorno virtual." }

Write-Host "Actualizando pip e instalando dependencias minimas..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "No se pudo actualizar pip. Comprueba la conexion a Internet y vuelve a intentarlo." }
& $VenvPython -m pip install -r requirements-ui-v2_28.txt
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias. Comprueba la conexion a Internet y vuelve a intentarlo." }

$VerifyArgs = @("scripts\verify_local_ui_install_v2_29a.py", "--root", $ProjectRoot)
if ($SkipHash) { $VerifyArgs += "--skip-dataset-hash" }
Write-Host "Verificando instalacion y datos operativos..." -ForegroundColor Yellow
& $VenvPython @VerifyArgs
if ($LASTEXITCODE -ne 0) { throw "La verificacion no ha finalizado correctamente." }

Write-Host "Instalacion validada. La UI esta lista." -ForegroundColor Green
if ($Launch) {
    Write-Host "Abriendo Scout Finance. Para cerrar, vuelve a esta ventana y pulsa Ctrl+C." -ForegroundColor Cyan
    & $VenvPython -m streamlit run app_v2_28.py --browser.gatherUsageStats=false
} else {
    Write-Host "Para abrirla, haz doble clic en INICIAR_SCOUT_FINANCE.bat" -ForegroundColor Cyan
}
