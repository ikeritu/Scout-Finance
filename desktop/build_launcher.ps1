<#
  Compiles "Scout Finance.exe" with the C# compiler that ships with Windows (.NET Framework 4): nothing to install.
  Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File desktop\build_launcher.ps1
  Output: desktop\Scout Finance.exe (ignored by git: it is rebuilt from ScoutFinanceLauncher.cs).
#>
param([string]$Output = "")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Output) { $Output = Join-Path $here "Scout Finance.exe" }
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { throw "No se encuentra el compilador de .NET Framework: $csc" }

$icon = Join-Path $here "scout_finance.ico"
$source = Join-Path $here "ScoutFinanceLauncher.cs"
$arguments = @("/nologo", "/codepage:65001", "/target:winexe", "/optimize+", "/out:$Output", "/win32icon:$icon",
               "/reference:System.dll", "/reference:System.Drawing.dll", "/reference:System.Windows.Forms.dll", "/reference:System.Management.dll", $source)
& $csc @arguments
if ($LASTEXITCODE -ne 0) { throw "La compilación falló (código $LASTEXITCODE)." }
Write-Host "Creado: $Output ($([math]::Round((Get-Item $Output).Length / 1KB)) KB)"
