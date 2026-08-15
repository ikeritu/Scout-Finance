param(
    [switch]$Launch,
    [switch]$SkipHash
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Scout Finance v2.29A - instalacion limpia de la UI local" -ForegroundColor Cyan

$PythonCommand = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -c "import sys; print(sys.version)" 2>$null
    if ($LASTEXITCODE -eq 0) { $PythonCommand = @("py", "-3.11") }
    else { $PythonCommand = @("py", "-3") }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = @("python")
} else {
    throw "Python no esta instalado o no esta disponible en PATH. Instala Python 3.11 y vuelve a ejecutar este script."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual .venv..." -ForegroundColor Yellow
    if ($PythonCommand.Count -eq 2) { & $PythonCommand[0] $PythonCommand[1] -m venv .venv }
    else { & $PythonCommand[0] -m venv .venv }
}

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { throw "No se pudo crear el entorno virtual." }

Write-Host "Actualizando pip e instalando dependencias minimas..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements-ui-v2_28.txt

$VerifyArgs = @("scripts\verify_local_ui_install_v2_29a.py", "--root", $ProjectRoot)
if ($SkipHash) { $VerifyArgs += "--skip-dataset-hash" }
Write-Host "Verificando instalacion y datos operativos..." -ForegroundColor Yellow
& $VenvPython @VerifyArgs
if ($LASTEXITCODE -ne 0) { throw "La verificacion no ha finalizado correctamente." }

Write-Host "Instalacion validada. La UI esta lista." -ForegroundColor Green
if ($Launch) {
    & $VenvPython -m streamlit run app_v2_28.py
} else {
    Write-Host "Para abrirla: .\run_local_ui_v2_28.bat" -ForegroundColor Cyan
}
