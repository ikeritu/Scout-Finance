<#
  Builds the launcher (if needed) and puts a "Scout Finance" shortcut with its icon on the Windows desktop.
  Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File desktop\install_shortcut.ps1
  Add -Rebuild to compile again, and -Remove to delete the shortcut. It never touches the app, its data or any key.
#>
param([switch]$Rebuild, [switch]$Remove)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$exe = Join-Path $here "Scout Finance.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$link = Join-Path $desktop "Scout Finance.lnk"

if ($Remove) {
    if (Test-Path $link) { Remove-Item $link; Write-Host "Acceso directo eliminado: $link" } else { Write-Host "No había acceso directo." }
    return
}

if ($Rebuild -or -not (Test-Path $exe)) { & (Join-Path $here "build_launcher.ps1") }

# the launcher normally finds the project next to itself; this is the fallback if the .exe is ever moved
$data = Join-Path $env:LOCALAPPDATA "ScoutFinance"
New-Item -ItemType Directory -Force $data | Out-Null
[IO.File]::WriteAllText((Join-Path $data "root.txt"), $root, (New-Object Text.UTF8Encoding($false)))

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = (Join-Path $here "scout_finance.ico")
$shortcut.Description = "Scout Finance: investigación local de mercados"
$shortcut.Save()
Write-Host "Acceso directo creado: $link"
